# Ruffy Gear5 Source Rejected

## Decision

The current Gear5 source/reextract is rejected as a source set.
No Gear5 candidates are approved.

## Reasons

* systematic cropped body/effect parts
* neighboring sprite fragments
* missing belt/sash details
* missing or inconsistent floating sash elements
* inconsistent vest/outfit parts
* bad feet/toes/knees in multiple candidates
* at least one candidate with missing or illogical arm
* not safe for source_approved

## Known Examples

* `ruffy_gear5_reextract_0004`: missing or illogical left arm
* `ruffy_gear5_reextract_0006`: bad toes/feet
* `ruffy_gear5_reextract_0010`: bad toes and left knee
* multiple candidates: missing sash/belt/floating cloth details
* multiple candidates: neighboring fragments or unsafe crop boundaries

## Deprecated Artifacts

Deprecated artifact: `assets/review/contact_sheets/ruffy_gear5_approved_review.png` was
generated before final Gear5 rejection and must not be used as approved evidence.

The PNG was moved to:

`assets/review/archive/contact_sheets/ruffy_gear5_approved_review_DEPRECATED_after_gear5_rejected.png`

A stub marker remains at the original path:
`assets/review/contact_sheets/ruffy_gear5_approved_review.DEPRECATED.txt`

## Required Next Action

Create a new Gear5 source based on a clean template-first workflow:

1. build one clean Gear5 base template
2. verify anatomy/outfit/sash/hair/aura
3. then generate or draw small controlled pose batches
4. approve only after visual review
