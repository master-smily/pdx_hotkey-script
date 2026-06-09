⚠️ This completly breaks the UI for now, it's probably ckparser.revert being experimental, so I don't think I'll be getting this to work.








# Paradox hotkey script
An automated utility script for paradox games modders to update, remap, and maintain user interface hotkeys across game updates.

Manually editing `.gui` files after every major patch is tedious and prone to breaking layouts. This tool uses `ckparser` to parse Paradox Jomini/Clausewitz GUI files into Python structures, applies your custom hotkey configuration, and safely exports them back into a mod-ready format.

It was built for HOI4 so I don't know what games this works for, but as long as the hotkeys are stored in the `.gui` interface files it should work.

## Features

- **Mass Search-and-Replace:** Globally swap out specific keys across all GUI files (e.g., remapping *RETURN* to *c*).
- **Targeted Replacements:** Update shortcuts for specific UI elements by targeting their unique container `name` properties (e.g., modifying only the `diplomacy_button`).
- **Mod Isolation:** Designed to run safely against copied interface files inside your custom mod directory, leaving base game files untouched.

---

## Installation & Setup

This project requires **Python 3.8+**. Follow these steps to set up a clean, isolated virtual environment.

### 1. Clone or download the Repository
```bash
git clone https://github.com/master-smily/pdx-hotkey-script.git
cd pdx-hotkey-script
```

### 2. Create a Virtual Environment (venv)
Isolate your project dependencies by creating a local virtual environment:

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
### 3. Install Dependencies
Install the required packages using pip and the provided requirements.txt:

```bash
pip install -r requirements.txt
```

## Configuration (*hotkeys_config.json*)
The script is driven entirely by a JSON configuration file. Create a file named hotkeys_config.json in the root directory of the script.

### Configuration Example
```JSON
{
    "target_directory": "./my_mod/interface",
    "global": {
        "RETURN": "c",
        "ESCAPE": "x"
    },
    "specific": [
        {
            "name": "diplomacy_button",
            "new_shortcut": "e"
        },
        {
            "name": "production_nav_button",
            "new_shortcut": "p"
        }
    ]
}
```

You can search for `shortcut = "e"` in all files if you open the interface folder using VS Code, that way you can find the name if you don't know it, in this case name is `diplomacy_button`

```
buttonType = {
    name = "diplomacy_button"
    quadTextureSprite ="GFX_topbar_diplomacy"
    position = { x= 6 y = 0 }
    Orientation = "UPPER_LEFT"
    shortcut = "e"
    clicksound = click_close
    oversound = ui_menu_over
}
```

### Options Breakdown
`target_directory`: The relative or absolute path to your mod's interface folder containing the .gui files you wish to modify.

`global`: A map of **Search-All and Replace** rules. Any shortcut matching the key will be replaced by the value.

`specific`: A list of targets for **Specific Replacements**. The script looks for a buttonType or container matching the exact name, then updates its shortcut fields to the new_shortcut value.

## Usage
Once your configuration file is populated and your virtual environment is active, run the script:

```Bash
python update_hotkeys.py
```
The script will scan the target directory recursively, parse the .gui layout files, apply your changes, and overwrite the files in your mod directory with the updated hotkeys.

## ⚠️ Important Modding Note
This tool relies on ckparser's reverse-conversion heuristics to rebuild Jomini text from Python data structures. Because Paradox UI scripting contains various structural anomalies and loose syntax edge cases:

- **Never run this tool directly on original base game files**. Always run it on a copy inside a dedicated mod directory.
- **Verify changes**. If the game throws UI validation errors or layouts appear broken after running the script, use a diff tool (like VS Code Diff, Git diff, or WinMerge) to compare the modified file against the backup. This will help identify if the parser shifted any non-shortcut layout formatting.
- The script doesn't check for hotkey conflicts, remember to check if anything else uses that button and replace that too
