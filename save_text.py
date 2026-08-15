import os
import time

import folder_paths


def _highest_counter(full_output_folder, filename, ext=None):
    """Highest existing `{filename}_{counter}_...` counter in the folder.
    ext=None scans every file (Save Image's own counter isn't extension-aware);
    pass an extension to scan only same-type files. Returns 0 if none found."""

    def map_filename(fn):
        prefix_len = len(filename)
        prefix = fn[:prefix_len + 1]
        try:
            remainder = fn[prefix_len + 1:]
            base_remainder = remainder.split(".")[0]
            digits = int(base_remainder.split("_")[0])
        except Exception:
            digits = 0
        return digits, prefix

    try:
        candidates = os.listdir(full_output_folder)
    except FileNotFoundError:
        os.makedirs(full_output_folder, exist_ok=True)
        return 0

    if ext is not None:
        candidates = [f for f in candidates if f.endswith(ext)]

    try:
        return max(
            filter(
                lambda a: os.path.normcase(a[1][:-1]) == os.path.normcase(filename) and a[1][-1] == "_",
                map(map_filename, candidates),
            )
        )[0]
    except ValueError:
        return 0


def get_save_text_path(filename_prefix, output_dir, width=0, height=0, sync_with_images=False):
    """Same prefix-templating scheme as folder_paths.get_save_image_path.

    Counter logic depends on `sync_with_images`:
    - False (no 'images' input connected): standalone auto-increment, based only
      on this node's own .txt history — normal Save Image-style behavior.
    - True ('images' connected, guaranteeing this node runs after Save Image):
      adopt the highest existing counter in the folder as-is (that's the image
      just written this run) instead of incrementing past it, so the text
      lands on the exact same number. Falls back to a fresh increment if that
      number is already taken by an earlier .txt (e.g. re-running without a
      paired image, or a leftover file)."""

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

    if sync_with_images:
        counter = _highest_counter(full_output_folder, filename) or 1
        while os.path.exists(os.path.join(full_output_folder, f"{filename}_{counter:05}_.txt")):
            counter += 1
    else:
        counter = _highest_counter(full_output_folder, filename, ext=".txt") + 1

    return full_output_folder, filename, counter, subfolder, filename_prefix


class PhoenixSaveText:
    DESCRIPTION = (
        "Saves text to the ComfyUI output directory using the same "
        "filename_prefix templating (%date%, %time%, %width%, %height% "
        "placeholders, subfolders via a path in the prefix) as the built-in "
        "Save Image node. Connect the optional 'images' input from your "
        "Save Image node (not saved, only used to force this node to run "
        "after it) to make this node adopt that image's exact counter "
        "instead of keeping its own — so a prefix like 'AAA/myImage' lines "
        "up as myImage_00023_.txt next to myImage_00023_.png even if only "
        "some earlier images had a matching text file. Without 'images' "
        "connected, it auto-increments on its own .txt history instead."
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
                    "tooltip": "Not saved. Connect your Save Image node's images output here so this node runs after it and adopts its exact counter.",
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
            filename_prefix, self.output_dir, width, height, sync_with_images=images is not None
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
