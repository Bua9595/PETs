# Hatch Pet Hinweise

Die echte App ist `src/desktop_pet.py`.

## Reale Runtime-Befehle

```bash
python src/desktop_pet.py --list-pets
python src/desktop_pet.py --pet ruffy --scale 0.5
python src/desktop_pet.py --pet pet2_chibi --scale 0.5
```

## Builder

PET 1 / Ruffy:

```bash
python src/pet1_100sheet_builder.py
```

PET 2 / Chibi Girl:

```bash
python src/pet2_chibi_builder.py
```

Codex-Nebenexport fuer Ruffy:

```bash
python src/codex_pet_builder.py
```

## Rolle von hatch-real-pet

Die lokale Kopie unter

```text
assets/hatch-skill/hatch-real-pet/
```

wird hier fuer Validierung und Packaging genutzt. Sie ist nicht die Quelle der
Desktop-Runtime-Dateien.

## Reale Quellen der Wahrheit

```text
assets/pets/ruffy/manifest.json
assets/pets/ruffy/spritesheet.png
assets/pets/pet2_chibi/manifest.json
assets/pets/pet2_chibi/spritesheet.png
```

## Bekannter Codex-Blocker

In dieser Codex-Umgebung kann Tk wegen fehlendem `init.tcl` nicht sichtbar
starten. Manifest-, Atlas- und `--list-pets`-Pruefung funktionieren trotzdem.
