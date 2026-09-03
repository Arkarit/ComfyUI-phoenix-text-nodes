MODEL_CLIP_TEXT_TYPE = "PHOENIX_MODEL_CLIP_TEXT"


def build_struct(model, clip, keywords):
    return {"model": model, "clip": clip, "keywords": keywords or ""}
