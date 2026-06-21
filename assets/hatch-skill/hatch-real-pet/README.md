# Local hatch-real-pet Copy

Diese Kopie dient im Projekt nur als lokale Referenz fuer Skill-Dateien,
Codex-Contract-Validierung und Packaging.

Sie ist nicht die Desktop-Runtime.

Fuer PET1 / Ruffy gilt:

- Runtime-Quelle: `assets/pets/ruffy/manifest.json`
- Runtime-Atlas: `assets/pets/ruffy/spritesheet.png`
- Ruffy-Quellen: `assets/source/pet1_ruffy_*_source.png`
- Build-Pipeline: `python src/pet1_ruffy_builder.py`
- Codex-Nebenexport: `assets/codex/ruffy/`

Der Codex-Nebenexport wird aus demselben bereinigten Runtime-Atlas gebaut, damit
Skill-Package und Desktop-App nicht auseinanderlaufen.

Validierung:

```bash
python src/codex_pet_builder.py
python "C:\Users\F. Bujupi\.codex\skills\hatch-real-pet\hatch-real-pet\scripts\validate_atlas.py" assets\codex\ruffy\spritesheet.png --json-out assets\codex\ruffy\validation.json
```

Diese Skill-Kopie ist nicht die Quelle der Ruffy-State-Kuration selbst; die
Kuration liegt im Projekt-Builder `src/pet1_ruffy_builder.py`.
