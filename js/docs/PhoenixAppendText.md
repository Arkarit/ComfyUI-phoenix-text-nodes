# Phoenix Append Text

Appends a fixed string to the end of `text`.

## Inputs

- `text` — the input text.
- `append` — text appended to the end. Multiline, so you can also start it with a literal newline if you want a gap before it.
- `separator` — what to insert *between* `text` and `append`:

  | Value | Inserted |
  | --- | --- |
  | `none` (default) | nothing — direct concatenation |
  | `newline` | `\n` |
  | `blank line` | `\n\n` |
  | `space` | a single space |

  The separator is only inserted when **both** parts are non-empty, so an empty `append` or an empty incoming `text` never produces a stray trailing newline.

## Output

- `text` — `text + separator + append`.

## Notes

Keep `separator` at `none` when building filenames (e.g. appending `_upscaled` to a filename prefix for **Phoenix Save Image + Text**). Use `newline` when appending a prompt footer, especially one that starts with a `#` comment line — otherwise the comment swallows the end of the incoming text and a later **Phoenix Filter Comments** removes both.
