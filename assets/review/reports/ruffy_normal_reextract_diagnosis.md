# Ruffy Normal Re-Extraction Diagnosis

## Raw Source

* path: `assets/source/pet1_ruffy_base_source.png`
* exists: yes
* dimensions: 1254x1254
* mode: RGB
* usable: yes

Background: solid magenta/chroma RGB (~210,20,215). Grid: 5x5.

Visible margin above hats in raw (row 0): yes — raw sheet shows intact hat tops with chroma gap.

## Ursache alter Cutoffs

Bewertung:

* likely_old_slicing_issue: unclear
* raw_source_clipped: yes

Der alte Builder nutzte feste 320x320-Zellen mit TARGET_PADDING=30 und Bottom-Alignment
(`fit_to_cell` in `pet1_ruffy_builder.py`). Das kann Inhalt oben verlieren, obwohl das
Raw-Sheet oben noch Rand hat.

## Neue Re-Extraction

* candidate_count: 25
* candidates_with_cutoff_risk: 6
* candidates_source_already_clipped: 6
* review_sheet: `assets/review/contact_sheets/ruffy_normal_reextract_review.png`

## Entscheidung

Noch keine Approved-Sprites.
Dieses Review-Paket dient nur zur manuellen Auswahl.

Das alte Sheet `assets/archive/deprecated_sprite_sources_20260627/review/ruffy_normal_review.png`
ist nicht approvalfähig (sichtbare Hut-/Kopf-Cutoffs aus altem Slicing).
