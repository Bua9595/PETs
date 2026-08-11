# PET Review Workflow

> Scope note (2026-08-12): This document describes the historical pose-sprite
> review path. Manifest-driven Godot production packs use
> `docs/PRODUCTION_PET_PIPELINE.md` plus the pack-local `review/` record. The
> first such pack, `pet001_blue_fox`, is technically validated and remains
> `needs_review` for production approval.

## Ziel

Dieses Dokument beschreibt, wie Sprite-Kandidaten geprüft und später freigegeben werden.

## Grundregel

`assets/source_approved/` bleibt leer, bis ein Sprite visuell freigegeben wurde.

## Review-Artefakte

* Kandidatenliste: `assets/review/reports/candidates.csv`
* Ruffy Review-Sheets: `assets/review/contact_sheets/ruffy_candidates*.png`
* PET2 Review-Sheets: `assets/review/contact_sheets/pet2_chibi_candidates*.png`

Erzeugt/aktualisiert werden diese Artefakte durch:

```bash
python scripts/build_candidate_review.py
```

## Review-Status

Erlaubte Werte:

* `pending`
* `approved`
* `rejected`
* `needs_fix`

## Ablehnungsgründe

Ein Kandidat wird abgelehnt, wenn:

* Körperteile fehlen
* Füße/Hände/Kopf abgeschnitten sind
* falsche Anatomie vorhanden ist
* zusätzliche Arme/Beine vorhanden sind
* Kleidung falsch oder unvollständig ist
* Pose unlogisch ist
* Sprite fast identisch zu einem besseren Kandidaten ist
* Text/Zahlen/Labels im Sprite enthalten sind
* Hintergrund/Ränder schlecht sind
* Charakter nicht konsistent ist

## Ablauf

1. Review-Contact-Sheet öffnen.
2. Candidate-ID visuell prüfen.
3. Entscheidung in `candidates.csv` eintragen:

   * `approved`
   * `rejected`
   * `needs_fix`
4. Erst nach Review werden Approved-Sprites in `assets/source_approved/...` kopiert.
5. Danach baut Codex den finalen Runtime-Atlas.

## Wichtig

Review-Sheets sind keine Runtime-Quelle.
Raw-Sheets sind keine Runtime-Quelle.
Nur `assets/source_approved/` ist finale Quelle.

Alte source_cells oder row_sources mit sichtbaren Cutoffs dürfen nicht erneut als Review-Basis verwendet werden. Neue Kandidaten müssen aus sauberen Raw-Sheets oder neu erzeugten Einzelsprites stammen.
