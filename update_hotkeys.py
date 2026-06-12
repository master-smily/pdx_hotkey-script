import argparse
from collections import deque
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Optional
import json
import re
import shutil


def build_arg_parser() -> argparse.ArgumentParser:
    """Builds the command line parser for config overrides."""
    parser = argparse.ArgumentParser(
        description=(
            "Update Paradox .gui hotkeys using a JSON config file. "
            "Any config option passed on the command line is also written "
            "back to the config file before processing."
        )
    )
    parser.add_argument(
        "--config",
        default="hotkeys_config.json",
        help="Path to the JSON config file. Defaults to hotkeys_config.json.",
    )

    parser.add_argument(
        "--source",
        help="Interface directory containing .gui files to read.",
    )
    parser.add_argument(
        "--output",
        help="Directory where changed .gui files will be written.",
    )

    parser.add_argument(
        "--global",
        dest="global_rules",
        action="append",
        nargs=2,
        metavar=("OLD_KEY", "NEW_KEY"),
        help=(
            "Add or update a global shortcut replacement. "
            "Can be passed multiple times."
        ),
    )
    parser.add_argument(
        "--specific",
        dest="specific_rules",
        action="append",
        nargs=2,
        metavar=("NAME", "NEW_SHORTCUT"),
        help=(
            "Add or update a named button shortcut replacement. "
            "Can be passed multiple times."
        ),
    )
    return parser


def load_config(path: str) -> dict[str, Any]:
    """Loads the replacement rules and target directory."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_config_overrides(
        config: dict[str, Any],
        args: argparse.Namespace,
) -> dict[str, Any]:
    """Merges command line config parameters into the loaded config."""
    if args.source is not None:
        config["target_directory"] = args.source

    if args.output is not None:
        config["output_directory"] = args.output

    if args.global_rules is not None:
        global_rules = config.get("global", {})
        for old_key, new_key in args.global_rules:
            global_rules[old_key] = new_key
        config["global"] = global_rules

    if args.specific_rules is not None:
        existing_rules = config.get("specific", {})
        for name, new_shortcut in args.specific_rules:
            existing_rules[name] = {
                "name": name,
                "new_shortcut": new_shortcut,
            }
        config["specific"] = existing_rules

    return config


def find_matching_brace(content: str, open_brace_index: int) -> int | None:
    """Returns the matching closing brace index, ignoring braces in strings/comments."""
    depth = 0
    quote: str | None = None
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


def iter_button_type_blocks(content: str) -> Iterator[tuple[int, int]]:
    """Yields balanced Paradox `buttonType = { ... }` block spans."""
    pattern = re.compile(r"\bbuttonType\s*=\s*\{", flags=re.IGNORECASE)

    for match in pattern.finditer(content):
        open_brace_index = content.find("{", match.start(), match.end())
        close_brace_index = find_matching_brace(content, open_brace_index)
        if close_brace_index is not None:
            yield match.start(), close_brace_index + 1


def has_named_button(block: str, target_name: str) -> bool:
    name_pattern = re.compile(
        rf'\bname\s*=\s*(["\']){re.escape(target_name)}\1'
    )
    return bool(name_pattern.search(block))


def replace_shortcuts_in_block(block: str, new_shortcut: str) -> str:
    shortcut_pattern = re.compile(r'(\bshortcut\s*=\s*)(["\'])(.*?)\2')
    return shortcut_pattern.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{new_shortcut}{match.group(2)}",
        block,
    )


def apply_hotkey_replacements(content: str, config: dict[str, Any]) -> str:
    """
    Applies replacements directly to the file content using Regex.
    This preserves the original file formatting perfectly.
    """
    count = []

    # 1. Global Replacements (Search-All)
    global_rules = config.get("global", {})
    if global_rules:
        # Build a single regex pattern: \bshortcut\s*=\s*"(key1|key2|key3)"
        escaped_keys = [re.escape(k) for k in global_rules.keys()]
        pattern = r'\bshortcut\s*=\s*"(' + '|'.join(escaped_keys) + r')"'

        # Callback function to handle the replacement logic for each match found
        def replace_match(match):
            old_key = match.group(1)
            new_key = global_rules[old_key]
            count.append((old_key, new_key))
            return f'shortcut = "{new_key}"'

        # re.sub does a single pass, completely preventing cascading replacements
        content = re.sub(pattern, replace_match, content)

    # 2. Specific Replacements (Targeted by 'name')
    specific_rules = config.get("specific", [])
    for rule in specific_rules:
        target_name = rule["name"]
        new_shortcut = rule["new_shortcut"]

        updated_parts: list[str] = []
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


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    logger: deque[str] = deque()
    config = load_config(args.config)
    config = apply_config_overrides(config, args)

    source_dir = Path(config.get("target_directory", "./interface")).resolve()
    output_dir = Path(config.get("output_directory", "./output")).resolve()

    validate_directory(output_dir, source_dir)

    shutil.rmtree(output_dir, ignore_errors=True)
    gui_files = source_dir.rglob("*.gui")

    last = ""
    for file_path in gui_files:
        if last != file_path.parent:
            print(f"Inspecting: {file_path.parent}")
            last = file_path.parent

        try:
            content = file_path.read_text(encoding="utf-8")
            new_content = apply_hotkey_replacements(content, config)

            if new_content != content:
                output_path = output_dir / file_path

                try:
                    validate_directory(output_path)
                except ValueError as e:
                    raise PermissionError(
                        f"Target path '{output_path}' falls within a protected game or storefront library."
                    ) from e
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  -> [SUCCESS] Wrote updated hotkeys to {output_path}")

        except Exception as e:
            logger.append(f"  -> [ERROR] Could not process {file_path}: {e}")

    if logger:
        print()
        for msg in logger:
            print(msg)


def validate_directory(output_dir: Path, source_dir: Optional[Path] = None):
    if source_dir and (output_dir == source_dir or source_dir in output_dir.parents):
        raise ValueError(
            f"Output directory must not be the source directory or inside it: {output_dir}"
        )

    if (output_dir / "descriptor.mod").exists():
        raise ValueError(
            f"Output directory appears to be a mod root and will not be removed: {output_dir}"
        )

    output_parts = output_dir.parts
    paradox_games = [
        # Jomini Engine / Modern Releases
        "Imperator Rome",
        "Crusader Kings III",
        "Victoria 3",
        "Europa Universalis V",

        # Clausewitz Engine Staples (Active Playerbases)
        "Hearts of Iron IV",
        "Europa Universalis IV",
        "Stellaris",

        # Classic Legacy Titles (Persistent Modding/Player Communities)
        "Crusader Kings II",
        "Victoria II",
        "Hearts of Iron III"
    ]
    storefront_markers = {
        "steamapps",  # Steam Library
        "epic games",  # Epic Games Store default
        "gog games",  # GOG default (Linux / Custom Windows)
        "gog galaxy",  # GOG Galaxy default library path
        "xboxgames",  # Xbox App / Windows Store default
        "origin games",  # Legacy EA App / Origin
        "ea games"  # Modern EA App
    }

    for game in paradox_games:
        if game in output_parts:
            raise ValueError(f"Output directory can't be in the {game} folder")

    intersection = storefront_markers & {part.lower() for part in output_parts}
    if intersection:
        raise ValueError(f"Output directory can't be in {list(intersection)[0].title()}")


if __name__ == "__main__":
    main()
