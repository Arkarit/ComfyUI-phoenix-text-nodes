# Phoenix Load Text

Loads a text file matched by a wildcard `path` (supports `*`, `?`, `[seq]`, and `**` for recursive matching). A relative path resolves against the ComfyUI root (the folder containing `input`/`output`); start with a drive letter or a leading slash for an OS-absolute path instead.

Matches are sorted alphabetically for a stable order, then `index` picks one:

| `index` | Picks |
| --- | --- |
| `-1` | Random match, using `seed` (same seed + same matches → same file) |
| `0` | First match |
| `N` (>0) | The match at that position (`1` = second match, `2` = third, ...) |

## Fallback

If no file is found — empty path, no match, index out of range, or the file can't be read — `text` falls back to `alternative_text`, `loaded` is `False`, and the `preview` widget explains why (empty path / no match / index out of range / read error).

## Outputs

- `text` — the loaded file's content, or `alternative_text` on failure.
- `loaded` — `True` if a file was actually read, `False` on any fallback.
- A read-only `preview` widget on the node shows the loaded text, or the failure reason.
