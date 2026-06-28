# PET1 Ruffy Approved Inventory — 2026-06-28

## Summary

* Normal: 13 PNG (+ `.gitkeep`)
* Gear2: 9 PNG (+ `.gitkeep`)
* Gear3: 5 PNG (+ `.gitkeep`)
* Gear4: 16 PNG (+ `.gitkeep`)
* Gear5: 0 PNG (`.gitkeep` only)
* Total approved PNG: **43**

## Approved Files

### Normal

`.gitkeep`: yes

* `ruffy_normal_celebrate_01.png`
* `ruffy_normal_idle_01.png`
* `ruffy_normal_idle_serious_01.png`
* `ruffy_normal_jump_01.png`
* `ruffy_normal_point_01.png`
* `ruffy_normal_run_a_01.png`
* `ruffy_normal_shy_01.png`
* `ruffy_normal_sleepy_01.png`
* `ruffy_normal_smile_01.png`
* `ruffy_normal_surprised_01.png`
* `ruffy_normal_thinking_01.png`
* `ruffy_normal_thumbs_up_01.png`
* `ruffy_normal_wave_01.png`

### Gear2

`.gitkeep`: yes

* `ruffy_gear2_battle_ready_01.png`
* `ruffy_gear2_dash_fast_01.png`
* `ruffy_gear2_dash_low_01.png`
* `ruffy_gear2_deep_crouch_01.png`
* `ruffy_gear2_guard_fists_01.png`
* `ruffy_gear2_idle_crouch_01.png`
* `ruffy_gear2_powerup_crouch_01.png`
* `ruffy_gear2_powerup_fists_01.png`
* `ruffy_gear2_punch_prep_01.png`

### Gear3

`.gitkeep`: yes

* `ruffy_gear3_air_inflate_01.png`
* `ruffy_gear3_giant_fist_ready_01.png`
* `ruffy_gear3_giant_punch_01.png`
* `ruffy_gear3_thumb_bite_01.png`
* `ruffy_gear3_tired_recovery_01.png`

### Gear4

`.gitkeep`: yes

* `ruffy_gear4_arms_out_01.png`
* `ruffy_gear4_crouch_01.png`
* `ruffy_gear4_crouch_ready_01.png`
* `ruffy_gear4_dash_01.png`
* `ruffy_gear4_fly_01.png`
* `ruffy_gear4_fly_02.png`
* `ruffy_gear4_guard_01.png`
* `ruffy_gear4_heavy_punch_01.png`
* `ruffy_gear4_idle_01.png`
* `ruffy_gear4_idle_hat_01.png`
* `ruffy_gear4_idle_hat_02.png`
* `ruffy_gear4_jump_01.png`
* `ruffy_gear4_powerup_steam_01.png`
* `ruffy_gear4_punch_01.png`
* `ruffy_gear4_standby_01.png`
* `ruffy_gear4_tired_recovery_01.png`

### Gear5

Erwartung: keine approved PNGs

* (keine PNG-Dateien)
* `.gitkeep`: yes

## Gear5 Status

* accepted: **no**
* status: **needs_new_source** (alle Gear5-States in `docs/PET_STATE_INDEX.md`)
* source_approved empty except `.gitkeep`: **yes**
* rejected backup folder: `assets/review/rejected/ruffy_gear5_removed_after_failed_approved_review/`
* rejected backup count: **12**

Backup-Dateien:

* `ruffy_gear5_air_jump_01.png`
* `ruffy_gear5_crouch_01.png`
* `ruffy_gear5_idle_01.png`
* `ruffy_gear5_jump_01.png`
* `ruffy_gear5_jump_impact_01.png`
* `ruffy_gear5_leap_impact_01.png`
* `ruffy_gear5_point_01.png`
* `ruffy_gear5_run_01.png`
* `ruffy_gear5_shout_01.png`
* `ruffy_gear5_silly_face_01.png`
* `ruffy_gear5_sit_calm_01.png`
* `ruffy_gear5_spin_01.png`

## Review CSV Abgleich

| Form   | Folder PNG | CSV approved | CSV rejected | CSV total |
| ------ | ---------- | ------------ | ------------ | --------- |
| normal | 13         | 13           | 9            | 25        |
| gear2  | 9          | 9            | 16           | 25        |
| gear3  | 5          | 5            | 3            | 8         |
| gear4  | 16         | 16           | 4            | 20        |
| gear5  | 0          | 0            | 20           | 20        |

## Contact Sheets

| Sheet | Status |
| ----- | ------ |
| `assets/review/contact_sheets/ruffy_normal_approved_review_clean.png` | vorhanden |
| `assets/review/contact_sheets/ruffy_gear2_approved_review_clean_v4.png` | vorhanden |
| `assets/review/contact_sheets/ruffy_gear3_approved_review.png` | vorhanden |
| `assets/review/contact_sheets/ruffy_gear4_approved_review_clean_v2.png` | vorhanden |
| `assets/review/contact_sheets/ruffy_gear5_approved_review.png` | **deprecated** — archiviert (siehe unten) |

## Deprecated / Archived Artifacts

| Artifact | Status |
| -------- | ------ |
| `assets/review/archive/contact_sheets/ruffy_gear5_approved_review_DEPRECATED_after_gear5_rejected.png` | archiviert (2026-06-28) |
| `assets/review/contact_sheets/ruffy_gear5_approved_review.DEPRECATED.txt` | Stub am Originalpfad |

## Consistency Check

* manual selection consistent: **yes**
* PET_STATE_INDEX consistent: **yes** (nach Doku-Korrektur 2026-06-28)
* CSVs consistent: **yes**
* approved folders consistent: **yes** (43 PNG, erwartete Counts)

## Problems Found (initial audit)

1. ~~Veraltetes Gear5-Contact-Sheet~~ → **resolved** (archiviert + DEPRECATED-Stub)
2. ~~Gear3 Benennungs-Drift (`air_inhale` vs. `air_inflate`)~~ → **resolved** (`gear3_air_inflate` primär; `gear3_air_inhale` als Alias dokumentiert)
3. ~~PET_STATE_INDEX Gear2 überzogene `approved_source`~~ → **resolved** (`gear2_crouch`, `gear2_jump`, `gear2_recovery`, `gear2_steam_powerup` → `needs_replacement_source`)
4. ~~Historischer Gear3-Abschnitt unklar~~ → **resolved** (HISTORICAL / REJECTED SOURCE Banner)

**Remaining (non-blocking):** `docs/PET_ASSET_PIPELINE.md` listet noch `gear3_air_inhale` — historische Referenz, kein approved-State-Konflikt. Gear3-v2-Review-CSV behält historischen target_state-Namen in Spalte (Audit-Historie).

## Next Recommended Step

Doku-Konsistenz ist bereinigt. **Gear5 Template-Neuaufbau Phase A** starten: 1 Base-Template → visuelle Prüfung → ggf. Aseprite-Korrektur → danach kleine 4er-Pose-Batches.
