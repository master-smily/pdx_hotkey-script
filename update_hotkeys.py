import json
import re
from pathlib import Path

def load_config(path="hotkeys_config.json"):
    """Loads the replacement rules and target directory."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def apply_hotkey_replacements(content, config):
    """
    Applies replacements directly to the file content using Regex.
    This preserves the original file formatting perfectly.
    """
    # 1. Global Replacements (Search-All)
    global_rules = config.get("global", {})
    for old_key, new_key in global_rules.items():
        # Matches: shortcut = "OLD_KEY"
        # Replaces with: shortcut = "NEW_KEY"
        # This handles varying whitespace around the '=' sign.
        pattern = rf'shortcut\s*=\s*"{old_key}"'
        content = re.sub(pattern, f'shortcut = "{new_key}"', content)

    # 2. Specific Replacements (Targeted by 'name')
    specific_rules = config.get("specific", [])
    for rule in specific_rules:
        target_name = rule["name"]
        new_shortcut = rule["new_shortcut"]
        
        # This regex looks for a buttonType block that contains the specific name.
        # It captures the entire block from 'buttonType {' to '}'.
        # [^}]* ensures we stay within the current block (non-greedy for the block).
        # We use re.DOTALL so that '.' matches newlines.
        block_pattern = (
            rf'(buttonType\s*\{{[^}}]*name\s*=\s*["\']{re.escape(target_name)}["'][^}]*'
            rf'shortcut\s*=\s*["\'][^"]+["'][^}]*\})'
        )
        
        def replace_shortcut_in_block(match):
            block = match.group(1)
            # Within the matched block, replace the shortcut value.
            # This ensures we only change the shortcut inside THIS specific buttonType.
            return re.sub(r'(shortcut\s*=\s*")[^"]+(")', rf'\1{new_shortcut}"\2', block)

        content = re.sub(block_pattern, replace_shortcut_in_block, content, flags=re.DOTALL)

    return content

def main():
    config = load_config()
    target_dir = config.get("target_directory", "./interface")
    
    # Grab all .gui files in the target directory and its subdirectories
    gui_files = Path(target_dir).rglob("*.gui")
    
    for file_path in gui_files:
        print(f"Inspecting: {file_path}")
        try:
            # Read the raw text content
            content = file_path.read_text(encoding="utf-8")
            
            # Apply the modifications
            new_content = apply_hotkey_replacements(content, config)
            
            # If the content changed, write it back
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  -> [SUCCESS] Updated hotkeys in {file_path.name}")
            else:
                print(f"  -> [SKIPPED] No matching hotkeys found in {file_path.name}")
        
        except Exception as e:
            print(f"  -> [ERROR] Could not process {file_path.name}: {e}")

if __name__ == "__main__":
    main()