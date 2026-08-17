import json
import os

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths
from comfy.cli_args import args


class PhoenixSaveImageAndText:
    DESCRIPTION = (
        "Saves images together with up to two optional matching text "
        "files (e.g. a caption and a second variant), using the same "
        "filename_prefix templating as the built-in Save Image node. All "
        "files are written from a single counter computed once per call, "
        "so the numbers are always in sync (e.g. myImage_00023_.png next "
        "to myImage_00023_.txt and myImage_00023_2.txt) regardless of how "
        "the rest of the graph is wired. text2_postfix controls the "
        "second text file's suffix before the extension (default '2'). "
        "Connect 'path' to bypass filename_prefix/counter entirely and "
        "save at an exact location instead — full path, no extension, "
        "e.g. this node's own 'path' output, or a location outside the "
        "ComfyUI output folder."
    )
    OUTPUT_NODE = True

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save."}),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "tooltip": "The prefix for the files to save. Same syntax as Save Image, e.g. 'AAA/myImage' or with %date:yyyy-MM-dd%. Ignored if 'path' is connected.",
                }),
            },
            "optional": {
                "text": ("STRING", {
                    "forceInput": True, "multiline": True,
                    "tooltip": "The text to save alongside each image (e.g. a caption). Leave unconnected to save only the image.",
                }),
                "text2": ("STRING", {
                    "forceInput": True, "multiline": True,
                    "tooltip": "A second, optional text to save alongside each image (e.g. a second caption variant), using text2_postfix as its filename suffix. Leave unconnected to skip it.",
                }),
                "text2_postfix": ("STRING", {
                    "default": "2",
                    "tooltip": "Suffix appended to the filename (before the extension) for text2, e.g. myImage_00023_2.txt.",
                }),
                "path": ("STRING", {
                    "forceInput": True,
                    "tooltip": "Exact save location: full path without extension (e.g. from another Save Image + Text node's 'path' output). Overrides filename_prefix/counter — the image is saved as '<path>.png', the text (if given) as '<path>.txt'.",
                }),
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("images", "text", "path")
    FUNCTION = "save"
    CATEGORY = "phoenix/text"

    def save(self, images, filename_prefix="ComfyUI", text=None, text2=None, text2_postfix="2", path=None, prompt=None, extra_pnginfo=None):
        results = []
        last_base_path = ""

        if path:
            full_output_folder = os.path.dirname(path) or "."
            base_name = os.path.basename(path)
            os.makedirs(full_output_folder, exist_ok=True)
            try:
                subfolder = os.path.relpath(full_output_folder, self.output_dir)
                if subfolder.startswith(".."):
                    subfolder = ""
            except ValueError:
                subfolder = ""
        else:
            full_output_folder, base_name, counter, subfolder, _ = folder_paths.get_save_image_path(
                filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
            )

        for batch_number, image in enumerate(images):
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            if path:
                base = base_name if len(images) == 1 else f"{base_name}_{batch_number}"
            else:
                filename_with_batch_num = base_name.replace("%batch_num%", str(batch_number))
                current_counter = counter + batch_number
                base = f"{filename_with_batch_num}_{current_counter:05}_"

            base_path = os.path.join(full_output_folder, base)
            last_base_path = base_path

            img.save(base_path + ".png", pnginfo=metadata, compress_level=self.compress_level)
            if text is not None:
                with open(base_path + ".txt", "w", encoding="utf-8") as f:
                    f.write(text)
            if text2 is not None:
                with open(base_path + text2_postfix + ".txt", "w", encoding="utf-8") as f:
                    f.write(text2)

            results.append({
                "filename": base + ".png",
                "subfolder": subfolder,
                "type": self.type,
            })

        return {"ui": {"images": results}, "result": (images, text, last_base_path)}


NODE_CLASS_MAPPINGS = {
    "PhoenixSaveImageAndText": PhoenixSaveImageAndText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixSaveImageAndText": "💾 Save Image + Text (Phoenix)",
}
