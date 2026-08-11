# Blue Fox rig notes

The pack follows the version-1 production contract and the shared loader in
`godot/pet_manifest_loader.gd`. Joint positions, pivots, layers, rest transforms,
overlap margins, cursor limits, and action bounds are declared in
`metadata/pet_manifest.json`.

The 2026-08-10 visual revision keeps the bone hierarchy but shortens the arm
segments and adjusts their rest transforms to correct the first failed
proportion review. Eyes retain separate fixed whites and movable pupil/iris
assets. The pupil canvases are 28 x 40 pixels with pivots at `(14, 20)` and
remain bounded by the manifest's `(5, 3)` cursor offset.

The current global contract has no `TailBone`. `tail.svg` is a separate visual
part parented to `TorsoBone` at `z_index=1`, behind both arms and hands. This
prevents the earlier torso-layer overlap without introducing unreviewed tail
animation. Add a shared tail-bone contract only after a reviewed animation
requires it.
