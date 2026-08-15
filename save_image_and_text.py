import json
import os

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths
from comfy.cli_args import args


class PhoenixSaveImageAndText:
    DESCRIPTION = (
        "Saves images together with a matching text file (e.g. a caption), "
        "using the same filename_prefix templating as the built-in Save "
        "Image node. Both files are written from a single counter computed "
        "once per call, so the numbers are always in sync (e.g. "
        "myImage_00023_.png next to myImage_00023_.txt) regardless of how "
        "the rest of the graph is wired — unlike chaining a separate Save "
        "Image and Save Text node, where two independently-executing "
        "nodes can end up off by one depending on execution order."
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
                "text": ("STRING", {
                    "forceInput": True, "multiline": True,
                    "tooltip": "The text to save alongside each image (e.g. a caption). The same text is written next to every image in the batch.",
                }),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "tooltip": "The prefix for the files to save. Same syntax as Save Image, e.g. 'AAA/myImage' or with %date:yyyy-MM-dd%.",
                }),
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "text")
    FUNCTION = "save"
    CATEGORY = "phoenix/text"

    def save(self, images, text, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )
        results = []
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

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            current_counter = counter + batch_number
            base = f"{filename_with_batch_num}_{current_counter:05}_"

            img.save(os.path.join(full_output_folder, base + ".png"), pnginfo=metadata, compress_level=self.compress_level)
            with open(os.path.join(full_output_folder, base + ".txt"), "w", encoding="utf-8") as f:
                f.write(text)

            results.append({
                "filename": base + ".png",
                "subfolder": subfolder,
                "type": self.type,
            })

        return {"ui": {"images": results}, "result": (images, text)}


NODE_CLASS_MAPPINGS = {
    "PhoenixSaveImageAndText": PhoenixSaveImageAndText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixSaveImageAndText": "💾 Save Image + Text (Phoenix)",
}
