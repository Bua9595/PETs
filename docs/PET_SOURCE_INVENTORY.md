# PET Source Inventory

## Current production-rig source (2026-08-12)

The sprite inventory below remains the historical inventory for the Python
pose-sprite path. The separate manifest-driven Godot production path now has
one technically validated pack:

| Pack | Primary reference | Alternate reference | Rig parts | Status |
| ---- | ----------------- | ------------------- | --------- | ------ |
| `pet001_blue_fox` | `assets/pets/pet001_blue_fox/source/master_front_review_candidate_v2_five_fingers.png` | `assets/pets/pet001_blue_fox/source/alternate_hand_reference.png` | 30 manifest-loaded production parts under `parts/`, including separate tail and wave arm set | `needs_review`; technical and visible checkpoint completed |

These reference PNGs are design inputs, not runtime sprites. The production parts
and `metadata/pet_manifest.json` are the current rig sources of truth.

> **Status 2026-06-27:** Alte Raw-/Review-/source_cell-Bildquellen wurden nach Backup unter `backups/deprecated_sprite_sources_20260627.zip` aus dem aktiven Projekt entfernt. Sie sind nicht mehr aktive Pipeline-Quelle. Neue Approved-Sprites müssen aus neu geprüften Einzelquellen oder neu erzeugten sauberen Sheets stammen.

## Zweck

Dieses Dokument listet vorhandene Bildquellen und ordnet sie der neuen Asset-Pipeline zu.

Nur Dateien unter `assets/source_approved/` dürfen später als finale Runtime-Quelle verwendet werden.

Dateien unter `assets/source_raw/` sind Rohmaterial oder Referenzen und nicht automatisch verwendbar.

Stand: Inventar-Lauf am 2026-06-27. Es wurden nur Kopien angelegt, nichts verschoben oder gelöscht.

## Inventar

