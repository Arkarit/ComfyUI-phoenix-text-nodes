# Phoenix Unpack Model/Clip/Text

The inverse of **Phoenix Pack Model/Clip/Text**: takes a `model_clip_text` struct (its only input, from that node or from **Phoenix Load Lora**) and splits it back into `model`, `clip` and `keywords`.

## Output

- `model` / `clip` / `keywords` — the values stored in the struct.
- `keywords` gets one trailing newline appended after the last entry, but only if there's at least one keyword (an empty struct keeps `keywords` as an empty string, not just a newline).
