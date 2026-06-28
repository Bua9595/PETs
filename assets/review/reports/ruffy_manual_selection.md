# Ruffy Manual Sprite Selection

## Ziel

Manuelle Freigabe der Ruffy-normal-Re-Extraction (Schritt 6/7).

Nur Kandidaten mit Status `approved` wurden nach `assets/source_approved/ruffy/normal/` kopiert.

Quelle: `assets/review/candidates/ruffy_normal_reextract/`

Stand: bereinigt nach finaler Sichtprüfung (Schritt 7b).

## Entscheidungscodes

* `approved`
* `rejected`
* `needs_fix`
* `duplicate`
* `wrong_form`
* `bad_anatomy`
* `not_full_body`
* `bad_pose`
* `wrong_character`
* `bad_cut`

## Normal — Re-Extraction (2026-06-27)

| candidate_id | decision | target_state | notes |
| ------------ | -------- | ------------ | ----- |
| ruffy_normal_reextract_0001 | approved | idle | in source_approved |
| ruffy_normal_reextract_0002 | approved | smile | in source_approved |
| ruffy_normal_reextract_0003 | approved | thumbs_up | in source_approved |
| ruffy_normal_reextract_0004 | approved | wave | in source_approved |
| ruffy_normal_reextract_0005 | approved | surprised | in source_approved |
| ruffy_normal_reextract_0006 | approved | thinking | in source_approved |
| ruffy_normal_reextract_0007 | approved | shy | in source_approved |
| ruffy_normal_reextract_0008 | approved | idle_serious | in source_approved |
| ruffy_normal_reextract_0009 | rejected | sit | bad_pose_visual_review |
| ruffy_normal_reextract_0010 | approved | sleepy | in source_approved |
| ruffy_normal_reextract_0011 | approved | celebrate | in source_approved |
| ruffy_normal_reextract_0012 | approved | point | in source_approved |
| ruffy_normal_reextract_0013 | rejected | | bad_cut_neighbor_fragment_bottom |
| ruffy_normal_reextract_0014 | approved | run_a | in source_approved |
| ruffy_normal_reextract_0015 | approved | jump | in source_approved |
| ruffy_normal_reextract_0016 | rejected | | bad_cut_neighbor_fragment_bottom |
| ruffy_normal_reextract_0017 | rejected | | bad_cut_neighbor_fragment_bottom |
| ruffy_normal_reextract_0018 | rejected | | bad_cut_neighbor_fragment_bottom |
| ruffy_normal_reextract_0019 | rejected | | bad_cut_neighbor_fragment_bottom |
| ruffy_normal_reextract_0020 | rejected | rest | removed from approved after visual review |
| ruffy_normal_reextract_0021 | needs_fix | sit_wave | removed from approved; minimal cutoff |
| ruffy_normal_reextract_0022 | needs_fix | crouch | removed from approved; minimal cutoff |
| ruffy_normal_reextract_0023 | needs_fix | confused | removed from approved; minimal cutoff |
| ruffy_normal_reextract_0024 | rejected | | top_cutoff_risk_raised_hands |
| ruffy_normal_reextract_0025 | rejected | inspect_ground | removed from approved after visual review |

## Approved-Dateien (bereinigt)

Aktuell in `assets/source_approved/ruffy/normal/` (13):

* `ruffy_normal_idle_01.png`
* `ruffy_normal_smile_01.png`
* `ruffy_normal_thumbs_up_01.png`
* `ruffy_normal_wave_01.png`
* `ruffy_normal_surprised_01.png`
* `ruffy_normal_thinking_01.png`
* `ruffy_normal_shy_01.png`
* `ruffy_normal_idle_serious_01.png`
* `ruffy_normal_sleepy_01.png`
* `ruffy_normal_celebrate_01.png`
* `ruffy_normal_point_01.png`
* `ruffy_normal_run_a_01.png`
* `ruffy_normal_jump_01.png`

Entfernt nach Sichtprüfung (Kopie unter `assets/review/rejected/ruffy_normal_removed_after_visual_review/`):

* `ruffy_normal_rest_01.png`
* `ruffy_normal_sit_wave_01.png`
* `ruffy_normal_crouch_01.png`
* `ruffy_normal_confused_01.png`
* `ruffy_normal_inspect_ground_01.png`
* `ruffy_normal_sit_01.png`

