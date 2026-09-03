import json
import os
import struct

import comfy.sd
import comfy.utils
import folder_paths

from .model_clip_text import MODEL_CLIP_TEXT_TYPE, build_struct


def _tags_file_path():
    return os.path.join(folder_paths.base_path, "loras_tags.json")


class PhoenixLoadLora:
    DESCRIPTION = (
        "Applies a LoRA to a model_clip_text struct's model (and clip), "
        "reading its trigger keywords and accumulating them into the "
        "struct. See this node's Info tab (Properties Panel) for full "
        "details."
    )

    def __init__(self):
        self.loaded_lora = None
        self.loaded_tags = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_clip_text": (MODEL_CLIP_TEXT_TYPE, {
                    "tooltip": "Bundled model+clip+keywords, from Pack Model/Clip/Text (Phoenix) or another Load Lora (Phoenix).",
                }),
                "lora_name": (folder_paths.get_filename_list("loras"), {
                    "tooltip": "The name of the LoRA to load.",
                }),
                "strength_model": ("FLOAT", {
                    "default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01,
                    "tooltip": "How strongly to modify the diffusion model.",
                }),
                "strength_clip": ("FLOAT", {
                    "default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01,
                    "tooltip": "How strongly to modify CLIP. Only has an effect if the struct's clip is set.",
                }),
            },
        }

    RETURN_TYPES = (MODEL_CLIP_TEXT_TYPE,)
    RETURN_NAMES = ("model_clip_text",)
    FUNCTION = "load_lora"
    CATEGORY = "phoenix/loaders"

    def load_lora(self, model_clip_text, lora_name, strength_model, strength_clip):
        model = model_clip_text.get("model")
        clip = model_clip_text.get("clip")
        base_keywords = model_clip_text.get("keywords") or ""

        if strength_model == 0 and strength_clip == 0:
            model_lora, clip_lora = model, clip
        else:
            if model is None:
                raise ValueError(
                    "PhoenixLoadLora: model_clip_text has no model, and strength_model is not 0."
                )
            lora_path = folder_paths.get_full_path_or_raise("loras", lora_name)
            lora, lora_metadata = self._get_lora(lora_path)
            model_lora, clip_lora = comfy.sd.load_lora_for_models(
                model, clip, lora, strength_model, strength_clip, lora_metadata=lora_metadata
            )

        own_keywords = "\n".join(self._lookup_keywords(lora_name))
        keywords = "\n".join(part for part in (base_keywords, own_keywords) if part)

        return (build_struct(model_lora, clip_lora, keywords),)

    def _get_lora(self, lora_path):
        if self.loaded_lora is not None and self.loaded_lora[0] == lora_path:
            return self.loaded_lora[1], self.loaded_lora[2]
        lora, lora_metadata = comfy.utils.load_torch_file(lora_path, safe_load=True, return_metadata=True)
        self.loaded_lora = (lora_path, lora, lora_metadata)
        return lora, lora_metadata

    def _lookup_keywords(self, lora_name):
        keywords = list(self._lookup_json_keywords(lora_name))
        for kw in self._lookup_metadata_keywords(lora_name):
            if kw not in keywords:
                keywords.append(kw)
        return keywords

    def _lookup_json_keywords(self, lora_name):
        tags = self._get_tags()
        entries = tags.get(lora_name)
        if entries is None:
            entries = tags.get(os.path.basename(lora_name))
        return entries or []

    def _lookup_metadata_keywords(self, lora_name):
        try:
            lora_path = folder_paths.get_full_path_or_raise("loras", lora_name)
            metadata = self._read_safetensors_metadata(lora_path)
        except Exception:
            return []

        keywords = []

        trigger_phrase = metadata.get("modelspec.trigger_phrase")
        if trigger_phrase:
            keywords.append(trigger_phrase)

        raw_freq = metadata.get("ss_tag_frequency")
        if raw_freq:
            try:
                freq = json.loads(raw_freq) if isinstance(raw_freq, str) else raw_freq
            except (json.JSONDecodeError, TypeError):
                freq = {}
            for folder_name in freq:
                # Kohya training folder convention: "<repeats>_<concept>".
                _, _, concept = folder_name.partition("_")
                if concept and concept not in keywords:
                    keywords.append(concept)

        return keywords

    @staticmethod
    def _read_safetensors_metadata(path):
        if not path.lower().endswith((".safetensors", ".sft")):
            return {}
        with open(path, "rb") as f:
            header_len = struct.unpack("<Q", f.read(8))[0]
            header = json.loads(f.read(header_len))
        return header.get("__metadata__") or {}

    def _get_tags(self):
        path = _tags_file_path()
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            self.loaded_tags = None
            return {}

        if self.loaded_tags is not None and self.loaded_tags[0] == path and self.loaded_tags[1] == mtime:
            return self.loaded_tags[2]

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = {}

        self.loaded_tags = (path, mtime, data)
        return data


NODE_CLASS_MAPPINGS = {
    "PhoenixLoadLora": PhoenixLoadLora,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixLoadLora": "🧩 Load Lora (Phoenix)",
}
