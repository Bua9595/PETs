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
- `Esc`: schliessen

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