## Gear2 — Re-Extraction (2026-06-27)

Quelle: `assets/review/candidates/ruffy_gear2_reextract/`

| candidate_id | decision | target_state | notes |
| ------------ | -------- | ------------ | ----- |
| ruffy_gear2_reextract_0001 | approved | gear2_idle_crouch | in source_approved |
| ruffy_gear2_reextract_0002 | approved | gear2_powerup_crouch | in source_approved |
| ruffy_gear2_reextract_0003 | approved | gear2_powerup_fists | in source_approved |
| ruffy_gear2_reextract_0004 | approved | gear2_dash_low | in source_approved |
| ruffy_gear2_reextract_0005 | rejected | gear2_run | missing_arm_skin_visual_review |
| ruffy_gear2_reextract_0006 | rejected | | wrong_character_silhouette_visual_review |
| ruffy_gear2_reextract_0007 | rejected | gear2_land | missing_hand_visual_review |
| ruffy_gear2_reextract_0008 | rejected | gear2_ground_crouch | bad_anatomy_visual_review |
| ruffy_gear2_reextract_0009 | rejected | | neighbor_fragment_right_visual_review |
| ruffy_gear2_reextract_0010 | rejected | gear2_kick | missing_arm_skin_visual_review |
| ruffy_gear2_reextract_0011 | rejected | gear2_low_charge | missing_skin_or_clothing_visual_review |
| ruffy_gear2_reextract_0012 | approved | gear2_punch_prep | in source_approved |
| ruffy_gear2_reextract_0013 | rejected | | wrong_form_gear3_like_arm_visual_review |
| ruffy_gear2_reextract_0014 | rejected | | neighbor_fragment_right_visual_review |
| ruffy_gear2_reextract_0015 | approved | gear2_guard_fists | in source_approved |
| ruffy_gear2_reextract_0016 | approved | gear2_dash_fast | in source_approved |
| ruffy_gear2_reextract_0017 | rejected | | bad_pose_visual_review |
| ruffy_gear2_reextract_0018 | rejected | gear2_smile | missing_skin_or_clothing_visual_review |
| ruffy_gear2_reextract_0019 | rejected | gear2_shout_powerup | missing_skin_or_clothing_visual_review |
| ruffy_gear2_reextract_0020 | rejected | gear2_laugh_powerup | missing_skin_or_clothing_visual_review |
| ruffy_gear2_reextract_0021 | approved | gear2_deep_crouch | in source_approved |
| ruffy_gear2_reextract_0022 | rejected | | weak_or_wrong_state_visual_review |
| ruffy_gear2_reextract_0023 | rejected | gear2_thumbs_up | missing_arm_skin_visual_review |
| ruffy_gear2_reextract_0024 | rejected | | neighbor_fragment_right_visual_review |
| ruffy_gear2_reextract_0025 | approved | gear2_battle_ready | in source_approved |

## Approved-Dateien Gear2

Aktuell in `assets/source_approved/ruffy/gear2/` (9):

* `ruffy_gear2_battle_ready_01.png`
* `ruffy_gear2_dash_fast_01.png`
* `ruffy_gear2_dash_low_01.png`
* `ruffy_gear2_deep_crouch_01.png`
* `ruffy_gear2_guard_fists_01.png`
* `ruffy_gear2_idle_crouch_01.png`
* `ruffy_gear2_powerup_crouch_01.png`
* `ruffy_gear2_powerup_fists_01.png`
* `ruffy_gear2_punch_prep_01.png`

Entfernt nach Sichtprüfung (Kopie unter `assets/review/rejected/ruffy_gear2_removed_after_visual_review/`):

* `ruffy_gear2_ground_crouch_01.png`
* `ruffy_gear2_kick_01.png`
* `ruffy_gear2_run_01.png`
* `ruffy_gear2_thumbs_up_01.png`
* `ruffy_gear2_land_01.png`
* `ruffy_gear2_low_charge_01.png`
* `ruffy_gear2_shout_powerup_01.png`
* `ruffy_gear2_smile_01.png`
* `ruffy_gear2_laugh_powerup_01.png`

## Gear3 — Re-Extraction (2026-06-27)

