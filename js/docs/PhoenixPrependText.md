# Phoenix Prepend Text

Prepends a fixed string to the start of `text`.

## Inputs

- `text` — the input text.
- `prepend` — text prepended to the start. Multiline, so you can also end it with a literal newline if you want a gap after it.
- `separator` — what to insert *between* `prepend` and `text`:

  | Value | Inserted |
  | --- | --- |
  | `none` (default) | nothing — direct concatenation |
  | `newline` | `\n` |
  | `blank line` | `\n\n` |
  | `space` | a single space |

  The separator is only inserted when **both** parts are non-empty, so an empty `prepend` or an empty incoming `text` never produces a stray leading newline.

## Output

- `text` — `prepend + separator + text`.

## Notes

If `prepend` ends with a `#` comment line and `separator` is left at `none`, the incoming text is glued onto the end of that comment line — a later **Phoenix Filter Comments** will then strip the prompt along with the comment. Set `separator` to `newline` for prompt headers; keep it at `none` for things like filename prefixes.
