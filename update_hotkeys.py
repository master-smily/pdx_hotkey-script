import json
import re
from pathlib import Path

def load_config(path="hotkeys_config.json"):
    """Loads the replacement rules and target directory."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_matching_brace(content, open_brace_index):
    """Returns the matching closing brace index, ignoring braces in strings/comments."""
    depth = 0
    quote = None
    in_comment = False

    for index in range(open_brace_index, len(content)):
        char = content[index]

        if in_comment:
            if char == "\n":
                in_comment = False
            continue

        if quote:
            if char == quote:
                quote = None
            continue

        if char == "#":
            in_comment = True
        elif char in ('"', "'"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index

    return None


def iter_button_type_blocks(content):
    """Yields balanced Paradox `buttonType = { ... }` block spans."""
    pattern = re.compile(r"\bbuttonType\s*=\s*\{", flags=re.IGNORECASE)

    for match in pattern.finditer(content):
        open_brace_index = content.find("{", match.start(), match.end())
        close_brace_index = find_matching_brace(content, open_brace_index)
        if close_brace_index is not None:
            yield match.start(), close_brace_index + 1


def has_named_button(block, target_name):
    name_pattern = re.compile(
        rf'\bname\s*=\s*(["\']){re.escape(target_name)}\1'
    )
    return bool(name_pattern.search(block))


def replace_shortcuts_in_block(block, new_shortcut):
    shortcut_pattern = re.compile(r'(\bshortcut\s*=\s*)(["\'])(.*?)\2')
    return shortcut_pattern.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{new_shortcut}{match.group(2)}",
        block,
    )


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
        pattern = rf'\bshortcut\s*=\s*"{re.escape(old_key)}"'
        content = re.sub(pattern, f'shortcut = "{new_key}"', content)

    # 2. Specific Replacements (Targeted by 'name')
    specific_rules = config.get("specific", [])
    for rule in specific_rules:
        target_name = rule["name"]
        new_shortcut = rule["new_shortcut"]

        updated_parts = []
        last_index = 0
        for start, end in iter_button_type_blocks(content):
            block = content[start:end]
            if has_named_button(block, target_name):
                updated_parts.append(content[last_index:start])
                updated_parts.append(replace_shortcuts_in_block(block, new_shortcut))
                last_index = end

        if updated_parts:
            updated_parts.append(content[last_index:])
            content = "".join(updated_parts)

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
