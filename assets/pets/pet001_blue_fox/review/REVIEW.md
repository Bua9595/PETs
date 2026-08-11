# Blue Fox review

Status: `needs_review`

Current design revision: 2026-08-10 at 23:23. The newest user-supplied master
reference now drives proportions, eye spacing, palette, open fingerless hand
silhouette, shoe separation, and tail placement. Earlier references are retained
only as audit history after the full-glove experiment failed visible review.

Completed automated checks for the current production pack:

- all declared production assets exist, load, and match manifest paths
- manifest, bones, pivots, layers, and action bounds are structurally valid
- shared Godot loader parses and starts the pack headlessly
- separate pupil assets remain within the declared cursor-look contract
- the normal idle arm and the separate `wave_right_*` arm switch are loaded
  through the same runtime manifest

The frozen master front view remains unchanged. The current wave-arm stand was
visually reviewed and accepted for this checkpoint; the three wave arm parts
are derived directly from the approved left arm reference.

Local render inspection completed before the new manual review:

- revised indigo/cream face and reduced, separated teal pupil/iris layers render
- royal-blue/cyan hoodie, dark shorts, gloves, shoes, ears, feet, and tail load
- the rig remains assembled through the shared manifest loader

Manual Windows review recorded for this checkpoint:

- final similarity to the supplied design direction without copying an old PET
- eyes read naturally at idle and while following the cursor
- both shortened hands read as open fingerless gloves in idle and wave
- shoes remain visibly separated in the neutral pose
- no clipping or coarse joint gaps across the full wave
- ten rapid Space presses produce exactly one complete wave
- transparency, click-through, dragging, always-on-top, and Esc under direct use

The pack remains `needs_review` for the broader production approval workflow;
this checkpoint does not alter the frozen master or other approved assets.
