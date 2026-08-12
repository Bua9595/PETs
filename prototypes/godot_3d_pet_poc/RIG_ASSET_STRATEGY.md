# 3D Blue Fox — Rig & Asset Strategy

Status: draft, written before any 3D production modeling started.
Scope: bridges `assets/pets/pet001_blue_fox/` (2D frontmaster, status `needs_review`,
v0.2.5) and `prototypes/godot_3d_pet_poc/` (validated 3D PoC, commit `be12b72`).
Neither source has been modified to produce this document.

## 1. Confirmed foundation: bone contract

The 3D PoC's `REQUIRED_BONES` list already matches the 2D manifest's `bones` array
exactly — same 15 bone names, same parent hierarchy:

```
TorsoBone (root)
├── HeadBone
├── TailBone
├── LeftUpperArmBone → LeftLowerArmBone → LeftHandBone
├── RightUpperArmBone → RightLowerArmBone → RightHandBone
├── LeftUpperLegBone → LeftLowerLegBone → LeftFootBone
└── RightUpperLegBone → RightLowerLegBone → RightFootBone
```

Decision: keep this contract as-is. Do not rename or restructure bones for the
3D production rig. This is the one part of the PoC that should carry over
unchanged.

Note: `assets/pets/pet001_blue_fox/rig/RIG_NOTES.md` currently states "no
TailBone in contract" — that is out of date, the manifest already has one.
Worth a small doc fix at some point, not a blocker here.

## 2. Proportions — do not copy the PoC's numbers

The PoC's bone rest offsets are an arbitrary placeholder blockout, not a
proportion target. Comparing segment lengths (2D manifest, scaled by
`rig_scale = 0.48`, vs. the 3D PoC's current meters), normalized against the
Torso→Head offset:

| Segment    | 2D (scaled px) | 2D ratio to Torso→Head | 3D PoC (m) | 3D PoC ratio to Torso→Head |
|------------|----------------|-------------------------|------------|------------------------------|
| Torso→Head | 240.0          | 1.00                     | 1.15       | 1.00                          |
| Upper arm  | 76.7           | 0.32                     | 0.78       | 0.68                          |
| Lower arm  | 58.0           | 0.24                     | 0.66       | 0.57                          |
| Upper leg  | 76.8           | 0.32                     | 0.94       | 0.82                          |
| Lower leg  | 62.4           | 0.26                     | 0.86       | 0.75                          |

The 2D Blue Fox is proportionally compact/chibi-like (short limbs relative to
the head offset). The 3D PoC blockout is closer to a generic adult humanoid.
Applying the 2D ratios directly would roughly halve the PoC's current limb
lengths — but that number is a mechanical projection from bone math, not a
verified visual target.

Decision: do not hard-code the ratio-derived lengths as final. Use them as a
directional starting point, then tune by eye against
`assets/pets/pet001_blue_fox/source/master_figure_reference.png` before
locking any proportion. [Unsicher] whether head-offset is even the right
anchor for a chibi-style character (a big-head design can distort this ratio)
— confirm visually, not just numerically.

## 3. Target palette (from the 2D pack's own description)

`assets/pets/pet001_blue_fox/README.md` describes the current authoritative
direction as: bright layered blue fur, orange inner ears, separated teal
eyes, compact royal-blue hoodie, dark shorts, open fingerless gloves,
separated sneakers, cream-tipped tail (behind the right arm).

The PoC's placeholder palette (`_build_fox_blockout()`) only partially
overlaps this:

| Part           | PoC placeholder       | Target (from README)          | Match? |
|-----------------|------------------------|--------------------------------|--------|
| Body/fur        | orange `d96b32`        | bright layered blue             | No — wrong hue entirely |
| Hoodie          | teal-blue `246b86`     | compact royal-blue hoodie       | Roughly, needs check |
| Eyes            | light teal `a8f3f2`    | separated teal eyes             | Roughly matches |
| Shorts          | dark `25314d`          | dark shorts                     | Matches |
| Ears            | same as fur (no accent)| orange inner ears               | Missing — no distinct color |
| Hands/feet      | plain cream sphere/box | fingerless gloves / sneakers    | Missing — no distinct detail |
| Tail tip        | cream `f6d7a7`         | cream-tipped tail                | Matches |

Decision: fur color is the one hard blocker — it must become blue, not
orange, before any 3D blockout could read as "Blue Fox" rather than "generic
fox." Ear-inner-color and hand/foot detailing are secondary polish, not
blockers for a first production pass.

## 4. Face/detail gap

The 2D master has ~30 manifest parts including separately layered pupils
(for cursor-look), face, mouth, hair front/back. The 3D PoC blockout has 25
primitive mesh parts and represents the whole head with two spheres (eye +
pupil) per side, no separate face/mouth/hair geometry. Cursor-look reuses the
2D rig's pupil-offset approach (`cursor_look.max_pupil_offset`) — the 3D rig
has no equivalent yet.

Decision: out of scope for a first 3D production pass. Track as a follow-up
once base proportions and palette are locked.

## 5. Open questions / risks

- [Unsicher] `rest_position` semantics in the 2D manifest were inferred from
  `godot/pet_manifest_loader.gd` (`bone.position = rest_position` on a
  Bone2D child — i.e. parent-relative), not visually verified in the editor.
- [Offen] The 2D pack itself is still `status: needs_review`, v0.2.5 — the
  "frontmaster" this strategy anchors to is not itself finalized.
- [Offen] No 3D reference exists yet for head/face shape beyond primitive
  spheres.

## 6. Next steps

1. Visually compare a proportion-adjusted 3D blockout against
   `master_figure_reference.png` before locking limb lengths numerically.
2. Swap the placeholder palette for the target palette (blue fur is the
   priority fix).
3. Decide whether ear-inner-color / glove / sneaker detailing goes into the
   first production pass or a later polish pass.
4. Only after 1–3 are decided: start building the actual production 3D
   blockout/mesh work on this branch.
