# PET Asset Pipeline

> Scope note (2026-08-12): The rules below govern the Python pose-sprite/atlas
> pipeline. New manifest-driven Godot rigs follow
> `docs/PRODUCTION_PET_PIPELINE.md`; their external parts and manifest remain
> pack-local under `assets/pets/<pet_id>/`. `pet001_blue_fox` is the first
> technically validated pack on that path and remains `needs_review`.

## Ziel

Diese Pipeline verhindert, dass schlechte Sprite-Sheets direkt in die Runtime gelangen.

## Ordner

### `assets/source_raw/`

Hier liegen Rohbilder aus Bildgeneratoren, Higgsfield, Screenshots oder alten Sheets.

Rohmaterial ist nicht automatisch verwendbar.

### `assets/source_rejected/`

Hier liegen verworfene Bilder oder Sprites.

Gründe:

* abgeschnitten
* falsche Anatomie
* falsche Kleidung
* falscher Charakter
* doppelt
* unlogisch
* Text/Labels
* schlechte Schnittbarkeit

### `assets/source_approved/`

Nur hier liegen freigegebene Sprite-Kandidaten.

Nur diese Dateien dürfen später von Codex oder Build-Skripten für Atlas/Runtime verwendet werden.

## Ablauf für neue Sprites

1. Bild generieren oder erhalten
2. Einzelne Sprites visuell prüfen
3. Schlechte Sprites verwerfen
4. Gute Sprites als Einzeldateien nach `assets/source_approved/...` kopieren
5. Dateinamen mit State versehen
6. Codex schneidet/packt nur Approved-Sprites
7. Contact Sheet und GIFs erzeugen
8. QA prüfen
9. Runtime testen
10. README aktualisieren

## Dateinamen-Konvention

Empfohlen:

`<pet>_<form>_<state>_<index>.png`

Beispiele:

* `ruffy_normal_idle_01.png`
* `ruffy_normal_wave_01.png`
* `ruffy_gear2_dash_01.png`
* `ruffy_gear3_thumb_bite_01.png`
* `ruffy_gear4_guard_01.png`
* `ruffy_gear5_laugh_01.png`
* `pet2_core_idle_01.png`
* `pet2_gaming_controller_01.png`

## Ruffy State-Gruppen

### Normal

* idle
* smile
* wave
* surprised
* thinking
* shy
* sit
* sleepy
* run_a
* run_b
* jump
* land
* crouch
* point
* celebrate
* thumbs_up
* rest
* inspect_ground
* drag_react
* window_hang

### Gear2

* gear2_idle
* gear2_crouch
* gear2_dash
* gear2_run
* gear2_jump
* gear2_punch
* gear2_recovery
* gear2_steam_powerup

### Gear3

* gear3_thumb_bite
* gear3_air_inhale
* gear3_fist_inflate
* gear3_giant_fist_ready
* gear3_giant_punch
* gear3_giant_stomp
* gear3_guard
* gear3_tired_recovery

### Gear4

* gear4_idle
* gear4_guard
* gear4_dash
* gear4_punch
* gear4_heavy_punch
* gear4_powerup
* gear4_jump
* gear4_landing

### Gear5

* gear5_idle
* gear5_laugh
* gear5_wave
* gear5_jump
* gear5_run
* gear5_cartoon_stretch
* gear5_ground_bounce
* gear5_spin
* gear5_sit_laugh
* gear5_victory

## PET2 State-Gruppen

### Core

* idle
* smile
* wave
* wink
* happy
* shy
* thinking
* surprised
* sit
* rest

### Gaming

* controller
* focused_gaming
* headset_adjust
* clutch_celebrate
* queue_wait
* tactical_think

### Social

* phone
* chat
* laptop
* heart
* celebrate
* sparkle_happy

### Desktop Interaction

* drag_react
* cursor_follow
* sit_on_edge
* window_peek
* folder_play
* hang_edge

## QA-Regeln

Ein Sprite ist nur approved, wenn:

* Full-Body sichtbar
* keine falsche Anatomie
* keine falsche Kleidung
* keine Labels/Zahlen/Text
* keine abgeschnittenen Füße/Hände/Köpfe
* keine Doppelcharaktere
* keine unlogischen Props
* klare Pose
* sinnvoller State
* guter Schnittkontrast
* keine Duplikate
