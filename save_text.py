import os
import time

import folder_paths


def get_save_text_path(filename_prefix, output_dir, ext=".txt"):
    """Same prefix-templating / counter scheme as folder_paths.get_save_image_path,
    but the counter only considers existing files with `ext`. Standalone use only —
    for text saved alongside images with guaranteed matching numbers, use
    PhoenixSaveImageAndText instead, which computes one counter for both files."""

    def map_filename(fn):
        prefix_len = len(os.path.basename(filename_prefix))
        prefix = fn[:prefix_len + 1]
        try:
            remainder = fn[prefix_len + 1:]
            base_remainder = remainder.split(".")[0]
            digits = int(base_remainder.split("_")[0])
        except Exception:
            digits = 0
        return digits, prefix

    def compute_vars(text):
        now = time.localtime()
        text = text.replace("%year%", str(now.tm_year))
        text = text.replace("%month%", str(now.tm_mon).zfill(2))
        text = text.replace("%day%", str(now.tm_mday).zfill(2))
        text = text.replace("%hour%", str(now.tm_hour).zfill(2))
        text = text.replace("%minute%", str(now.tm_min).zfill(2))
        text = text.replace("%second%", str(now.tm_sec).zfill(2))
        return text

    if "%" in filename_prefix:
        filename_prefix = compute_vars(filename_prefix)

    subfolder = os.path.dirname(os.path.normpath(filename_prefix))
    filename = os.path.basename(os.path.normpath(filename_prefix))

    full_output_folder = os.path.join(output_dir, subfolder)

    if not folder_paths.is_within_directory(output_dir, full_output_folder):
        raise Exception(
            "**** ERROR: Saving text outside the output folder is not allowed."
            f"\n full_output_folder: {os.path.abspath(full_output_folder)}"
            f"\n         output_dir: {output_dir}"
        )

    try:
        candidates = [f for f in os.listdir(full_output_folder) if f.endswith(ext)]
        counter = max(
            filter(
                lambda a: os.path.normcase(a[1][:-1]) == os.path.normcase(filename) and a[1][-1] == "_",
                map(map_filename, candidates),
            )
        )[0] + 1
    except ValueError:
        counter = 1
    except FileNotFoundError:
        os.makedirs(full_output_folder, exist_ok=True)
        counter = 1
    return full_output_folder, filename, counter, subfolder, filename_prefix


class PhoenixSaveText:
    DESCRIPTION = (
        "Saves standalone text to the ComfyUI output directory using the "
        "same filename_prefix templating (%date%, %time% placeholders, "
        "subfolders via a path in the prefix) and auto-incrementing "
        "counter scheme as the built-in Save Image node. The counter is "
        "based only on this node's own .txt history, so it's independent "
        "of any Save Image node — for text saved alongside images with "
        "guaranteed matching numbers, use 'Save Image + Text (Phoenix)' "
        "instead."
    )
    OUTPUT_NODE = True

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "forceInput": True, "multiline": True,
                    "tooltip": "The text to save.",
                }),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "tooltip": "Same syntax as Save Image's filename_prefix, e.g. 'AAA/myImage' or with %date:yyyy-MM-dd%.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "save_text"
    CATEGORY = "phoenix/text"

    def save_text(self, text, filename_prefix="ComfyUI"):
        full_output_folder, filename, counter, subfolder, _ = get_save_text_path(
            filename_prefix, self.output_dir
        )
        file = f"{filename}_{counter:05}_.txt"
        with open(os.path.join(full_output_folder, file), "w", encoding="utf-8") as f:
            f.write(text)

        return {"ui": {"text": [text]}, "result": (text,)}


NODE_CLASS_MAPPINGS = {
    "PhoenixSaveText": PhoenixSaveText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixSaveText": "💾 Save Text (Phoenix)",
}
