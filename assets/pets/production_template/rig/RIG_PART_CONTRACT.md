# Production rig-part contract

All source files have transparent backgrounds. The listed reserve is the minimum
transparent extension past the visible outline at a joint; it is not a visible
gap. Pivots use image-local pixels and sit exactly at the named joint. Layer
values are defined by `metadata/pet_manifest.json` and are intentionally data,
not scene magic numbers.

| Part | Transparent reserve / overlap | Pivot and orientation | Layer | Reject when |
| --- | --- | --- | --- | --- |
| hair_back | 12 px behind head and neck | neck pivot; upright | behind head | it leaks beyond head silhouette unexpectedly or has a solid background |
| head | 12 px under hair and neck | neck centre; upright | head base | it is cropped, has an opaque background, or exposes a neck gap |
| face | 8 px inside head edge | same head pivot; upright | over head | facial region does not align with head |
| eye_whites | 6 px inside face | same head pivot; upright | below pupils | whites are cropped, offset, or include pupils |
| left_pupil | 4 px all sides | pupil centre; upright | over eye white | it cannot move within the eye or contains eye-white pixels |
| right_pupil | 4 px all sides | pupil centre; upright | over eye white | it cannot move within the eye or contains eye-white pixels |
| mouth | 4 px all sides | same head pivot; upright | face layer | it does not align with the face |
| hair_front | 10 px over forehead | same head pivot; upright | front-most head layer | it clips face or lacks forehead overlap |
| torso | 14 px at neck, shoulders, hips | torso centre; upright | body base | any attachment opens a visible gap |
| left_upper_arm | 14 px at shoulder/elbow | shoulder pivot; points toward elbow | arm base | shoulder or elbow lacks hidden overlap |
| left_lower_arm | 12 px at elbow/wrist | elbow pivot; points toward wrist | over upper arm | elbow/wrist is cropped or misoriented |
| left_hand | 10 px at wrist | wrist pivot; fingers outward | hand layer | fingers are cropped or wrist opens |
| right_upper_arm | 14 px at shoulder/elbow | shoulder pivot; points toward elbow | arm base | shoulder or elbow lacks hidden overlap |
| right_lower_arm | 12 px at elbow/wrist | elbow pivot; points toward wrist | over upper arm | elbow/wrist is cropped or misoriented |
| right_hand | 10 px at wrist | wrist pivot; fingers outward | hand layer | fingers are cropped or wrist opens |
| left_upper_leg | 14 px at hip/knee | hip pivot; points toward knee | behind torso | hip or knee opens during motion |
| left_lower_leg | 12 px at knee/ankle | knee pivot; points toward ankle | over upper leg | knee/ankle is cropped or misoriented |
| left_foot | 10 px at ankle | ankle pivot; sole rests on ground | foot layer | sole is cropped or ground contact is unstable |
| right_upper_leg | 14 px at hip/knee | hip pivot; points toward knee | behind torso | hip or knee opens during motion |
| right_lower_leg | 12 px at knee/ankle | knee pivot; points toward ankle | over upper leg | knee/ankle is cropped or misoriented |
| right_foot | 10 px at ankle | ankle pivot; sole rests on ground | foot layer | sole is cropped or ground contact is unstable |

Do not bake shadows, desktop background, labels, or unrelated props into a body
part. Review visual quality manually; the validator only checks technical
structure and decodability.
