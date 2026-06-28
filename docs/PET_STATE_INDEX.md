# PET State Index

Dieses Dokument listet die Zielstates für alle Pets.

## PET1 — Ruffy

Status: in Arbeit

### Normal

| State          | Zweck                | Status           |
| -------------- | -------------------- | ---------------- |
| idle           | Standardstand        | approved_source  |
| smile          | freundlicher Idle    | approved_source  |
| wave           | User-Begrüßung       | approved_source  |
| surprised      | Reaktion             | approved_source  |
| thinking       | Denkpose             | approved_source  |
| shy            | verlegen             | approved_source  |
| idle_serious   | ernster Stand        | approved_source  |
| sit            | sitzend              | needs_fix_source |
| sleepy         | müde                 | approved_source  |
| run_a          | Lauf-Frame           | approved_source  |
| run_b          | Lauf-Frame           | pending          |
| jump           | Sprung               | approved_source  |
| land           | Landung              | pending          |
| crouch         | Hocke / Vorbereitung | needs_fix_source |
| point          | zeigt auf Element    | approved_source  |
| celebrate      | Jubel                | approved_source  |
| thumbs_up      | Zustimmung           | approved_source  |
| rest           | Pause                | needs_fix_source |
| sit_wave       | sitzend winken       | needs_fix_source |
| confused       | verwirrt / shrug     | needs_fix_source |
| inspect_ground | untersucht Desktop   | needs_fix_source |
| drag_react     | Reaktion beim Ziehen | pending          |
| window_hang    | hängt an Kante       | pending          |

### Gear2

| State               | Zweck                    | Status                   | Notes |
| ------------------- | ------------------------ | ------------------------ | ----- |
| gear2_idle          | Steam-Stand              | approved_source          | covered by `ruffy_gear2_idle_crouch_01.png` |
| gear2_crouch        | Startpose                | needs_replacement_source | desired/target state; no approved PNG in source_approved/ruffy/gear2 |
| gear2_dash          | schneller Dash           | approved_source          | covered by `ruffy_gear2_dash_fast_01.png`, `ruffy_gear2_dash_low_01.png` |
| gear2_run           | schneller Lauf           | rejected_source          | |
| gear2_jump          | Sprung/Kick              | needs_replacement_source | desired/target state; no approved PNG in source_approved/ruffy/gear2 |
| gear2_punch         | schneller Punch          | approved_source          | covered by `ruffy_gear2_punch_prep_01.png` |
| gear2_recovery      | Nachwirkung              | needs_replacement_source | desired/target state; no approved PNG in source_approved/ruffy/gear2 |
| gear2_steam_powerup | Aktivierung              | needs_replacement_source | desired/target state; no approved PNG in source_approved/ruffy/gear2 |
| gear2_idle_crouch   | geduckter Steam-Stand    | approved_source          | `ruffy_gear2_idle_crouch_01.png` |
| gear2_powerup_crouch | Powerup-Hocke           | approved_source          | `ruffy_gear2_powerup_crouch_01.png` |
| gear2_powerup_fists | Powerup-Fäuste           | approved_source          | `ruffy_gear2_powerup_fists_01.png` |
| gear2_dash_low      | tiefer Dash              | approved_source          | `ruffy_gear2_dash_low_01.png` |
| gear2_land          | Landung                  | rejected_source          | |
| gear2_ground_crouch | Boden-Hocke              | rejected_source          | |
| gear2_kick          | Kick                     | rejected_source          | |
| gear2_low_charge    | tiefe Ladepose           | rejected_source          | |
| gear2_punch_prep    | Punch-Vorbereitung       | approved_source          | `ruffy_gear2_punch_prep_01.png` |
| gear2_guard_fists   | Guard mit Fäusten        | approved_source          | `ruffy_gear2_guard_fists_01.png` |
| gear2_dash_fast     | schneller Dash           | approved_source          | `ruffy_gear2_dash_fast_01.png` |
| gear2_smile         | Lächeln mit Steam        | rejected_source          | |
| gear2_shout_powerup | Powerup-Ruf              | rejected_source          | |
| gear2_laugh_powerup | Powerup-Lachen           | rejected_source          | |
| gear2_deep_crouch   | tiefe Hocke              | approved_source          | `ruffy_gear2_deep_crouch_01.png` |
| gear2_thumbs_up     | Daumen hoch              | rejected_source          | |
| gear2_battle_ready  | kampfbereit              | approved_source          | `ruffy_gear2_battle_ready_01.png` |

### Gear3

