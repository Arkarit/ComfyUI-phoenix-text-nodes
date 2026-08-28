# Phoenix Save Text

Saves `text` to the ComfyUI output directory using the same `filename_prefix` templating (subfolders via a path in the prefix, plus date/time placeholders) and auto-incrementing counter scheme as the built-in Save Image node.

The counter is based only on this node's own `.txt` file history in the target folder — it does not look at any images. If you need a text file that always shares the exact same counter as a saved image (e.g. `myImage_00023_.png` / `myImage_00023_.txt`), use **Save Image + Text (Phoenix)** instead, which computes one counter for both files from a single call.

## `filename_prefix`

| Example | Result |
| --- | --- |
| `ComfyUI` | `ComfyUI_00001_.txt`, `ComfyUI_00002_.txt`, ... |
| `AAA/myImage` | Saved into an `AAA` subfolder, e.g. `AAA/myImage_00001_.txt` |

The prefix also supports these placeholders, expanded from the current date/time before saving:

| Placeholder | Replaced with |
| --- | --- |
| `%year%` | 4-digit year |
| `%month%` | 2-digit month |
| `%day%` | 2-digit day |
| `%hour%` | 2-digit hour (24h) |
| `%minute%` | 2-digit minute |
| `%second%` | 2-digit second |

Saving outside the ComfyUI output folder is refused with an error.

## Output

- `text` — the same text that was passed in, unchanged, so this node can sit inline without breaking the graph.
