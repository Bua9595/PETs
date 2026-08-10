# Production pet pipeline

This pipeline prepares an original Godot-rigged pet before it is allowed into a
production path. It does not migrate `src/desktop_pet.py`, and it does not turn
the existing Ruffy or PET2 pose assets into rig assets.

## Status flow

`draft` -> `needs_review` -> `approved`

At any review point, use `rejected` instead. Only a completed visual review may
set a pack to `approved`.

## Practical workflow

1. Copy `assets/pets/production_template/` to `assets/pets/<pet_id>/` and set a
   unique `pet_id`, name, version, source reference, and initial `draft` status.
2. Create and record an original, licensed reference figure in `source/`.
3. Split the figure into the 21 named transparent parts in `parts/`; do not put
   a whole character, desktop background, or pose sheet in a single part.
4. Prepare the hidden shoulder, elbow, wrist, hip, knee, ankle, neck, and hair
   overlap areas according to `rig/RIG_PART_CONTRACT.md`.
5. Set every local pivot, parent bone, layer, local position, overlap margin,
   and conservative action-bound contribution in `metadata/pet_manifest.json`.
6. Run the technical validator after all required files exist:

   ```powershell
   python src/production_pet_validator.py assets/pets/<pet_id>/metadata/pet_manifest.json
   ```

7. In a future Godot `Skeleton2D` scene, preload the shared
   `godot/pet_manifest_loader.gd` and call `load_into()` with the manifest, the
   scene skeleton, and `PetRoot`. The helper creates the manifest-declared
   `Sprite2D` children; it is not a new pet client and is not copied per pack.
8. Create and test `idle_breath`, bounded cursor look, and non-looping `wave`.
   Confirm stable feet, no crop, and no joint gaps in the relevant action bounds.
9. Perform the manual checks in `review/REVIEW_CHECKLIST.md`. The validator does
   not evaluate style, anatomy, white fringes, or artistic consistency.
10. Change status to `needs_review`, record the review outcome, and mark the
    pack `approved` only after all technical and visual checks pass.

The template deliberately has no art files, so its initial `draft` manifest is
expected to report missing required parts. It becomes technically valid only
after a real original pet's 21 sources are supplied.
