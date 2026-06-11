# Paradox hotkey script
An automated utility script for paradox games modders to update, remap, and maintain user interface hotkeys across game updates.

Manually editing `.gui` files after every major patch is tedious and prone to breaking layouts. This tool edits shortcut assignments in-place in the original text, applies your custom hotkey configuration, and exports changed files into a mod-ready output folder.

It was built for HOI4 so I don't know what games this works for, but as long as the hotkeys are stored in the `.gui` interface files it should work.

## Features

- **Mass Search-and-Replace:** Globally swap out specific keys across all GUI files (e.g., remapping *RETURN* to *c*).
- **Targeted Replacements:** Update shortcuts for specific UI elements by targeting their unique container `name` properties (e.g., modifying only the `diplomacy_button`).
- **Mod Isolation:** Reads source interface files and writes modified files to an output directory, leaving the input files untouched.

---


This project requires **Python 3.8+**.

### Clone or download the Repository
```bash
git clone https://github.com/master-smily/pdx-hotkey-script.git
cd pdx-hotkey-script
```

## Configuration (*hotkeys_config.json*)
The script is driven entirely by a JSON configuration file. Create a file named hotkeys_config.json in the root directory of the script.

### Configuration Example
```JSON
{
    "target_directory": "./my_mod/interface",
    "output_directory": "./output",
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
`target_directory`: The relative or absolute path to the interface folder containing the .gui files you want to read.

`output_directory`: The relative or absolute path where changed .gui files will be written. Defaults to `./output`.

`global`: A map of **Search-All and Replace** rules. Any shortcut matching the key will be replaced by the value.

`specific`: A list of targets for **Specific Replacements**. The script looks for a buttonType or container matching the exact name, then updates its shortcut fields to the new_shortcut value.

## Usage
Once your configuration file is populated and your virtual environment is active, run the script:

```Bash
python update_hotkeys.py
```
The script will scan the target directory recursively, apply your changes, and write changed files under the output directory while preserving the interface folder structure. With the example above, output files are written under `output/interface`.

## ⚠️ Important Modding Note
This tool avoids rebuilding Paradox GUI files from parsed data and instead preserves the original text around changed shortcut assignments. Because Paradox UI scripting contains various structural anomalies and loose syntax edge cases:

- **Never set `output_directory` to your source interface folder**. The script refuses to write into the source tree, but keeping input and output separate makes review simpler.
- **Verify changes**. If the game throws UI validation errors or layouts appear broken after running the script, use a diff tool (like VS Code Diff, Git diff, or WinMerge) to compare the output file against the source file.
- The script doesn't check for hotkey conflicts, remember to check if anything else uses that button and replace that too