| Datei | Pet | Kategorie | Aktion | Begründung |
| ----- | --- | --------- | ------ | ---------- |
| `assets/source/pet1_ruffy_base_source.png` | ruffy | raw_sheet | copy_to_source_raw | Master-Quellsheet PET1 normal/base, eindeutig Ruffy. |
| `assets/source/pet1_ruffy_gear2_source.png` | ruffy | raw_sheet | copy_to_source_raw | Master-Quellsheet PET1 Gear2. |
| `assets/source/pet1_ruffy_gear3_source.png` | ruffy | raw_sheet | copy_to_source_raw | Master-Quellsheet PET1 Gear3. |
| `assets/source/pet1_ruffy_gear4_source.png` | ruffy | raw_sheet | copy_to_source_raw | Master-Quellsheet PET1 Gear4. |
| `assets/source/pet1_ruffy_gear5_source.png` | ruffy | raw_sheet | copy_to_source_raw | Master-Quellsheet PET1 Gear5. |
| `assets/source/pet2_chibi_master_main.png` | pet2_chibi | raw_sheet | copy_to_source_raw | Master-Quellsheet PET2 main, eindeutig Chibi-Girl. |
| `assets/source/pet2_chibi_master_support.png` | pet2_chibi | raw_sheet | copy_to_source_raw | Master-Quellsheet PET2 support. |
| `assets/source/pet2_chibi_master_extra.png` | pet2_chibi | raw_sheet | copy_to_source_raw | Master-Quellsheet PET2 extra. |
| `assets/source/pet2_chibi_reference_sheet.png` | pet2_chibi | contact_sheet | copy_to_source_raw | Referenz-/Übersichtssheet PET2, als Raw-Referenz (`not_approved_raw_reference`). |
| `tmp/pet2_source_reviews/ChatGPT Image Jun 21, 2026, 12_01_12 AM_indexed.png` | pet2_chibi | contact_sheet | copy_to_source_raw | Indexierter Review-Overlay PET2 (Labels/Nummern), nur Raw-Referenz (`not_approved_raw_reference`). |
| `tmp/pet2_source_reviews/ChatGPT Image Jun 21, 2026, 12_05_38 AM_indexed.png` | pet2_chibi | contact_sheet | copy_to_source_raw | Indexierter Review-Overlay PET2 (Labels/Nummern), nur Raw-Referenz (`not_approved_raw_reference`). |
| `tmp/pet2_source_reviews/ChatGPT Image Jun 21, 2026, 12_15_12 AM_indexed.png` | pet2_chibi | contact_sheet | copy_to_source_raw | Indexierter Review-Overlay PET2 (Labels/Nummern), nur Raw-Referenz (`not_approved_raw_reference`). |
| `assets/pets/ruffy/spritesheet.png` | ruffy | runtime_atlas | keep_runtime | Aktiver Runtime-Atlas PET1, von der Runtime geladen. |
| `assets/pets/ruffy/contact_sheet.png` | ruffy | contact_sheet | keep_runtime | QA-Übersicht zum aktuellen Atlas, kein Rohbild. |
| `assets/pets/ruffy/qa/contact_sheet_dark.png` | ruffy | qa_artifact | keep_runtime | QA-Artefakt (dunkler Hintergrund). |
| `assets/pets/ruffy/qa/contact_sheet_magenta.png` | ruffy | qa_artifact | keep_runtime | QA-Artefakt (Magenta-Hintergrund). |
| `assets/pets/ruffy/previews/*.gif` (24 Dateien) | ruffy | preview | keep_runtime | Animations-Previews zum aktuellen Atlas. |
| `assets/pets/ruffy/row_sources/*.png` (96 Dateien) | ruffy | unknown | manual_review_needed | Bereits geschnittene Zwischen-Cells, aus Master-Sheets abgeleitet; kein Roh-Sheet, nicht approved. |
| `assets/pets/ruffy/source_cells/*.png` (110 Dateien) | ruffy | unknown | manual_review_needed | Geschnittene Einzelzellen (base/gear2–5), Build-Zwischenstand; nicht approved. |
| `assets/pets/pet2_chibi/spritesheet.png` | pet2_chibi | runtime_atlas | keep_runtime | Aktiver Runtime-Atlas PET2. |
| `assets/pets/pet2_chibi/contact_sheet.png` | pet2_chibi | contact_sheet | keep_runtime | QA-Übersicht zum aktuellen Atlas. |
| `assets/pets/pet2_chibi/review.gif` | pet2_chibi | preview | keep_runtime | Review-GIF zum aktuellen Atlas. |
| `assets/pets/pet2_chibi/qa/contact_sheet_dark.png` | pet2_chibi | qa_artifact | keep_runtime | QA-Artefakt (dunkler Hintergrund). |
| `assets/pets/pet2_chibi/previews/*.gif` (35 Dateien) | pet2_chibi | preview | keep_runtime | Animations-Previews zum aktuellen Atlas. |
| `assets/pets/pet2_chibi/row_sources/*.png` (132 Dateien) | pet2_chibi | unknown | manual_review_needed | Geschnittene Zwischen-Cells (main/support/extra), aus Master-Sheets abgeleitet; nicht approved. |
| `assets/codex/ruffy/spritesheet.png` | ruffy | runtime_atlas | keep_runtime | Codex-Nebenexport aus demselben Atlas. |
| `assets/codex/ruffy/spritesheet.webp` | ruffy | runtime_atlas | keep_runtime | Codex-Nebenexport (WEBP). |

## Kopierte Rohquellen

| Quelle | Ziel | Pet | Grund |
| ------ | ---- | --- | ----- |
| `assets/source/pet1_ruffy_base_source.png` | `assets/source_raw/ruffy/pet1_ruffy_base_source.png` | ruffy | Eindeutiges Ruffy-Master-Sheet. |
| `assets/source/pet1_ruffy_gear2_source.png` | `assets/source_raw/ruffy/pet1_ruffy_gear2_source.png` | ruffy | Eindeutiges Ruffy-Master-Sheet. |
| `assets/source/pet1_ruffy_gear3_source.png` | `assets/source_raw/ruffy/pet1_ruffy_gear3_source.png` | ruffy | Eindeutiges Ruffy-Master-Sheet. |
| `assets/source/pet1_ruffy_gear4_source.png` | `assets/source_raw/ruffy/pet1_ruffy_gear4_source.png` | ruffy | Eindeutiges Ruffy-Master-Sheet. |
| `assets/source/pet1_ruffy_gear5_source.png` | `assets/source_raw/ruffy/pet1_ruffy_gear5_source.png` | ruffy | Eindeutiges Ruffy-Master-Sheet. |
| `assets/source/pet2_chibi_master_main.png` | `assets/source_raw/pet2_chibi/pet2_chibi_master_main.png` | pet2_chibi | Eindeutiges PET2-Master-Sheet. |
| `assets/source/pet2_chibi_master_support.png` | `assets/source_raw/pet2_chibi/pet2_chibi_master_support.png` | pet2_chibi | Eindeutiges PET2-Master-Sheet. |
| `assets/source/pet2_chibi_master_extra.png` | `assets/source_raw/pet2_chibi/pet2_chibi_master_extra.png` | pet2_chibi | Eindeutiges PET2-Master-Sheet. |
| `assets/source/pet2_chibi_reference_sheet.png` | `assets/source_raw/pet2_chibi/pet2_chibi_reference_sheet.png` | pet2_chibi | PET2-Referenz, `not_approved_raw_reference`. |
| `tmp/pet2_source_reviews/ChatGPT Image Jun 21, 2026, 12_01_12 AM_indexed.png` | `assets/source_raw/pet2_chibi/pet2_chibi_source_review_indexed_01.png` | pet2_chibi | PET2-Review-Overlay, `not_approved_raw_reference` (Labels/Nummern). |
| `tmp/pet2_source_reviews/ChatGPT Image Jun 21, 2026, 12_05_38 AM_indexed.png` | `assets/source_raw/pet2_chibi/pet2_chibi_source_review_indexed_02.png` | pet2_chibi | PET2-Review-Overlay, `not_approved_raw_reference` (Labels/Nummern). |
| `tmp/pet2_source_reviews/ChatGPT Image Jun 21, 2026, 12_15_12 AM_indexed.png` | `assets/source_raw/pet2_chibi/pet2_chibi_source_review_indexed_03.png` | pet2_chibi | PET2-Review-Overlay, `not_approved_raw_reference` (Labels/Nummern). |

