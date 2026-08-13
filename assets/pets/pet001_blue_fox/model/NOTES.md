# Blue Fox 3D model — asset spec / TODO

Status: planning only, no modeling started. Written on
`feature/blue-fox-3d-production-poc` at HEAD `355df72`
("Document 3D Blue Fox rig and asset strategy"), after two Godot-primitive
blockout iterations were rejected on visual grounds (see that branch's
history). This document is the checklist for the actual Blender session,
not a record of work already done.

## 1. Goal

- [ ] Build one manual Blender/GLB model of the same Blue Fox character —
      not a new character.
- The 2D frontmaster (`assets/pets/pet001_blue_fox/source/master_figure_reference.png`)
  stays the visual reference for identity and silhouette.
- The Godot 3D PoC (`prototypes/godot_3d_pet_poc/`) stays the runtime
  reference — rotation, framing, toon shading, transparent shell are already
  proven there and are not being re-decided here.
- Godot primitives (capsules/spheres/boxes) are rejected as the production
  modeling method. This file exists because of that rejection.

## 2. Target structure

```
assets/pets/pet001_blue_fox/model/
├── blend/pet001_blue_fox_v1.blend
├── export/pet001_blue_fox_v1.glb
├── preview/front.png
├── preview/side_right.png
├── preview/back.png
├── preview/skeleton_overlay.png
└── NOTES.md
```

- [ ] `blend/` and `export/` and `preview/` created only when the actual
      modeling session starts — not part of this commit.

## 3. Model scope V1

Allowed:
- [ ] Head
- [ ] Ears
- [ ] Muzzle / cheeks
- [ ] Torso / hoodie
- [ ] Arms
- [ ] Simplified open hands / implied fingerless gloves
- [ ] Shorts
- [ ] Legs
- [ ] Shoes
- [ ] Tail with light-colored tip

Not V1 (explicitly out of scope, do not add):
- [ ] No face rig
- [ ] No cursor-look pupils
- [ ] No detailed fingers
- [ ] No cloth simulation
- [ ] No animation set beyond what's needed to sanity-check the rig
- [ ] No auxiliary/helper bones

## 4. Proportion rules

- [ ] Chibi, but not head-only — body/hoodie must stay clearly visible and
      readable, not overwhelmed by the head (this is exactly what failed in
      both Godot iterations).
- [ ] Big head, but torso/hoodie volume clearly present.
- [ ] Arms/legs short, but still readable as limbs, not stubs.
- [ ] Shorts and shoes visibly separate from each other and from the legs.
- [ ] Tail visible, but not larger than or competing with the body focus.
- [ ] Reference is the 2D master image, not the numeric values from the
      rejected Godot-primitive iterations. Those numbers are historical
      context only, not a target to hit.

## 5. Rigging contract V1

Exactly these 15 bones, no additions:

```
TorsoBone
HeadBone
TailBone
LeftUpperArmBone
LeftLowerArmBone
LeftHandBone
RightUpperArmBone
RightLowerArmBone
RightHandBone
LeftUpperLegBone
LeftLowerLegBone
LeftFootBone
RightUpperLegBone
RightLowerLegBone
RightFootBone
```

Rules:
- [ ] Blender bone names must exactly match the Godot bone names above (no
      translation table).
- [ ] Same parent hierarchy as the existing PoC/manifest contract
      (`TorsoBone` root; `HeadBone` and `TailBone` and both arm/leg chains
      parented to `TorsoBone`; each limb chain Upper → Lower → Hand/Foot).
- [ ] No Aux bones.
- [ ] No helper bones of any kind.
- [ ] Exported skeleton must contain exactly 15 bones — verify count before
      export.
- [ ] Target pose: A-pose (not T-pose).
- [ ] Simple, clean skin weights — mostly rigid per-bone assignment, no
      complex multi-bone blending needed for V1.

## 6. Material / look rules

- [ ] Flat material colors or vertex colors are sufficient for V1 — no
      texture painting required.
- [ ] Fur: strong/saturated blue.
- [ ] Muzzle/cheeks and tail tip: cream.
- [ ] Inner ears: cream/skin-toned (not orange — corrected after checking
      the reference image; the older README text saying "orange inner ears"
      is wrong).
- [ ] Eyes: teal/cyan.
- [ ] Hoodie: royal blue, with a darker navy hood/collar portion.
- [ ] Shorts: dark/navy.
- [ ] Shoes: clearly separate from legs/shorts, distinct color block.
- [ ] Gloves: dark, fingerless implied (no separate finger geometry needed).

## 7. Blender working order

- [ ] Set up reference-image plane(s) (front view minimum; side view if
      available).
- [ ] Block silhouette, check against front reference before adding detail.
- [ ] Head / ears / muzzle first.
- [ ] Hoodie / torso.
- [ ] Arms / hands.
- [ ] Shorts / legs / shoes.
- [ ] Tail last.
- [ ] Rig only after silhouette is approved.
- [ ] Capture preview screenshots (front, side_right, back, skeleton
      overlay).
- [ ] Export GLB last, after preview screenshots are approved.

## 8. Acceptance criteria before Godot import

- [ ] Front view reads clearly as the Blue Fox without explanation.
- [ ] Hoodie, shorts, hands, shoes, tail each individually identifiable.
- [ ] 3/4, side, and back views stay plausible (no silhouette collapse).
- [ ] Skeleton contains exactly the 15 required bones, correctly named and
      parented.
- [ ] A simple test bone rotation in Blender does not tear the mesh at
      shoulder/hip/neck joints.
- [ ] No strong identity drift from the 2D master.

## 9. Open topics for later (explicitly not V1)

- Face rig
- Cursor-look / pupil tracking
- Detailed finger geometry
- Secondary ear/tail motion
- Toon shader match-up once real geometry (not primitives) is in Godot —
  normal distribution will differ from the PoC's primitive meshes, needs a
  fresh visual check, not assumed to look the same
