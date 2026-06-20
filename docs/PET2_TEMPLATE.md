# PET 2 Notes

PET 2 ist jetzt als eigenes Pet unter `assets/pets/pet2_chibi/` angelegt.

## Runtime-Dateien

```text
assets/pets/pet2_chibi/
  manifest.json
  spritesheet.png
  row_sources/
  qa/
  previews/
  contact_sheet.png
  qa_report.json
  review.gif
```

## Quelle

```text
assets/source/pet2_chibi_reference_sheet.png
```

## Builder

```bash
python src/pet2_chibi_builder.py
```

## Start

```bash
python src/desktop_pet.py --list-pets
python src/desktop_pet.py --pet pet2_chibi --scale 0.5
```

## Aktueller Fokus

PET 2 ist als kleines Runtime-Mindestset integriert. Der groessere Ausbau auf
Richtung ~100 Frames ist als Backlog in `assets/pets/pet2_chibi/qa_report.json`
dokumentiert und wird nicht blind in einem Schritt erzeugt.
