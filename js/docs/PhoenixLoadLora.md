# Phoenix Load Lora

Applies a LoRA to the `model` (and `clip`, if set) stored inside a `model_clip_text` struct, exactly like the built-in LoRA loader (`comfy.sd.load_lora_for_models`). On top of that, it reads the LoRA's trigger keywords and accumulates them (newline-joined) into the struct's `keywords`.

`model_clip_text` is this node's only input and only output. Chain multiple LoRAs by feeding one's output straight into the next one's input — a single link carries `model`, `clip` and the accumulated `keywords` together.

## Building and splitting the struct

- **Phoenix Pack Model/Clip/Text** produces the initial struct at the head of a chain, from a checkpoint loader's `model`/`clip` (and optionally a starting keywords text).
- **Phoenix Unpack Model/Clip/Text** splits the final struct back into `model`, `clip` and `keywords` at the end of the chain.

## Where keywords come from

Two sources are checked, and their results combined (duplicates removed, first source wins the order):

### 1. `loras_tags.json`

A JSON object at the ComfyUI root mapping a LoRA filename to a list of keyword strings, e.g.:

```json
{
  "my_lora.safetensors": ["trigger word", "another phrase"]
}
```

- The key must match the `lora_name` combo value; if not found, the file's basename is tried as a fallback (useful when the combo value includes a subfolder).
- If the file itself is missing or invalid JSON, this source simply contributes nothing.
- The file is re-read whenever its modification time changes, so edits take effect without restarting ComfyUI.

### 2. The LoRA file's own embedded metadata

Read directly from the `.safetensors` header (just the header, not the tensor weights — cheap even for a multi-GB file):

- `modelspec.trigger_phrase`, if present, is used as-is.
- Kohya-style training metadata (`ss_tag_frequency`, written by tools like Kohya's trainer or ai-toolkit) names its training folders `"<repeats>_<concept>"` — the concept name after the first underscore of each such folder name is used, e.g. `"1_ABCDE"` → `ABCDE`.

A LoRA with neither of these, or with a non-`.safetensors` format, simply contributes no keywords from this source — not an error.

## Error handling

If the struct's `model` is unset (e.g. **Phoenix Pack Model/Clip/Text** was never given one) and `strength_model` isn't 0, the node raises a clear error rather than crashing obscurely inside the LoRA-apply call.

## Bypassing a node in the chain

Since `model_clip_text` is both this node's only input and only output (same type), ComfyUI's node-bypass — which forwards an output to whatever is connected to the *same node's* same-type input — works correctly out of the box: bypassing any **Phoenix Load Lora** in the middle of a chain simply forwards the incoming struct unchanged to the next node.
