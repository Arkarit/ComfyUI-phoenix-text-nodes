# ComfyUI-phoenix-text-nodes

Eigenes Node-Pack für ComfyUI.

## Nodes

- **PhoenixTextConcat** — Beispiel-Node, verkettet zwei Strings mit Trennzeichen.
- **PhoenixRandomCSVTextReplace** — ersetzt fortlaufende Platzhalter ($1, $2, ...) in einem Text durch einen zufällig gewählten Begriff aus einer CSV-Kandidatenliste (eine Zeile pro Platzhalter). Portiert von [comfyui-text-placeholder-randomizer](https://github.com/Arkarit/comfyui-text-placeholder-randomizer), dessen `RandomCSVTextReplace`-Node unabhängig davon weiter existiert.

## Neuen Node hinzufügen

1. Neue Datei (z.B. `mein_node.py`) mit der Node-Klasse anlegen — mindestens `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, `CATEGORY` — sowie eigenen `NODE_CLASS_MAPPINGS`/`NODE_DISPLAY_NAME_MAPPINGS` am Dateiende.
2. Datei in `__init__.py` importieren und ihre Mappings in `NODE_CLASS_MAPPINGS`/`NODE_DISPLAY_NAME_MAPPINGS` mit einmischen (`{**a.NODE_CLASS_MAPPINGS, **b.NODE_CLASS_MAPPINGS}`).
3. ComfyUI neu starten.

## Web-Extensions (JS)

`WEB_DIRECTORY = "js"` ist aktiv; `.js`-Dateien im `js/`-Ordner werden automatisch geladen (siehe `random_csv_text_replace_preview.js` für das Preview-Widget von `PhoenixRandomCSVTextReplace`).

## Dependencies

Nur in `requirements.txt` eintragen, wenn wirklich nötig — alle Node-Packs teilen sich Stability Matrix' ComfyUI-venv, siehe `requirements.txt` für Details zum NumPy/numba-Konflikt vom Update heute.

## Veröffentlichen (optional)

`pyproject.toml` ist für die [Comfy Registry](https://registry.comfy.org) vorbereitet (`comfy node publish` via [comfy-cli](https://github.com/Comfy-Org/comfy-cli)). `PublisherId` und Repository-URL vor Veröffentlichung anpassen.