Hinweis: Alle Quellen bleiben unverändert an ihrem Ursprungsort. Es wurde ausschließlich kopiert.

## Nicht kopiert / ignoriert

| Datei | Grund |
| ----- | ----- |
| `assets/pets/ruffy/spritesheet.png` | Runtime-Atlas, keine Rohquelle. |
| `assets/codex/ruffy/spritesheet.png` / `.webp` | Runtime-/Codex-Atlas, keine Rohquelle. |
| `assets/pets/pet2_chibi/spritesheet.png` | Runtime-Atlas, keine Rohquelle. |
| `assets/pets/ruffy/contact_sheet.png` | QA-Kontaktsheet zum fertigen Atlas, kein Eingangs-Roh-Sheet. |
| `assets/pets/pet2_chibi/contact_sheet.png` | QA-Kontaktsheet zum fertigen Atlas. |
| `assets/pets/ruffy/qa/contact_sheet_dark.png`, `.../contact_sheet_magenta.png` | QA-Artefakte. |
| `assets/pets/pet2_chibi/qa/contact_sheet_dark.png` | QA-Artefakt. |
| `assets/pets/ruffy/previews/*.gif` (24) | Previews zum fertigen Atlas. |
| `assets/pets/pet2_chibi/previews/*.gif` (35), `review.gif` | Previews zum fertigen Atlas. |
| `assets/pets/ruffy/row_sources/*.png` (96), `source_cells/*.png` (110) | Bereits geschnittene Build-Zwischen-Cells, kein Eingangs-Roh-Sheet; siehe Prüfpunkte. |
| `assets/pets/pet2_chibi/row_sources/*.png` (132) | Bereits geschnittene Build-Zwischen-Cells; siehe Prüfpunkte. |

## Manuelle Prüfpunkte

Dateien/Gruppen mit unklarer endgültiger Einordnung:

* `assets/pets/ruffy/row_sources/` (96 PNG) und `assets/pets/ruffy/source_cells/` (110 PNG): geschnittene Einzelzellen aus den Master-Sheets. Sie sind weder Roh-Sheet noch approved. Offen: ob einzelne dieser Zellen nach manueller QA gezielt nach `assets/source_approved/ruffy/<form>/` übernommen werden sollen.
* `assets/pets/pet2_chibi/row_sources/` (132 PNG, main/support/extra): wie oben, geschnittene Zwischenstände PET2. Offen: gezielte Freigabe einzelner Zellen nach QA.
* `tmp/pet2_source_reviews/*_indexed.png` (3 PNG): indexierte Review-Overlays mit Nummern/Labels. Wurden als Raw-Referenz kopiert. Offen: ob die zugehörigen un-indexierten Originale existieren und stattdessen genutzt werden sollen.
* `assets/source/` vs. `assets/source_raw/`: aktuell doppelte Quellhaltung (Original + Kopie). Offen: ob `assets/source/` langfristig zugunsten von `assets/source_raw/` aufgelöst werden soll.

## Pipeline-Status

* `source_raw` befüllt: ja
* `source_approved` befüllt: nein
* Runtime geändert: nein
* Sprites geschnitten: nein
