import glob
import os
import random

import folder_paths


def _resolve_pattern(path):
    if os.path.isabs(path):
        return path
    return os.path.join(folder_paths.base_path, path)


class PhoenixLoadText:
    DESCRIPTION = (
        "Loads a text file matched by a wildcard path (e.g. "
        "input/random/random*.txt — supports *, ?, [seq], and ** for "
        "recursive matching). A relative path resolves against the "
        "ComfyUI root (which contains the input/output folders); use a "
        "path starting with a drive letter or leading slash for an "
        "OS-absolute path instead. Matches are sorted alphabetically for "
        "a stable order, then index picks one: -1 = random match (via "
        "seed), 0 = first match, N>0 = the match at that position (1 = "
        "second match, 2 = third, ...). If no file is found (empty "
        "path, no match, index out of range, unreadable file), the text "
        "output falls back to alternative_text, loaded is False, and the "
        "preview widget explains why."
    )
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {
                    "default": "input/random/random*.txt",
                    "tooltip": (
                        "File path with wildcards (*, ?, [seq], ** for recursive). "
                        "Relative paths resolve against the ComfyUI root."
                    ),
                }),
                "index": ("INT", {
                    "default": -1, "min": -1, "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "-1 = random match (uses seed). 0 = first match. >0 = match at that position (1 = second match, ...).",
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "control_after_generate": True,
                    "tooltip": "Only used when index is -1. Same seed + same matches always picks the same file.",
                }),
            },
            "optional": {
                "alternative_text": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Output when no file could be loaded, instead of an empty string.",
                }),
                "preview": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Read-only preview of the loaded text, or the reason none was found. Not an input; updates after each run.",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("text", "loaded")
    FUNCTION = "load"
    CATEGORY = "phoenix/text"

    def load(self, path, index, seed, alternative_text="", preview=""):
        text, message, loaded = self._load_text(path, index, seed, alternative_text)
        return {"ui": {"text": [message]}, "result": (text, loaded)}

    def _load_text(self, path, index, seed, alternative_text):
        path = (path or "").strip()
        if not path:
            return alternative_text, "No Text found: no path specified. Using alternative text.", False

        matches = sorted(
            m for m in glob.glob(_resolve_pattern(path), recursive=True)
            if os.path.isfile(m)
        )
        if not matches:
            return alternative_text, f"No Text found: no files matched pattern '{path}'. Using alternative text.", False

        if index == -1:
            chosen = random.Random(seed).choice(matches)
        elif index < len(matches):
            chosen = matches[index]
        else:
            return alternative_text, (
                f"No Text found: index {index} out of range "
                f"(only {len(matches)} file(s) matched '{path}'). Using alternative text."
            ), False

        try:
            with open(chosen, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            return alternative_text, f"No Text found: failed to read '{chosen}': {e}. Using alternative text.", False

        return content, content, True


NODE_CLASS_MAPPINGS = {
    "PhoenixLoadText": PhoenixLoadText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixLoadText": "📄 Load Text (Phoenix)",
}
