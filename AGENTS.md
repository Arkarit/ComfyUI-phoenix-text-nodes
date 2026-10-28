# Repository Guidelines

## Project Structure & Module Organization

Python node implementations live at the repository root, usually one node per snake_case module. `__init__.py` combines node class/display-name mappings and exposes `WEB_DIRECTORY = "js"`. Shared helpers include `defines.py` and `model_clip_text.py`. Browser extensions live in `js/`, node help pages in `js/docs/Phoenix<NodeName>.md`, and the demo workflow image in `examples/demo_workflow.png`. There is currently no test directory.

## Build, Test, and Development Commands

Use ComfyUI's existing Python environment, with this repository installed under `ComfyUI/custom_nodes/`. The commands below assume its interpreter is available as `python`; otherwise use its explicit path.

- `python -m pip install -r requirements.txt` — install declared dependencies; the file currently contains only comments.
- `python -m compileall -q .` — check Python syntax from this repository; this does not validate ComfyUI integration.
- `python main.py` — launch ComfyUI from the **ComfyUI root**. Restart after Python changes and refresh the browser after JavaScript changes.
- `git diff --check` — check pending changes for whitespace errors.

There is no standalone build step or configured formatter/linter.

## Coding Style & Naming Conventions

Use four-space Python indentation, snake_case functions/modules, and `Phoenix`-prefixed PascalCase node classes. Retain ComfyUI API names such as `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, and `CATEGORY`. Follow existing JavaScript tab indentation, camelCase identifiers, and extension registration patterns.

For a new node, define both mapping dictionaries in its module, import it in `__init__.py`, and merge both mappings. Add its README entry and corresponding `js/docs/` help page.

## Testing Guidelines

No automated testing framework or coverage threshold is configured. Validate affected nodes in ComfyUI with a small reproducible workflow. Check empty inputs, optional sockets, bypass behavior, and existing saved workflows as relevant. For random selection changes, use fixed seeds; for save nodes, verify filenames and paired outputs in a temporary destination. Document validation steps and results in the PR.

## Commit & Pull Request Guidelines

Recent commits use concise imperative subjects such as `Add separator widget to Append/Prepend Text`. Follow that style. PRs should explain the behavior change, reference relevant issues, and include reproduction/validation steps; attach screenshots for visible UI changes.

## Compatibility & Dependencies

Preserve existing node identifiers and socket contracts. Keep deprecated `PhoenixFlexConcat` behavior unchanged; use V2 for fixes. Add dependencies only when necessary because node packs share ComfyUI's environment.
