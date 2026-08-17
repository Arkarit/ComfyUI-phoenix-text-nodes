# ComfyUI-phoenix-text-nodes

Eigenes Node-Pack für ComfyUI.

## Nodes

- **PhoenixTextConcat** — Beispiel-Node, verkettet zwei Strings mit Trennzeichen.
- **PhoenixRandomCSVTextReplace** — ersetzt fortlaufende Platzhalter ($1, $2, ...) in einem Text durch einen zufällig gewählten Begriff aus einer CSV-Kandidatenliste (eine Zeile pro Platzhalter). Portiert von [comfyui-text-placeholder-randomizer](https://github.com/Arkarit/comfyui-text-placeholder-randomizer), dessen `RandomCSVTextReplace`-Node unabhängig davon weiter existiert.
  - Standardmäßig sind Zeilen unabhängig — derselbe Begriff kann mehrfach gezogen werden.
  - `unique` (Bool): aktiviert, verhindert, dass ein Begriff in diesem Durchlauf für mehr als einen Platzhalter gezogen wird (zeilenübergreifend).
  - Feinsteuerung pro Zeile: das Feld `_UNIQUE_` in eine CSV-Zeile aufnehmen, um nur diese Zeile(n) gegenseitig eindeutig zu machen — unabhängig vom `unique`-Bool. Das Keyword wird vor der Auswahl aus der Kandidatenliste entfernt, ist selbst also kein möglicher Wert. Wirkt nur zwischen mehreren so markierten Zeilen (bei nur einer markierten Zeile gibt es nichts, wovon sie sich abgrenzen könnte). Sind bei einer eindeutigen Zeile bereits alle Kandidaten vergeben, wird trotzdem aus der vollen Liste gezogen (Wiederholung statt unaufgelöstem Platzhalter).
  - Enthält eine Zeile nur das Feld `_NONE_` (z.B. Zeile 5 = `_NONE_`), wird der zugehörige Platzhalter (`$5`) komplett aus der Ausgabe entfernt statt durch einen Begriff ersetzt.
- **PhoenixSaveText** — speichert eigenständigen Text mit demselben `filename_prefix`-Schema (inkl. `%date%`-Platzhaltern, Unterordnern) und Auto-Counter-Prinzip wie `Save Image`. Der Counter basiert nur auf der eigenen `.txt`-Historie — für Text, der garantiert dieselbe Nummer wie ein zugehöriges Bild bekommen soll, stattdessen **PhoenixSaveImageAndText** benutzen (siehe unten).
- **PhoenixSaveImageAndText** — speichert Bilder zusammen mit bis zu zwei optionalen begleitenden Texten (z.B. Captions) unter demselben Schema wie `Save Image`. Alle Dateien nutzen einen einzigen, in diesem einen Funktionsaufruf berechneten Counter, z.B. `AAA/myImage_00023_.png` + `AAA/myImage_00023_.txt` — dadurch garantiert synchron, unabhängig davon, wie der restliche Graph verdrahtet ist. (Zwei separate Save-Image/Save-Text-Nodes, die beide direkt an derselben Bildquelle hängen, haben *keine* erzwungene Ausführungsreihenfolge zueinander — je nachdem, welche zuerst dran ist, verschiebt sich die Nummer um eins. Deshalb diese kombinierte Node, wenn Bild und Text zusammengehören sollen.)
  - `text` ist optional — unverbunden wird nur das Bild gespeichert, keine `.txt`.
  - `text2` (optional) — ein zweiter, unabhängiger Text (z.B. eine zweite Caption-Variante), unverbunden wird er nicht gespeichert. Dateiname nutzt `text2_postfix` (default `"2"`) als Suffix vor der Extension, z.B. `AAA/myImage_00023_2.txt`.
  - `path` (optional) überschreibt `filename_prefix`/Counter komplett: kompletter Pfad ohne Extension, z.B. von einer anderen Instanz dieser Node. Bild wird als `<path>.png` gespeichert, `text` (falls angegeben) als `<path>.txt`, `text2` (falls angegeben) als `<path><text2_postfix>.txt`. Damit auch außerhalb des ComfyUI-Output-Ordners nutzbar (z.B. direkt ins Trainingsdatenset schreiben).
  - `path`-Ausgang liefert exakt das Format, das der `path`-Eingang einer anderen Instanz dieser Node erwartet — zum Verketten mehrerer Save-Nodes auf denselben Pfad.
- **PhoenixAppendText** — hängt ein festes Textfeld an einen eingehenden String an und gibt das Ergebnis aus.
- **PhoenixLoadText** — lädt eine `.txt`-Datei über einen Pfad mit Wildcards (`*`, `?`, `[seq]`, `**` für rekursiv), z.B. `input/random/random*.txt`. Relative Pfade werden gegen das ComfyUI-Root aufgelöst; Treffer werden alphabetisch sortiert.
  - `index`: `-1` = zufälligen Treffer wählen (per `seed`), `0` = ersten Treffer nehmen, `>0` = Treffer an dieser Position (`1` = zweiter Treffer, ...).
  - `seed` + `control_after_generate`: wie bei KSampler — wird nur bei `index = -1` verwendet.
  - `preview`: read-only Widget, zeigt den geladenen Text, oder bei keinem Treffer "No Text found" plus Grund (kein Pfad, kein Match, Index außerhalb des Bereichs, Datei nicht lesbar). Der `text`-Ausgang ist in diesem Fall leer.

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
