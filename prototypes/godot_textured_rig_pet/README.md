# Godot textured rig pet prototype

## Validierter sichtbarer Windows-Test

Der sichtbare Test war erfolgreich. Der Produktionspack lädt 30 Manifest-Parts;
kein Asset fehlte. Die Figur blieb vollstaendig sichtbar, die getrennten
Pupillen folgten dem Cursor innerhalb ihrer Begrenzung, und die Kopfneigung
blieb klein. Das Fenster folgte dem Cursor nicht.

`wave` lief vollstaendig und ohne abgeschnittene Koerperteile. Zehn schnelle
Leertastendruecke starteten genau eine Wave; nach ausreichender Ruhe startete
eine bewusst neue Eingabe wieder genau eine Wave. Es blieb keine Zwischenpose
eingefroren. Transparenz, Rahmenlosigkeit, Always-on-top, Click-through,
Dragging und `Esc` funktionierten ebenfalls.

Der Prototyp bleibt bewusst ein Machbarkeitsnachweis: Sein eingebauter
Democharakter verwendet keine echten PET-Produktionsassets. Er kann inzwischen
aber einen externen Produktionspack wie den noch nicht freigegebenen
`pet001_blue_fox` über den gemeinsamen Manifest-Loader darstellen. Er migriert
die Python-Runtime nicht, besitzt kein Kontextmenue und noch kein
Walk-/Chase-Verhalten.

This isolated Godot 4.7 prototype demonstrates a `Skeleton2D` character built
from replaceable external SVG body parts. It contains no Ruffy, PET2, or other
existing PET assets and does not modify the Python runtime.

## Production-pack preview

Der gemeinsame Loader akzeptiert den Produktionsmanifestpfad über
`--pet-manifest`. Im Idle bleibt der normale rechte Arm sichtbar; während
`wave` werden die drei separaten `wave_right_*`-Parts eingeblendet und danach
wieder ausgeblendet.

## Project layout

- `assets/parts/` contains the 21 transparent SVG body-part files, including
  separate left/right pupil assets.
- `assets/rig_manifest.json` is the central asset contract. Every part declares
  its asset path, parent bone, local placement, pivot, layer, visibility, and
  idle/wave action-bounds contribution.
- `main.tscn` contains the stable `Skeleton2D`/`Bone2D` hierarchy and the
  `AnimationPlayer` tracks.
- `desktop_pet_textured_rig.gd` reads the manifest, decodes each external SVG
  source directly into a runtime texture, creates the `Sprite2D` children,
  applies action bounds, and owns desktop interaction. Generated Godot SVG
  import sidecars are therefore not runtime prerequisites.

## Pivots and layers

Each sprite is created with `centered = false` and positioned as
`local_position - pivot`. The pivot therefore stays at the bone joint while the
SVG extends several pixels above it: shoulders, elbows, wrists, hips, knees,
and ankles overlap instead of opening visible gaps.

The manifest gives hair-back the lowest head layer, places legs behind torso,
then arms/hands, torso, head/face/eyes/mouth, and finally hair-front. All
graphics have transparent SVG backgrounds.

## Stable action canvas

The static transparent canvas is 720×720. `PetRoot` is read from the manifest
at `(360, 670)`, making it the lower-middle ground anchor. The visible feet end
near `y=688`; the canvas is never resized during animation.

The manifest defines conservative full-sprite action envelopes:

- `idle_bounds`: `(195,145)` to `(525,705)`.
- `wave_bounds`: `(195,110)` to `(690,705)`.

The script installs `idle_bounds` at startup, switches to `wave_bounds` before
wave starts, and restores idle bounds when the action finishes. Desktop clicks
outside the active envelope pass through to the application below.

## Controls and behavior

- Left mouse button on the active figure envelope drags the entire window.
- `Space` starts the non-looping `wave` once. Repeated presses while it runs are
  ignored. On `animation_finished`, the script returns to `idle_breath`.
- `Esc` exits.
- `look_at_cursor` keeps the eye whites fixed and moves only the separate
  left/right pupil sprites by at most `(5,3)` pixels in their elliptical eye
  area. Head tilt remains clamped to ±0.07 radians; the desktop window never
  follows the cursor and the reaction pauses while dragging.
- Every non-echo `Space` keydown updates the last-request time. The first one
  starts Wave and locks the burst; later keydowns are discarded, never queued.
  After Wave ends, Idle starts immediately, while the burst lock is released
  only after 600 ms have passed since the most recent discarded/accepted press.

## Manual launch

Open `project.godot` in Godot and run with `F6` or `F5`, or use:

```powershell
& 'C:\Tools\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64.exe' --path 'C:\Users\Bujupi\Desktop\PETs\prototypes\godot_textured_rig_pet'
```

To preview a production pack through the same validated shell, pass its
manifest after Godot's `--` user-argument separator:

```powershell
& 'C:\Tools\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64.exe' --path 'C:\Users\Bujupi\Desktop\PETs\prototypes\godot_textured_rig_pet' -- --pet-manifest='C:\Users\Bujupi\Desktop\PETs\assets\pets\pet001_blue_fox\metadata\pet_manifest.json'
```

The preview compiles and calls the shared `godot/pet_manifest_loader.gd`; the
pet pack itself contains no runtime script.

`pet001_blue_fox` is currently a `draft`. Its 2026-08-10 reference/style update
uses the user-supplied image for overall contrast and the preserved alternate
reference for the preferred rounded full-glove hands. Loading it successfully
does not imply visual approval.

Visual desktop behavior must be confirmed manually on Windows; headless mode
cannot validate compositor transparency or always-on-top behavior.
