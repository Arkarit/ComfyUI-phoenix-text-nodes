import os
import time

import folder_paths


def get_save_text_path(filename_prefix, output_dir, ext=".txt", width=0, height=0):
    """Same prefix-templating / counter scheme as folder_paths.get_save_image_path,
    but the counter only considers existing files with `ext` — Save Image's own
    counter isn't extension-aware, so an unfiltered scan here would make whichever
    of the two nodes runs second within a run get bumped one past the first."""

    def map_filename(filename):
        prefix_len = len(os.path.basename(filename_prefix))
        prefix = filename[:prefix_len + 1]
        try:
            remainder = filename[prefix_len + 1:]
            base_remainder = remainder.split(".")[0]
            digits = int(base_remainder.split("_")[0])
        except Exception:
            digits = 0
        return digits, prefix

    def compute_vars(text):
        text = text.replace("%width%", str(width))
        text = text.replace("%height%", str(height))
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
        "Saves text to the ComfyUI output directory using the same "
        "filename_prefix templating (%date%, %time%, %width%, %height% "
        "placeholders, subfolders via a path in the prefix) and "
        "auto-incrementing counter scheme as the built-in Save Image node "
        "— so a prefix like 'AAA/myImage' lines up with an accompanying "
        "Save Image node, e.g. myImage_00001_.txt next to "
        "myImage_00001_.png. Connect the optional 'images' input from "
        "your Save Image node (not saved, only used for ordering) to "
        "force this node to run after it, keeping the counters in sync."
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
            "optional": {
                "images": ("IMAGE", {
                    "tooltip": "Not saved. Connect your Save Image node's images output here to force this node to run after it, so the counters match.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "save_text"
    CATEGORY = "phoenix/text"

    def save_text(self, text, filename_prefix="ComfyUI", images=None):
        width = images[0].shape[1] if images is not None else 0
        height = images[0].shape[0] if images is not None else 0
        full_output_folder, filename, counter, subfolder, _ = get_save_text_path(
            filename_prefix, self.output_dir, ".txt", width, height
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
