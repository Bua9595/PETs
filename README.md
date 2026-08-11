# Hatch Desktop Pet

Lokales Desktop-Pet-Projekt mit mehreren Pets. Die echte Runtime ist
`src/desktop_pet.py`.

## Start

```bash
python src/desktop_pet.py --list-pets
python src/desktop_pet.py --pet ruffy --scale 0.5
python src/desktop_pet.py --pet pet2_chibi --scale 0.5
```

Steuerung:

- linke Maustaste ziehen: Pet verschieben
- Doppelklick: pet-spezifische Hauptaktion
- Rechtsklick: Animationsmenue
- `Esc`: Python/Tk-Verhalten weiterhin separat verifizieren; dies ist nicht
  identisch mit dem erfolgreich validierten Esc-Verhalten der Godot-Prototypen.

## Source Of Truth

Runtime pro Pet:

- `assets/pets/ruffy/manifest.json`
- `assets/pets/ruffy/spritesheet.png`
- `assets/pets/pet2_chibi/manifest.json`
- `assets/pets/pet2_chibi/spritesheet.png`

Der Desktop-Pet laedt diese Manifeste. Alte Root-Dateien wie
`assets/ruffy_sprite_manifest.json` oder `assets/sprites/ruffy_spritesheet.png`
sind nicht mehr Teil der PET1-Pipeline.

## Agenten- und Asset-Pipeline

Die verbindlichen Regeln für Cursor, Codex und Asset-Verarbeitung liegen in:

* `docs/PET_AGENT_CONTRACT.md`
* `docs/PET_ASSET_PIPELINE.md`
* `docs/PET_STATE_INDEX.md`

Nur Sprites unter `assets/source_approved/` gelten als finale Quelle für Runtime-Assets.
Rohbilder und fehlerhafte Sheets dürfen nicht direkt in den Runtime-Atlas übernommen werden.

Das aktuelle Rohquellen-Inventar liegt in `docs/PET_SOURCE_INVENTORY.md`.

Der Review-Prozess für Sprite-Kandidaten ist in `docs/PET_REVIEW_WORKFLOW.md` dokumentiert.

Aktuelle Review-Dateien werden je Schritt unter `assets/review/reports/` erzeugt. Für Ruffy normal liegt die aktuelle Re-Extraction-Liste unter `assets/review/reports/ruffy_normal_reextract_review.csv`.

Alte fehlerhafte Bildquellen wurden gesichert unter `backups/deprecated_sprite_sources_20260627.zip` und aus der aktiven Pipeline entfernt.

## PET 1 / Ruffy

PET1 wurde am 2026-06-21 aus den neuen fuenf Magenta-Quellen neu gebaut:

- `assets/source/pet1_ruffy_base_source.png`
- `assets/source/pet1_ruffy_gear2_source.png`
- `assets/source/pet1_ruffy_gear3_source.png`
- `assets/source/pet1_ruffy_gear4_source.png`
- `assets/source/pet1_ruffy_gear5_source.png`

Runtime-Artefakte:

- `assets/pets/ruffy/spritesheet.png`
- `assets/pets/ruffy/manifest.json`
- `assets/pets/ruffy/contact_sheet.png`
- `assets/pets/ruffy/qa/qa_table.md`
- `assets/pets/ruffy/previews/*.gif`
- `assets/codex/ruffy/` als Nebenexport aus demselben Runtime-Atlas

Animationen:

`idle`, `blink`, `wave`, `happy`, `surprised`, `thinking`, `curious`,
`walk`, `run`, `jump`, `sit`, `rest`, `failed`, `celebrate`, `drag_react`,
`cursor_follow`, `rubber_stretch`, `rubber_punch`, `rubber_reach`,
`rubber_kick`, `gear2`, `gear3`, `gear4`, `gear5`.

PET1 neu bauen:

```bash
python src/pet1_ruffy_builder.py
```

Der alte Befehl bleibt als Wrapper erhalten:

```bash
python src/pet1_100sheet_builder.py
```

## PET 2 / Chibi Girl

PET2 nutzt eigene Quellen und ist von PET1 getrennt:

- `assets/source/pet2_chibi_master_main.png`
- `assets/source/pet2_chibi_master_support.png`
- `assets/source/pet2_chibi_master_extra.png`
- `assets/pets/pet2_chibi/manifest.json`
- `assets/pets/pet2_chibi/spritesheet.png`

PET2 neu bauen:

```bash
python src/pet2_chibi_builder.py
```

## Verhalten

Die Runtime nutzt `desktop_behavior` aus dem jeweiligen Manifest:

- Kategorien mit Wechselwahrscheinlichkeit
- mehrere Versuche pro Kategorie vor einem Wechsel
- mindestens 60 Sekunden Cooldown pro Animation, bevor sie automatisch wieder
  ausgewaehlt wird