| State                  | Zweck                | Status                   | Notes |
| ---------------------- | -------------------- | ------------------------ | ----- |
| gear3_thumb_bite       | beißt in Daumen/Hand | approved_source          | `ruffy_gear3_thumb_bite_01.png` |
| gear3_air_inflate      | bläst Luft ein       | approved_source          | `ruffy_gear3_air_inflate_01.png` |
| gear3_fist_inflate     | Faust wächst         | needs_replacement_source | |
| gear3_giant_fist_ready | große Faust bereit   | approved_source          | `ruffy_gear3_giant_fist_ready_01.png` |
| gear3_giant_punch      | großer Schlag        | approved_source          | `ruffy_gear3_giant_punch_01.png` |
| gear3_giant_stomp      | großer Fußtritt      | needs_replacement_source | |
| gear3_guard            | große Hand blockt    | needs_replacement_source | |
| gear3_tired_recovery   | Nachteil/Recoil      | approved_source          | `ruffy_gear3_tired_recovery_01.png` |
| gear3_victory          | Siegerpose           | needs_replacement_source | |

Alias (nicht separater approved State): `gear3_air_inhale` → `alias_of: gear3_air_inflate`
(historischer target_state-Name im v2-Review-CSV).

### Gear4

| State             | Zweck               | Status  |
| ----------------- | ------------------- | ------- |
| gear4_idle        | kräftige Gear4-Form | approved_source  |
| gear4_guard       | Verteidigung        | approved_source  |
| gear4_dash        | Rush                | approved_source  |
| gear4_punch       | Punch               | approved_source  |
| gear4_heavy_punch | schwerer Punch      | approved_source  |
| gear4_powerup     | Powerup             | approved_source  |
| gear4_shout       | Ruf / Schrei        | needs_replacement_source |
| gear4_jump        | Sprung              | approved_source  |
| gear4_landing     | Landung             | needs_replacement_source |
| gear4_tired_recovery | Recoil / müde    | approved_source  |

### Gear5

| State                 | Zweck                   | Status  |
| --------------------- | ----------------------- | ------- |
| gear5_idle            | Gear5-Stand             | needs_new_source |
| gear5_shout           | Ruf / Schrei            | needs_new_source |
| gear5_point           | Zeigen                  | needs_new_source |
| gear5_crouch          | Hocke                   | needs_new_source |
| gear5_jump            | Sprung                  | needs_new_source |
| gear5_air_jump        | Sprung in der Luft      | needs_new_source |
| gear5_run             | verspielter Lauf        | needs_new_source |
| gear5_spin            | Wirbel/Spin             | needs_new_source |
| gear5_jump_impact     | Sprung-Landung/Impact   | needs_new_source |
| gear5_leap_impact     | Sprung-Impact           | needs_new_source |
| gear5_silly_face      | Grimasse                | needs_new_source |
| gear5_sit_calm        | Sitzen ruhig            | needs_new_source |
| gear5_laugh           | Lachen                  | needs_new_source |
| gear5_wave            | Winken                  | needs_new_source |
| gear5_cartoon_stretch | cartoonige Dehnung      | needs_new_source |
| gear5_ground_bounce   | Boden/Gummi-Interaktion | needs_new_source |
| gear5_sit_laugh       | Sitzen/Lachen           | needs_new_source |
| gear5_victory         | Jubel                   | needs_new_source |

## PET2 — Chibi Girl

Status: vorbereitet

### Core

| State     | Zweck         | Status  |
| --------- | ------------- | ------- |
| idle      | Standardstand | pending |
| smile     | freundlich    | pending |
| wave      | Begrüßung     | pending |
| wink      | Zwinkern      | pending |
| happy     | Freude        | pending |
| shy       | verlegen      | pending |
| thinking  | Denken        | pending |
| surprised | Reaktion      | pending |
| sit       | Sitzen        | pending |
| rest      | Pause         | pending |

### Gaming

| State            | Zweck                 | Status  |
| ---------------- | --------------------- | ------- |
| controller       | spielt mit Controller | pending |
| focused_gaming   | Fokus                 | pending |
| headset_adjust   | Headset richten       | pending |
| clutch_celebrate | Sieg/Jubel            | pending |
| queue_wait       | Warteschlange         | pending |
| tactical_think   | taktisch denken       | pending |

### Social

| State         | Zweck             | Status  |
| ------------- | ----------------- | ------- |
| phone         | Handy             | pending |
| chat          | Chat/Discord-Vibe | pending |
| laptop        | Laptop            | pending |
| heart         | Herz/Reaktion     | pending |
| celebrate     | Jubel             | pending |
| sparkle_happy | sehr happy        | pending |

### Desktop Interaction

| State         | Zweck                        | Status  |
| ------------- | ---------------------------- | ------- |
| drag_react    | Reaktion beim Ziehen         | pending |
| cursor_follow | folgt Cursor                 | pending |
| sit_on_edge   | sitzt auf Fensterkante       | pending |
| window_peek   | schaut hinter Fenster hervor | pending |
| folder_play   | spielt mit Ordner            | pending |
| hang_edge     | hängt an Kante               | pending |
