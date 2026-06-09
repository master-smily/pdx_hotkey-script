import json
import ckparser
from pathlib import Path

# Restricting the search space to relevant GUI nodes based on your parameters
VALID_CONTAINERS = {"guitypes", "containerwindowType", "buttontype", "windowtype"}

def load_config(path="hotkeys_config.json"):
    """Loads the replacement rules and target directory."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def modify_shortcuts(data, config):
    """
    Recursively searches for 'shortcut' fields and modifies them based on the config.
    Returns True if any modification was made.
    """
    modified = False
    
    # ckparser converts duplicate Jomini keys into Python lists. We must traverse them.
    if isinstance(data, list):
        for item in data:
            if modify_shortcuts(item, config):
                modified = True
                
    elif isinstance(data, dict):
        # Duck-typing: If we hit a dictionary with a 'shortcut', evaluate it
        if "shortcut" in data:
            # Strip quotes for clean comparison
            current_shortcut = str(data["shortcut"]).strip('"')
            name = str(data.get("name", "")).strip('"')
            
            # 1. Specific Replace (Targeted by 'name' field)
            specific_match = next((item for item in config.get("specific", []) if item["name"] == name), None)
            
            if specific_match:
                # Add quotes around the new string so Jomini parses it correctly as a string
                new_val = f'"{specific_match["new_shortcut"]}"'
                if data["shortcut"] != new_val:
                    data["shortcut"] = new_val
                    modified = True
            
            # 2. Search-All Replace (Fallback if no specific name match)
            elif current_shortcut in config.get("global", {}):
                new_val = f'"{config["global"][current_shortcut]}"'
                if data["shortcut"] != new_val:
                    data["shortcut"] = new_val
                    modified = True

        # Traverse further into the hierarchy
        for key, value in data.items():
            # Optimize performance by only checking known containers or lists 
            # (since nested duplicate containers become lists)
            if key.lower() in VALID_CONTAINERS or isinstance(value, list):
                # Ensure we only recurse into iterables
                if isinstance(value, (dict, list)):
                    if modify_shortcuts(value, config):
                        modified = True
                        
    return modified

def main():
    config = load_config()
    target_dir = config.get("target_directory", "./interface")
    
    # Grab all .gui files in the target directory and its subdirectories
    gui_files = Path(target_dir).rglob("*.gui")
    
    for file_path in gui_files:
        print(f"Inspecting: {file_path}")
        try:
            # 1. Safely read file with ckparser's built-in encoding detection
            raw_text = ckparser.read_file(str(file_path))
            
            # 2. Parse raw Jomini text into a Python structure
            parsed_data = ckparser.parse_text(raw_text)
            
            # 3. Apply shortcut modifications
            if modify_shortcuts(parsed_data, config):
                
                # 4. Revert Python structure back to Jomini text
                new_text = ckparser.revert(parsed_data)
                
                # Write the changes back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_text)
                print(f"  -> [SUCCESS] Updated hotkeys in {file_path.name}")
                
        except Exception as e:
            print(f"  -> [ERROR] Could not process {file_path.name}: {e}")

if __name__ == "__main__":
    main()