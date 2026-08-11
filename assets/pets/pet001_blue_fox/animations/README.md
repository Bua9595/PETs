# Blue Fox animation contract

The shared textured-rig preview supplies the current animation tracks:

- `idle_breath`: calm looping head and arm motion with a stable foot baseline
- `wave`: non-looping right-arm action protected by the 600 ms burst lock
- `look_at_cursor`: bounded pupil movement plus slight scripted head tilt

The revised SVG design keeps the same rest pose, bones, and static action canvas.
The pack manifest owns the rest transforms and action bounds; no pet-specific
runtime script or duplicated loader is included in this pack.

Any new animation must be reviewed for joint overlap, action bounds, stable feet,
and uninterrupted return to `idle_breath` before the pack can leave `draft`.