> **HISTORICAL / REJECTED SOURCE — do not use for approved source**
>
> Dieser Abschnitt dokumentiert das verworfene alte 20er-Gear3-Sheet
> (`ruffy_gear3_reextract_0001`–`0020`). **Kein** Eintrag hier ist approved.
> Gear3 approved stammt ausschließlich aus **Gear3 v2** (`ruffy_gear3_reextract_v2_*`).

Quelle: `assets/review/candidates/ruffy_gear3_reextract/`

**Entscheidung: Keine approved.** Das gesamte Gear3-Re-Extract-Paket wurde als
Quelle abgelehnt. Alle Kandidaten `ruffy_gear3_reextract_0001` bis
`ruffy_gear3_reextract_0020` sind **rejected**.

Grund: `gear3_source_sheet_not_approval_safe` — zu viele Anatomie-, Logik-,
Overlap- und Schnittfehler. Ein neues Gear3-Source-Sheet mit größerem Abstand
und strikterem Pose-Design ist nötig.

Bekannte Einzelfehler:

* `ruffy_gear3_reextract_0002`: bad_thumb_bite_logic (Faust vor Mund + zweiter Daumen)
* `ruffy_gear3_reextract_0012`: bad_anatomy_six_fingers
* `ruffy_gear3_reextract_0009`: bad_arm_path_visual_review (unlogische Armführung)

Approved-Ordner `assets/source_approved/ruffy/gear3/`: leer außer `.gitkeep`.

## Gear3 v2 — Re-Extraction (2026-06-28)

Quelle: `assets/source/pet1_ruffy_gear3_source_v2.png`
Kandidaten: `assets/review/candidates/ruffy_gear3_reextract_v2/`

| candidate_id | decision | target_state | notes |
| ------------ | -------- | ------------ | ----- |
| ruffy_gear3_reextract_v2_0001 | approved | gear3_thumb_bite | in source_approved |
| ruffy_gear3_reextract_v2_0002 | approved | gear3_air_inflate | in source_approved → `ruffy_gear3_air_inflate_01.png` (alias: `gear3_air_inhale`) |
| ruffy_gear3_reextract_v2_0003 | approved | gear3_giant_fist_ready | in source_approved |
| ruffy_gear3_reextract_v2_0004 | approved | gear3_giant_punch | in source_approved |
| ruffy_gear3_reextract_v2_0005 | rejected | gear3_guard | bad_anatomy_six_fingers |
| ruffy_gear3_reextract_v2_0006 | rejected | gear3_giant_stomp | missing_sandal_visual_review |
| ruffy_gear3_reextract_v2_0007 | approved | gear3_tired_recovery | in source_approved |
| ruffy_gear3_reextract_v2_0008 | rejected | gear3_victory | bad_fist_visual_review |

## Approved-Dateien Gear3

Aktuell in `assets/source_approved/ruffy/gear3/` (5):

* `ruffy_gear3_thumb_bite_01.png`
* `ruffy_gear3_air_inflate_01.png`
* `ruffy_gear3_giant_fist_ready_01.png`
* `ruffy_gear3_giant_punch_01.png`
* `ruffy_gear3_tired_recovery_01.png`

Offen (`needs_replacement_source`): `gear3_guard`, `gear3_giant_stomp`, `gear3_victory`, `gear3_fist_inflate`

## Gear4 — Re-Extraction (2026-06-28)

Quelle: `assets/source/pet1_ruffy_gear4_source.png`
Kandidaten: `assets/review/candidates/ruffy_gear4_reextract/`

