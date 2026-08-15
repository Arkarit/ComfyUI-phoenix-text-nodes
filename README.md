# ComfyUI-phoenix-text-nodes

Eigenes Node-Pack für ComfyUI. Enthält aktuell einen Beispiel-Node (`PhoenixTextConcat`) als Vorlage.

## Neuen Node hinzufügen

1. Node-Klasse in `nodes.py` (oder einer neuen Datei) anlegen — mindestens `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, `CATEGORY`.
2. In `NODE_CLASS_MAPPINGS` und `NODE_DISPLAY_NAME_MAPPINGS` (unten in `nodes.py`) eintragen.
3. ComfyUI neu starten.

Wächst das Pack, `nodes.py` in mehrere Dateien aufteilen und in `__init__.py` importieren — Mappings dabei zusammenführen (`{**a.NODE_CLASS_MAPPINGS, **b.NODE_CLASS_MAPPINGS}`).

## Web-Extensions (JS)

Der `js/`-Ordner ist vorbereitet. Sobald dort `.js`-Dateien liegen, `WEB_DIRECTORY = "js"` in `__init__.py` einkommentieren.

## Dependencies

Nur in `requirements.txt` eintragen, wenn wirklich nötig — alle Node-Packs teilen sich Stability Matrix' ComfyUI-venv, siehe `requirements.txt` für Details zum NumPy/numba-Konflikt vom Update heute.

## Veröffentlichen (optional)

`pyproject.toml` ist für die [Comfy Registry](https://registry.comfy.org) vorbereitet (`comfy node publish` via [comfy-cli](https://github.com/Comfy-Org/comfy-cli)). `PublisherId` und Repository-URL vor Veröffentlichung anpassen.
