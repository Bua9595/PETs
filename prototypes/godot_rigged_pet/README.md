# Godot rigged desktop-pet prototype

This is an isolated Godot 4.7 desktop-shell experiment. It uses only built-in
`Polygon2D`, `Skeleton2D`, `Bone2D`, and `AnimationPlayer` nodes; it contains no
PET assets and makes no change to the Python runtime.

## Controls

- Drag the figure with the left mouse button.
- Press `Space` to start `wave` when no action is active. Further presses during
  the wave are ignored.
- `wave` automatically resumes `idle_breath` after its 2.2-second sequence.
- Press `Esc` to close the prototype.

## Rig layout

`PetRoot` is fixed at `(320, 592)`, the lower-middle ground anchor of the static
640×640 action canvas. `Rig` is positioned at `(-210, -430)` below it, so the
visible soles remain at a stable `y=591` without moving or resizing the window.

`Skeleton2D` contains a `TorsoBone` at the torso pivot. Its child bones are the
head, both upper arms, and both legs. Each upper-arm bone owns its lower-arm bone;
each leg bone owns its foot bone. The individual body parts are drawn as separate
`Polygon2D` children of those bones. Their polygons deliberately overlap slightly
at shoulders, elbows, hips, and ankles, so ordinary bone rotations do not reveal
large joints gaps.

## Animations

- `idle_breath` loops every 2.4 seconds and gently raises the head by at most
  three pixels. The torso and feet remain fixed, and no body part is scaled.
- `wave` runs for 2.2 seconds. It raises the right upper arm, applies several
  small, cubic-interpolated forearm rotations, then returns every tracked bone to
  its resting angle before the script resumes `idle_breath`.

## Desktop behavior

`project.godot` and `desktop_pet_rig.gd` both set a transparent, borderless,
always-on-top window. The script supplies an `idle_passthrough_polygon` during
idle and a larger `wave_passthrough_polygon` while the arm is raised to
`DisplayServer.window_set_mouse_passthrough()`. Mouse events outside the active
action outline should therefore reach the window beneath it.

The script prints the effective transparency, viewport, borderless,
always-on-top, passthrough-point, and animation-list values to Godot's Output
panel. Visual desktop behavior must still be confirmed manually on the target
Windows machine.