| candidate_id | decision | target_state (vorgeschlagen) | notes |
| ------------ | -------- | ---------------------------- | ----- |
| ruffy_gear4_reextract_0001 | approved | gear4_idle | in source_approved → idle_hat_01 |
| ruffy_gear4_reextract_0002 | approved | gear4_idle | in source_approved → crouch_01 |
| ruffy_gear4_reextract_0003 | approved | gear4_punch | in source_approved |
| ruffy_gear4_reextract_0004 | approved | gear4_idle | in source_approved |
| ruffy_gear4_reextract_0005 | approved | gear4_guard | in source_approved |
| ruffy_gear4_reextract_0006 | rejected | | illogical_gear4_pose_visual_review |
| ruffy_gear4_reextract_0007 | approved | gear4_idle | in source_approved → crouch_ready_01 |
| ruffy_gear4_reextract_0008 | approved | gear4_jump | in source_approved |
| ruffy_gear4_reextract_0009 | approved | gear4_idle | in source_approved → standby_01 |
| ruffy_gear4_reextract_0010 | approved | gear4_dash | in source_approved |
| ruffy_gear4_reextract_0011 | approved | gear4_dash | in source_approved → fly_01 |
| ruffy_gear4_reextract_0012 | approved | gear4_powerup | in source_approved → arms_out_01 |
| ruffy_gear4_reextract_0013 | rejected | gear4_shout | detached_effect_fragments_visual_review |
| ruffy_gear4_reextract_0014 | approved | gear4_heavy_punch | in source_approved |
| ruffy_gear4_reextract_0015 | approved | gear4_dash | in source_approved → fly_02 |
| ruffy_gear4_reextract_0016 | rejected | | bad_anatomy_visual_review |
| ruffy_gear4_reextract_0017 | approved | gear4_tired_recovery | in source_approved |
| ruffy_gear4_reextract_0018 | approved | gear4_idle | in source_approved → idle_hat_02 |
| ruffy_gear4_reextract_0019 | rejected | | bad_fist_visual_review |
| ruffy_gear4_reextract_0020 | approved | gear4_powerup | in source_approved → powerup_steam_01 |

## Approved-Dateien Gear4

Aktuell in `assets/source_approved/ruffy/gear4/` (16):

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

Entfernt nach Sichtprüfung (Kopie unter `assets/review/rejected/ruffy_gear4_removed_after_visual_review/`):

* `ruffy_gear4_shout_01.png`

Offen: `gear4_landing`, `gear4_shout` (`needs_replacement_source`)

## Gear5 — Re-Extraction (2026-06-28)

Quelle: `assets/source/pet1_ruffy_gear5_source.png`
Kandidaten: `assets/review/candidates/ruffy_gear5_reextract/`

**Entscheidung: Keine approved.** Das gesamte Gear5-Re-Extract-Paket wurde als
Quelle abgelehnt. Alle Kandidaten `ruffy_gear5_reextract_0001` bis
`ruffy_gear5_reextract_0020` sind **rejected** (`gear5_source_sheet_not_approval_safe`).

| candidate_id | decision | notes |
| ------------ | -------- | ----- |
| ruffy_gear5_reextract_0001 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0002 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0003 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0004 | rejected | missing_or_illogical_left_arm_visual_review |
| ruffy_gear5_reextract_0005 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0006 | rejected | bad_toes_feet_visual_review |
| ruffy_gear5_reextract_0007 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0008 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0009 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0010 | rejected | bad_toes_and_left_knee_visual_review |
| ruffy_gear5_reextract_0011 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0012 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0013 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0014 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0015 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0016 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0017 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0018 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0019 | rejected | gear5_source_sheet_not_approval_safe |
| ruffy_gear5_reextract_0020 | rejected | gear5_source_sheet_not_approval_safe |

Grund (gesamt):
Cutoffs, Fremdfragmenten, fehlendem Hüftband/fliegendem Band, Outfit-Inkonsistenzen,
Arm-/Fuß-/Zehen-/Knie-Fehlern. Neuer Gear5-Template-Neuaufbau nötig.

Bekannte Einzelfehler:

* `ruffy_gear5_reextract_0004`: missing_or_illogical_left_arm_visual_review
* `ruffy_gear5_reextract_0006`: bad_toes_feet_visual_review
* `ruffy_gear5_reextract_0010`: bad_toes_and_left_knee_visual_review

Zurückgezogene Approved-Sprites (Kopie unter `assets/review/rejected/ruffy_gear5_removed_after_failed_approved_review/`):

* `ruffy_gear5_idle_01.png`
* `ruffy_gear5_shout_01.png`
* `ruffy_gear5_point_01.png`
* `ruffy_gear5_crouch_01.png`
* `ruffy_gear5_jump_01.png`
* `ruffy_gear5_air_jump_01.png`
* `ruffy_gear5_run_01.png`
* `ruffy_gear5_spin_01.png`
* `ruffy_gear5_jump_impact_01.png`
* `ruffy_gear5_leap_impact_01.png`
* `ruffy_gear5_silly_face_01.png`
* `ruffy_gear5_sit_calm_01.png`

Approved-Ordner `assets/source_approved/ruffy/gear5/`: leer außer `.gitkeep`.
