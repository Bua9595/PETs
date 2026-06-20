# Hatch Desktop Pet

Lokales Desktop-Pet-Projekt mit waehlbaren Pets. Die echte Runtime ist
`src/desktop_pet.py`.

## Start

```bash
python src/desktop_pet.py --list-pets
python src/desktop_pet.py --pet ruffy --scale 0.5
python src/desktop_pet.py --pet pet2_chibi --scale 0.5
```

Steuerung:

- Ziehen mit linker Maustaste
- Doppelklick: pet-spezifische Reaktion aus dem Manifest
- Rechtsklick: Animationsmenue
- `Esc`: Schliessen

## Aktive Pet-Struktur

Source of truth pro Pet:

- `assets/pets/ruffy/manifest.json`
- `assets/pets/ruffy/spritesheet.png`
- `assets/pets/pet2_chibi/manifest.json`
- `assets/pets/pet2_chibi/spritesheet.png`

Kompatibilitaets-/Nebenexporte:

- `assets/ruffy_sprite_manifest.json`
- `assets/sprites/ruffy_spritesheet.png`
- `assets/codex/ruffy/`

## PET 1 / Ruffy

Quellen:

- `assets/source/pet1_ruffy_100_source_sheet.png`
- `assets/source/pet1_ruffy_gear5_32_source_sheet.png`
- `assets/source/pet1_ruffy_power_32_source_sheet.png`

Status:

- Full-body erreicht
- `gear2`, `gear3`, `gear4`, `gear5` getrennt
- `gear3` kommt aus dem Power-Sheet
- normales Hauptsheet ist weiter nicht crispy-clean

Relevante QA:

- `assets/pets/ruffy/contact_sheet.png`
- `assets/pets/ruffy/qa/contact_sheet_dark.png`
- `assets/pets/ruffy/qa/contact_sheet_magenta.png`
- `assets/pets/ruffy/qa/halo_report.json`
- `assets/pets/ruffy/review.gif`

## PET 2 / Chibi Girl

Charakter:

- langes braunes Haar
- grosse blaue Augen
- violette Haaraccessoires
- schwarz/pinkes Outfit
- cute gamer / streamer / social vibe

Referenz:

- `assets/source/pet2_chibi_reference_sheet.png`

Aktuelles Runtime-Mindestset:

- `idle`
- `blink`
- `wave`
- `happy`
- `walk`
- `run`
- `jump`
- `rest`
- `wink`
- `shy`
- `gaming`
- `chat`
- `phone`
- `celebrate`

PET2-Artefakte:

- `assets/pets/pet2_chibi/contact_sheet.png`
- `assets/pets/pet2_chibi/qa/contact_sheet_dark.png`
- `assets/pets/pet2_chibi/qa_report.json`
- `assets/pets/pet2_chibi/review.gif`
- `assets/pets/pet2_chibi/previews/*.gif`
- `assets/pets/pet2_chibi/runtime_test.txt`

## PET 2 Ausbauplan Richtung ~100 Frames

- `core_idle_movement`: idle variations, blink variants, walk cycle, jump land, sit rest
- `social_cute_reactions`: wave, wink, shy, heart, happy sparkle, laugh, surprise
- `gamer_streamer`: gaming, laptop, phone, chat, celebrate, focus mode, headset adjust
- `counter_strike_inspired`: queue wait, tactical think, clutch celebrate, peek pose, rank pride, desk competitive mode
- `desktop_interaction`: drag react, cursor follow, sit on edge, hang, folder peek, window peek, object inspect
- `multi_pet_interaction`: greet other pet, wave to other pet, play together, sit together, celebrate together, follow other pet

## Builder / QA

PET1 neu bauen:

```bash
python src/pet1_100sheet_builder.py
```

PET2 neu bauen:

```bash
python src/pet2_chibi_builder.py
```

Codex-Export fuer Ruffy neu bauen:

```bash
python src/codex_pet_builder.py
```

Codex-Atlas validieren:

```bash
python "C:\Users\F. Bujupi\.codex\skills\hatch-real-pet\hatch-real-pet\scripts\validate_atlas.py" assets\codex\ruffy\spritesheet.png --json-out assets\codex\ruffy\validation.json
```

## Multi-Pet-Vorbereitung

Bereits im PET2-Manifest vorhanden:

- `personality_tags`
- `interaction_tags`
- `compatible_group_actions`
- `desktop_behavior`

Geplant spaeter:

- echte Pet-zu-Pet-Reaktionen in der Runtime
- gemeinsame Group Actions
- koordinierte Positionierung mehrerer Pets

## Bekannte Grenzen

- Die Codex-Umgebung kann das Tk-Fenster aktuell nicht sichtbar starten wegen:

```text
_tkinter.TclError: Can't find a usable init.tcl
```

- `--list-pets`, Manifest-Load und Atlas-Load sind pruefbar.
- PET1 ist visuell noch nicht final wegen Halo am Hauptsheet.
- PET2 ist als eigenes Pet integriert, aber die sichtbare GUI-Runtime konnte hier wegen Tcl/Tk nicht endgueltig bestaetigt werden.