- Drag-, Doppelklick- und Rechtsklick-Aktionen pro Pet

## Manifest-Validierung

Bestehende Manifeste ohne `schema_version` werden als Version 1 behandelt.
Vor dem Start und in der Pack-Erkennung werden die statischen Runtime-Felder
validiert. Fehler nennen Pack, Feldpfad und Ursache; optionale unbekannte
Felder bleiben rückwärtskompatibel. PET2 bleibt trotz seines separaten
QA-Status auswählbar.

Headless-Tests und Manifest-Validierung ausführen:

```bash
python -m unittest discover -s tests -v
```

## QA

PET1-QA:

```bash
python src/pet1_ruffy_builder.py
type assets\pets\ruffy\qa\qa_table.md
```

Codex-Nebenexport validieren:

```bash
python src/codex_pet_builder.py
python "C:\Users\F. Bujupi\.codex\skills\hatch-real-pet\hatch-real-pet\scripts\validate_atlas.py" assets\codex\ruffy\spritesheet.png --json-out assets\codex\ruffy\validation.json
```

Der QA-Report prueft pro Animation `frames`, `min_margin_px`,
`edge_touch_count`, `chroma_edge_pixels`, `visible_cluster_count` und
`accepted`.

## Bekannte Grenzen

- PET1 `walk` und `run` haben nur zwei saubere eindeutige Base-Bewegungsposen;
  sie sind stabil, aber noch kein wirklich fluessiger Laufzyklus.
- Die neuen PET1-Quellen enthalten keine echten Gaming-/Laptop-/Phone-/Folder-
  oder Multi-Pet-Desktop-Props; solche States werden nicht gefakt.
- In dieser Umgebung kann das Tk-Fenster je nach Python/Tcl-Installation nicht
  sichtbar starten. `--list-pets`, Manifest-Load, Build und Atlas-Validierung
  sind pruefbar.

## Entwicklungs-Checkpoints und Godot-Machbarkeit

Die produktive Runtime bleibt derzeit `src/desktop_pet.py`. Die Godot-Projekte
unter `prototypes/` sind bewusst isolierte Machbarkeitsprototypen und ersetzen
die Python-Runtime noch nicht.

- Python-Fundament: `c6686db Add behavior, manifest, sensor and chase foundations`.
- Validierte Godot-Desktop-Shell:
  `a64f3046bccebc6714dba59800e20cb880a02428`
  (`Add validated Godot desktop pet shell prototype`).
- Validierter Godot-Polygon-Rig-Prototyp:
  `d6f874713905c2b0470751cee34faac24d0091a0`
  (`Add validated Godot 2D rig prototype`).
- Der texturierte Godot-Rig-Prototyp verwendet 21 externe SVG-Teile und einen
  manifest-gesteuerten Aufbau. Er hat getrennte Pupillen, eine begrenzte
  Cursor-Blickreaktion, die Animationen `idle_breath` und `wave`, eine
  Wave-Burst-Sperre sowie ein statisches transparentes Action-Canvas. Der
  sichtbare Windows-Test dieses Prototyps war erfolgreich.

## Produktionspipeline und Blue Fox

Die manifest-gesteuerte Produktionspipeline liegt in
`assets/pets/production_template/`, der gemeinsame Godot-Loader in
`godot/pet_manifest_loader.gd` und der technische Validator in
`src/production_pet_validator.py`.

`assets/pets/pet001_blue_fox/` ist der erste echte Durchlauf dieser Pipeline.
Der Pack enthält 30 geladene Produktionsparts einschließlich separat
gelayertem Schwanz und Wave-Arm-Set, dokumentierte Designreferenzen und ein
Version-1-Manifest. Der visuell geprüfte Stand bleibt im Produktionsworkflow
für weitere Freigabeschritte unter `needs_review`.

```powershell
python src/production_pet_validator.py assets/pets/pet001_blue_fox/metadata/pet_manifest.json
& 'C:\Tools\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64.exe' --path 'prototypes\godot_textured_rig_pet' -- --pet-manifest='C:\Users\Bujupi\Desktop\PETs\assets\pets\pet001_blue_fox\metadata\pet_manifest.json'
```

Bekannte offene Punkte:

- Der erste echte Godot-Produktionspack ist technisch validiert und noch nicht
  Teil einer produktiven Python-Runtime.
- Es gibt noch keine produktive Godot-Migration.
- Ein Godot-Kontextmenue ist noch nicht implementiert.
- Walk-/Chase-Verhalten fehlt im Godot-Pfad noch.
- Die alten Pose-Sprites bleiben Referenzen, sind aber nicht der kuenftige
  Hauptanimationspfad.
