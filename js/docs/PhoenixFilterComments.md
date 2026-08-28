# Phoenix Filter Comments

Removes comment lines from `text` entirely, so they never reach whatever comes next (e.g. a plain CLIP Text Encode).

A line is a comment if it starts with `#`, ignoring leading whitespace — the whole line is dropped, not just the `#` onward. Every other line passes through unchanged, in the same order.

## Output

- `text` — the input with all comment lines removed.
