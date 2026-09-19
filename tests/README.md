# Regression tests

From the repository root:

```sh
python3 -m unittest discover -s tests -v
node tests/run_node_toggle.mjs
python3 -m compileall -q .
git diff --check
```

The Python tests use the standard library and stub only ComfyUI's server
registration and JSON response boundary. They exercise the actual parser,
selection, node execution and HTTP handler. The JavaScript tests execute the
actual extension with a small graph and mocked API responses; they cover active,
bypassed, multiply bypassed and muted intermediate nodes, virtual routing and
reversed canvas order. These tests do not validate ComfyUI's real serialization
or rendering behavior. Node.js is a development tool, not a node-pack dependency.

## Manual ComfyUI check

Restart the backend after Python edits and reload the browser after JS edits.
Use a copy of a workflow and a fixed seed (for example 0).

1. In Flex Concat V2, set count to 10 and template to `$1 / $10 / $2`.
   Connect `eins` to input 1 and `zehn` to input 10, leaving input 2 empty.
   Expect `eins / zehn / $2`. Save and reload the workflow and repeat.
2. Connect the defines output of Random CSV A to B, and B to C. Give each
   node text `$1`. A's terms: `See _DEFINE(See)_`. B's terms:
   `_IF(See)_ Boot _DEFINE(See)_`. Disable pass-through on B. C's terms:
   `Land, _IF(See)_ Wasser`. Expect `Wasser` from C.
3. For a visible toggle, add a bypassable LoRA node titled `TestLoRA` and set
   C's terms to `Land, _IF(See)_ Wasser _NODE(TestLoRA)_`. Bypass B and queue:
   expect C to output `Wasser` and TestLoRA to be active in that same prompt.
   Change A's terms to `Wald`: expect `Land` and TestLoRA bypassed. Restore B
   and repeat. Also test two bypassed nodes and a Get/Set connection if used.
4. Load an older saved workflow with these nodes, queue twice, and check
   socket links, preview text and LoRA state. Automated tests cannot confirm
   compatibility with the installed ComfyUI frontend or other extensions.
