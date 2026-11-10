# Measurements

The evidence behind `rules.md`. Twenty films, each decoded frame by frame at its own frame rate
(12–60 fps; about 22,000 frames in total) with `scripts/mdmeasure.py analyze --sheets`, then aggregated with
`mdmeasure.py aggregate`. The films themselves are not part of this skill and nothing from them was copied into it.

## The set

| # | group | length | fps | what it is (eye) |
| --- | --- | --- | --- | --- |
| 01 | intro | 13 s | 25 | AI model launch sting: macro footage of instruments, one shot per beat, ends on name + mark |
| 02 | intro | 20 s | 25 | AI brand film: arc-shape match-cut montage of textures, one word held over cutting plates |
| 03 | intro | 44 s | 30 | Kitchen brand intro: kinetic sentence over flat colour fields with food footage inserts |
| 04 | intro | 50 s | 30 | Studio showreel: 3D, type and brand work, 3–59-frame shots, bleeding hero type |
| 05 | intro | 46 s | 30 | Product brand intro: 3D spheres and light, strobe section, ends on wordmark |
| 06 | intro | 13 s | 60 | Streaming brand promo: word-by-word sentence, flood to brand green, slot-word swaps |
| 07 | intro | 40 s | 30 | 3D studio reel: dark grounds, product renders, short inserts, name card |
| 08 | intro | 35 s | 25 | Motion designer reel: UI, 3D, type, brand idents |
| 09 | intro | 15 s | 24 | Film company logo sting: one continuous camera push through paper layers |
| 10 | intro | 39 s | 25 | 2D illustration reel: condensed hero type, flat colour fields, character animation |
| 11 | launch | 37 s | 24 | Website builder launch: dark ground, the site builds itself, mark |
| 12 | launch | 47 s | 24 | Website builder feature film: dark/purple, 2–3-word feature cards over UI |
| 13 | launch | 90 s | 24 | Workspace AI agents: light UI at scale, cursor-driven, CTA + mark |
| 14 | launch | 60 s | 24 | Mail app launch: verb title cards alternating with UI, light ground |
| 15 | launch | 82 s | 24 | AI dashboards: a person on a call, UI and an animated map, long holds |
| 16 | launch | 82 s | 24 | AI design tool: prompt → canvas, many cuts on motion, dark-mode flood |
| 17 | launch | 35 s | 24 | Creative app suite: black ground, kinetic type, app montage |
| 18 | launch | 68 s | 12 | Motion tool launch: saturated colour sections, UI, big cursor, 12 fps |
| 19 | launch | 39 s | 30 | Launcher app update: glass UI on a dark abstract ground, 10 s end hold |
| 20 | launch | 33 s | 30 | Video localisation app: one take with camera moves, light ground |

## How the instrument was checked

- **Cuts and transitions**: compared with the transition contact sheets of every film. Two failure modes were
  found and fixed: (1) in-place colour changes (a flood, a dim, dark mode) were read as cuts; a cut now needs the
  layout to change (gradient-magnitude correlation < 0.5; measured cuts ≤ 0.27, floods ≥ 0.56); (2) bursts of
  1-frame "shots" during fast wipes are merged and re-classified. Known limit: a fast wipe between two pictures
  of the same colour (04 at 7.0 s) still reads as two hard cuts, so wipe counts are a lower bound.
- **Motion**: six moves with known GSAP eases were rendered in HyperFrames (expo.out 0.6 s, power2.inOut 0.8 s,
  power3.in 0.4 s, linear 1.0 s, power3.out 0.5 s, sine.inOut 1.2 s) and measured. The first version (97th
  percentile of Farneback flow over the frame) missed small movers and was replaced. The shipped version (DIS
  flow; speed = p90 of flow over changed pixels; a model fit of per-frame displacement over ease × tween length ×
  start) recovers: family 6/6, exact ease 4/6 (power3.in → power2.in, power3.out → power2.out), tween length
  0.6→0.62, 0.8→0.80, 0.4→0.32, 1.0→1.00, 0.5→0.38, 1.2→1.21 s. Speeds above ~30 px/frame at 240 px wide
  (≈ 12% of the frame width per frame) saturate.
- **Text**: OCR line box ÷ font size, calibrated on Arial, Arial Bold and Segoe UI at 28–240 px: 1.04–1.36,
  median ≈ 1.2. Headline holds use only lines of ≤ 8 words at ≥ 5%H with ≤ 12 display words on screen,
  lasting ≥ 0.3 s (215 lines).
- **Beat**: where both trackers ran (16 films), the HyperFrames beat tracker and the built-in tracker agree within
  2.5 BPM on 13; on the other 3 they pick a different metrical level (07: 102 vs 152, 10: 82 vs 162, 11: 104 vs
  157). The HyperFrames value was used. For 01, 02, 09 and 19 HyperFrames found no steady beat and the built-in
  tracker was used.

## Beat analysis (cuts vs music)

| film | BPM | cuts | within ±2 f of a beat (chance) | phase-lock R (chance) | onset z at the cut |
| --- | --- | --- | --- | --- | --- |
| 01 | 120 | 14 | 0.21 (0.34) | 0.49 (0.27) | 1.15 |
| 02 | 112 | 38 | 0.45 (0.30) | 0.27 (0.16) | 0.08 |
| 03 | 91 | 11 | 0.45 (0.20) | 0.08 (0.30) | −0.40 |
| 04 | 110 | 63 | 0.21 (0.25) | 0.07 (0.13) | 1.59 |
| 05 | 121 | 41 | 0.34 (0.27) | 0.12 (0.16) | **3.60** |
| 07 | 102 | 41 | 0.20 (0.23) | 0.07 (0.16) | **4.46** |
| 08 | 105 | 34 | 0.21 (0.28) | 0.15 (0.17) | −0.54 |
| 10 | 82 | 33 | 0.24 (0.22) | 0.09 (0.17) | −1.43 |
| 11 | 104 | 13 | 0.00 (0.30) | 0.04 (0.28) | 0.99 |
| 12 | 105 | 23 | 0.39 (0.30) | 0.20 (0.21) | −0.59 |
| 13 | 121 | 18 | 0.56 (0.34) | 0.18 (0.24) | 1.37 |
| 14 | 142 | 18 | 0.50 (0.40) | 0.38 (0.24) | 1.25 |
| 15 | 172 | 18 | 0.56 (0.49) | 0.06 (0.24) | 0.38 |
| 16 | 105 | 37 | 0.16 (0.29) | 0.08 (0.16) | −1.60 |
| 17 | 120 | 13 | 0.23 (0.33) | 0.30 (0.28) | −0.99 |
| 18 | 126 | 31 | 0.77 (0.71) | 0.17 (0.18) | 2.14 |
| 19 | 133 | 7 | 0.29 (0.31) | 0.74 (0.38) | 1.50 |

"Onset z" = how much stronger the music's onset envelope is within ±1 frame of the hard cuts than at random
times (z ≥ 2: the film cuts on musical hits). A lag sweep of −8…+8 frames found no consistent offset, so this is
not an audio/video sync artefact. 06 and 09 have too few cuts to test. Phase-lock R tests whether all cuts sit at
the same phase of the beat, whatever the tracker's phase error.

## Per-film eye notes

- **01**: every shot is a macro of a measuring instrument and repeats one arc in the same place; shots 12–13 f
  (one beat at 120 BPM); type only at the end, a centred serif at ~7.7%H; name 2.2 s, then mark 2.9 s.
- **02**: the arc sits in the same place in all 28 shots; "There's / more to / discover" are held while
  6–20-frame plates cut beneath; mark 3.8 s.
- **03**: the whole film is one sentence; 2–6 words on screen; each section a new flat ground (cream, green, pink,
  orange); food footage inserted for 0.3–2 s; mark held 3.3 s with a small tagline.
- **04**: hero type that bleeds off the frame (to 67%H); type wrapped around objects; cuts every 3–59 f.
- **05**: 3D light and spheres on black → a white strobe section (1–3-frame pulses) → wordmark on white, 6.5 s.
- **06**: "The best music streaming service in the world." built one word per 0.33–0.5 s, then a flood to the brand
  green, then one word swapped every 0.5–0.67 s, the price, the mark.
- **07**: dark grounds, 3D renders 1–3 s with 3–10-frame inserts; text cards 0.4 s; name card 4.3 s.
- **08**: white/black alternating grounds, logo idents, UI and 3D; shots ~1 s.
- **09**: one continuous push from clouds through concentric paper rings into a city; mark lands at 12.5 s, 2.5 s.
- **10**: a condensed face filling 90% of the width; flat colour fields; 1–1.5 s shots.
- **11**: the website assembles itself (layout boxes, a ~20%H headline); dark ground; mark 4.9 s.
- **12**: dark ground with purple light; 2–3-word cards over real UI; mark 6.8 s.
- **13**: an 8-word, two-line headline at frame 0; UI at scale, cursor-driven; CTA, then mark.
- **14**: the clearest launch structure: 3–4-word verb cards (1.2–2.2 s) alternating with the UI doing it.
- **15**: a person on a video call; dashboards; an animated 3D map; holds up to 17 s while the UI acts.
- **16**: prompt box → generated canvas; many cuts during moves; a dark-mode toggle as a colour flood; mark 4.8 s.
- **17**: black ground, kinetic type, app montage, a 2-word claim held 3.7 s.
- **18**: 12 fps; saturated violet/orange/lime sections; UI at 2×; a large cursor.
- **19**: glass UI on a dark abstract ground; long calm shots; end card held 10 s.
- **20**: one take with camera moves between UI states; light ground; 3-word claim, then mark 4.3 s.

## Aggregate tables

`mdmeasure.py aggregate` output: p10 / median / p90 across films ("ui" = launch). Per-video columns:
`move f med` = median visible frames of a move; `peak fw/s` = median peak speed in frame widths per second;
`font %H` = estimated font size as % of frame height.

| metric | intro p10 / med / p90 | ui p10 / med / p90 | all p10 / med / p90 |
|---|---|---|---|
| sec | 13.225 / **36.9** / 46.83 | 34.83 / **53.665** / 82.422 | 14.837 / **39.4** / 81.508 |
| shots | 2.9 / **29.5** / 41.3 | 8.0 / **16.5** / 31.3 | 7.5 / **19.0** / 34.5 |
| cuts_per_min | 8.86 / **49.85** / 74.19 | 10.77 / **16.2** / 26.55 | 9.58 / **22.45** / 64.28 |
| shot_sec_median | 0.515 / **0.896** / 5.601 | 1.409 / **2.367** / 3.606 | 0.52 / **1.844** / 3.801 |
| shot_sec_mean | 0.795 / **1.177** / 4.569 | 2.182 / **3.453** / 4.918 | 0.877 / **2.546** / 4.918 |
| shot_sec_p10 | 0.145 / **0.416** / 2.847 | 0.041 / **0.619** / 1.855 | 0.065 / **0.416** / 2.217 |
| shot_sec_p90 | 1.003 / **2.198** / 6.211 | 4.447 / **7.304** / 10.964 | 1.329 / **5.223** / 8.99 |
| shot_sec_min | 0.033 / **0.24** / 2.224 | 0.041 / **0.146** / 1.41 | 0.033 / **0.204** / 1.8 |
| hard_cut_share | 0.0 / **0.754** / 0.907 | 0.494 / **0.682** / 0.9 | 0.4 / **0.738** / 0.907 |
| flash_frames | 0.0 / **0.0** / 0.1 | 0.0 / **0.0** / 0.0 | 0.0 / **0.0** / 0.0 |
| moving_frac_median | 0.0 / **0.076** / 0.127 | 0.0 / **0.028** / 0.084 | 0.0 / **0.035** / 0.118 |
| moving_frac_p90 | 0.124 / **0.367** / 0.628 | 0.14 / **0.371** / 0.487 | 0.129 / **0.37** / 0.555 |
| still_time_frac | 0.137 / **0.187** / 0.65 | 0.133 / **0.326** / 0.571 | 0.137 / **0.25** / 0.646 |
| hold_sec_median | 0.415 / **0.513** / 2.23 | 0.446 / **0.552** / 0.912 | 0.415 / **0.552** / 1.945 |
| hold_sec_p90 | 0.795 / **1.902** / 2.395 | 0.897 / **1.271** / 2.866 | 0.803 / **1.596** / 2.538 |
| moves_per_sec | 0.245 / **0.87** / 1.461 | 0.436 / **0.595** / 0.815 | 0.304 / **0.685** / 1.161 |
| move_frames_median | 11.6 / **15.5** / 20.4 | 7.8 / **14.25** / 18.6 | 8.0 / **14.75** / 20.4 |
| move_frames_p10 | 5.0 / **7.4** / 12.14 | 3.54 / **5.1** / 6.0 | 4.23 / **6.0** / 9.38 |
| move_frames_p90 | 22.67 / **32.2** / 101.94 | 23.18 / **41.7** / 85.92 | 22.67 / **38.4** / 96.0 |
| move_sec_median | 0.445 / **0.526** / 0.784 | 0.28 / **0.605** / 0.935 | 0.28 / **0.593** / 0.925 |
| tween_sec_est_median | 0.458 / **0.571** / 0.967 | 0.409 / **0.652** / 1.031 | 0.409 / **0.579** / 1.031 |
| move_peak_fw_s_median | 0.781 / **1.243** / 1.703 | 0.529 / **0.786** / 1.469 | 0.552 / **0.98** / 1.61 |
| move_peak_fw_s_p90 | 2.055 / **3.296** / 4.129 | 1.667 / **2.087** / 3.399 | 1.732 / **2.57** / 4.015 |
| move_peak_pos_median | 0.212 / **0.408** / 0.757 | 0.156 / **0.321** / 0.473 | 0.156 / **0.36** / 0.614 |
| linear_share | 0.0 / **0.192** / 0.322 | 0.105 / **0.146** / 0.219 | 0.072 / **0.151** / 0.296 |
| clean_moves | 1.0 / **10.0** / 21.0 | 7.7 / **18.0** / 30.0 | 3.7 / **11.5** / 26.3 |
| clean_share.out | 0.0 / **0.45** / 0.67 | 0.282 / **0.498** / 0.688 | 0.113 / **0.472** / 0.688 |
| clean_share.inOut | 0.09 / **0.225** / 0.614 | 0.248 / **0.367** / 0.602 | 0.139 / **0.333** / 0.603 |
| clean_share.in | 0.0 / **0.214** / 0.46 | 0.0 / **0.097** / 0.239 | 0.0 / **0.118** / 0.31 |
| clean_share.linear | 0.0 / **0.0** / 0.115 | 0.0 / **0.0** / 0.057 | 0.0 / **0.0** / 0.103 |
| clean_tween_sec_median | 0.188 / **0.396** / 3.11 | 0.29 / **0.44** / 0.699 | 0.244 / **0.421** / 1.043 |
| clean_out_tween_sec_median | 0.207 / **0.35** / 0.413 | 0.242 / **0.393** / 1.062 | 0.226 / **0.373** / 0.665 |
| camera_moves | 0.0 / **0.0** / 1.0 | 0.0 / **0.0** / 2.2 | 0.0 / **0.0** / 1.1 |
| camera_move_sec_median | 0.166 / **0.6** / 2.411 | 0.625 / **1.042** / 2.1 | 0.254 / **0.899** / 2.67 |
| camera_peak_fw_s_median | 0.237 / **1.022** / 3.859 | 0.492 / **1.289** / 2.115 | 0.249 / **1.278** / 3.077 |
| palette_n | 4.9 / **11.5** / 16.2 | 2.9 / **5.0** / 7.7 | 3.0 / **6.5** / 14.2 |
| palette_core_n | 2.0 / **4.0** / 5.0 | 1.0 / **2.0** / 2.6 | 1.0 / **2.0** / 5.0 |
| neutral_share | 0.436 / **0.615** / 0.762 | 0.807 / **0.94** / 0.987 | 0.52 / **0.788** / 0.952 |
| n_backgrounds | 1.9 / **3.5** / 5.1 | 1.0 / **1.5** / 2.5 | 1.0 / **2.0** / 5.1 |
| bg_L_mean | 18.8 / **45.15** / 78.56 | 0.1 / **61.9** / 93.87 | 1.18 / **49.95** / 92.42 |
| text.display_text_time_frac | 0.184 / **0.544** / 0.875 | 0.745 / **0.831** / 0.92 | 0.408 / **0.752** / 0.92 |
| text.display_words_on_screen_median | 1.0 / **2.0** / 4.1 | 2.9 / **5.5** / 8.6 | 1.0 / **3.0** / 7.1 |
| text.display_words_on_screen_p90 | 1.0 / **4.5** / 10.01 | 9.4 / **19.0** / 39.1 | 1.9 / **9.55** / 29.1 |
| text.display_words_on_screen_max | 1.9 / **7.0** / 63.8 | 16.8 / **31.5** / 57.1 | 2.0 / **24.5** / 59.8 |
| text.font_pct_h_median | 6.792 / **7.483** / 11.04 | 4.309 / **5.479** / 8.222 | 4.737 / **6.867** / 11.04 |
| text.font_pct_h_p90 | 7.933 / **14.015** / 21.915 | 9.644 / **10.718** / 17.678 | 7.948 / **12.657** / 19.152 |
| text.font_pct_h_max | 12.11 / **32.021** / 65.357 | 16.774 / **22.145** / 42.237 | 12.62 / **24.075** / 47.905 |
| text.line_w_pct_max | 27.07 / **66.9** / 96.3 | 55.85 / **71.0** / 87.76 | 28.8 / **70.9** / 92.39 |
| text.event_sec_median | 0.465 / **2.08** / 3.804 | 0.649 / **1.083** / 1.517 | 0.498 / **1.333** / 2.751 |
| text.event_sec_p10 | 0.16 / **0.616** / 2.902 | 0.167 / **0.167** / 0.328 | 0.166 / **0.167** / 2.202 |
| text.sec_per_word_median | 0.118 / **0.606** / 2.666 | 0.083 / **0.15** / 0.311 | 0.083 / **0.271** / 1.952 |
| text.sec_per_word_p10 | 0.03 / **0.444** / 1.586 | 0.008 / **0.033** / 0.086 | 0.018 / **0.079** / 0.68 |
| text.words_per_event_median | 1.0 / **2.5** / 4.1 | 2.9 / **5.25** / 17.45 | 1.0 / **3.75** / 9.8 |
| audio.bpm | 89.64 / **107.5** / 121.19 | 105.06 / **120.75** / 145.07 | 90.68 / **115.5** / 133.46 |
| audio.pulse_clarity | 0.081 / **0.342** / 0.61 | 0.152 / **0.367** / 0.454 | 0.081 / **0.367** / 0.607 |
| audio.cuts.within_2f_beat | 0.156 / **0.214** / 0.449 | 0.146 / **0.362** / 0.578 | 0.13 / **0.286** / 0.556 |
| audio.cuts.chance_within_2f_beat | 0.185 / **0.247** / 0.309 | 0.289 / **0.316** / 0.512 | 0.216 / **0.299** / 0.421 |
| audio.cuts.within_2f_halfbeat | 0.364 / **0.5** / 0.616 | 0.454 / **0.593** / 1.0 | 0.44 / **0.556** / 0.911 |
| audio.cuts.chance_within_2f_halfbeat | 0.375 / **0.497** / 0.61 | 0.581 / **0.633** / 0.964 | 0.421 / **0.594** / 0.826 |
| audio.cuts.within_2f_hit | 0.17 / **0.273** / 0.327 | 0.146 / **0.293** / 0.52 | 0.13 / **0.278** / 0.446 |
| audio.cuts.chance_within_2f_hit | 0.146 / **0.208** / 0.27 | 0.2 / **0.245** / 0.315 | 0.16 / **0.231** / 0.293 |
| audio.cuts.median_abs_offset_beat_frames | 2.348 / **3.88** / 5.182 | 1.75 / **2.715** / 3.877 | 1.928 / **3.25** / 4.688 |
| audio.cuts.phase_lock_R | 0.061 / **0.094** / 0.31 | 0.06 / **0.186** / 0.415 | 0.058 / **0.153** / 0.401 |
| audio.cuts.phase_lock_R_chance | 0.15 / **0.171** / 0.383 | 0.178 / **0.236** / 0.338 | 0.156 / **0.236** / 0.342 |
| audio.cuts.within_2f_of_locked_grid | 0.214 / **0.333** / 0.472 | 0.382 / **0.491** / 0.723 | 0.272 / **0.391** / 0.676 |
| audio.cuts.within_2f_of_locked_halfgrid | 0.37 / **0.635** / 0.676 | 0.605 / **0.718** / 1.0 | 0.522 / **0.667** / 0.911 |
| audio.shot_len_beats_median | 0.588 / **1.19** / 5.718 | 2.328 / **3.8** / 7.321 | 0.8 / **2.48** / 7.462 |
| audio.shot_len_integer_beats_share | 0.14 / **0.212** / 0.468 | 0.081 / **0.262** / 0.503 | 0.078 / **0.25** / 0.506 |

## Pooled distributions (p10, p25, p50, p75, p90)

### intro

- **shot_sec**: [0.24, 0.436, 0.8, 1.35, 2.793]
- **move_sec**: [0.167, 0.3, 0.533, 0.96, 1.52]
- **move_frames_at30**: [5.0, 9.0, 16.0, 28.8, 45.6]
- **tween_sec_est**: [0.12, 0.233, 0.546, 1.155, 2.206]
- **move_peak_fw_s**: [0.319, 0.603, 1.458, 2.447, 3.736]
- **move_peak_pos**: [0.0, 0.0, 0.286, 0.708, 1.0]
- **clean_ease_family_share**: {'out': 0.45, 'inOut': 0.312, 'in': 0.211, 'linear': 0.028}
- **clean_ease_share**: {'expo.out': 0.284, 'expo.inOut': 0.202, 'expo.in': 0.083, 'power3.out': 0.055, 'power4.out': 0.046, 'power2.inOut': 0.037, 'power2.out': 0.037, 'power3.in': 0.037, 'power2.in': 0.037, 'power4.in': 0.037}
- **clean_tween_sec_by_family**: {'out': [0.08, 0.163, 0.333, 0.73, 1.896], 'inOut': [0.088, 0.142, 0.241, 0.577, 1.434], 'in': [0.07, 0.14, 0.357, 0.557, 1.32]}
- **clean_peak_fw_s_by_family**: {'out': [0.266, 0.383, 0.945, 2.099, 2.98], 'inOut': [0.287, 0.481, 0.758, 1.406, 2.385], 'in': [0.22, 0.363, 1.323, 2.089, 4.132]}
- **n_clean_moves**: 109
- **camera_sec**: [0.166, 0.265, 0.6, 1.427, 2.411]
- **camera_peak_fw_s**: [0.237, 0.371, 1.022, 2.405, 3.859]
- **ease_family_share**: {'out': 0.43, 'linear': 0.195, 'in': 0.195, 'inOut': 0.18}
- **ease_share**: {'expo.out': 0.202, 'linear': 0.195, 'expo.inOut': 0.099, 'expo.in': 0.096, 'power1.out': 0.085, 'power2.out': 0.051, 'power3.out': 0.051, 'power1.in': 0.048}
- **camera_ease_family_share**: {'in': 0.5, 'out': 0.25, 'linear': 0.25}
- **transition_share**: {'hard-cut': 0.55, 'hard-cut-on-motion': 0.216, 'colour-flood': 0.119, 'morph/in-place': 0.09, 'wipe-vertical': 0.014, 'wipe-horizontal': 0.007, 'dissolve': 0.004}
- **gradual_transition_frames**: [4.4, 8.0, 11.0, 15.0, 28.0]
- **text_event_sec**: [0.167, 0.333, 0.64, 1.167, 2.667]
- **text_event_words**: [1.0, 2.0, 2.5, 5.0, 8.0]
- **text_size_pct_h**: [4.47, 6.33, 9.34, 16.75, 27.3]
- **text_build_sec**: [0.163, 0.48, 1.148]
- **hold_by_words**: {'1-2': {'n': 85, 'p10': 0.167, 'p25': 0.333, 'median': 0.5}, '3-4': {'n': 37, 'p10': 0.16, 'p25': 0.333, 'median': 0.667}, '5-7': {'n': 25, 'p10': 0.167, 'p25': 0.333, 'median': 0.8}, '8+': {'n': 23, 'p10': 0.167, 'p25': 0.327, 'median': 0.667}}
- **still_hold_sec**: [0.28, 0.35, 0.44, 0.633, 1.683]
- **n_shots**: 255
- **n_moves**: 272
- **n_camera**: 4
- **n_text_events**: 170

### ui

- **shot_sec**: [0.208, 1.167, 2.333, 4.042, 7.187]
- **move_sec**: [0.167, 0.25, 0.5, 1.0, 1.635]
- **move_frames_at30**: [5.0, 7.5, 15.0, 30.0, 49.0]
- **tween_sec_est**: [0.163, 0.304, 0.567, 1.15, 1.978]
- **move_peak_fw_s**: [0.139, 0.313, 0.723, 1.481, 2.405]
- **move_peak_pos**: [0.0, 0.0, 0.3, 0.569, 1.0]
- **clean_ease_family_share**: {'out': 0.519, 'inOut': 0.346, 'in': 0.124, 'linear': 0.011}
- **clean_ease_share**: {'expo.out': 0.378, 'expo.inOut': 0.146, 'expo.in': 0.081, 'power4.out': 0.065, 'power3.inOut': 0.065, 'sine.inOut': 0.043, 'power2.inOut': 0.043, 'power1.out': 0.027, 'power3.out': 0.027, 'power1.inOut': 0.027}
- **clean_tween_sec_by_family**: {'out': [0.104, 0.208, 0.413, 0.784, 1.453], 'inOut': [0.089, 0.247, 0.627, 0.871, 1.308], 'in': [0.154, 0.248, 0.379, 0.652, 0.821]}
- **clean_peak_fw_s_by_family**: {'out': [0.13, 0.212, 0.55, 1.069, 1.663], 'inOut': [0.126, 0.215, 0.6, 1.593, 2.149], 'in': [0.223, 0.383, 0.981, 1.611, 2.285]}
- **n_clean_moves**: 185
- **camera_sec**: [0.196, 0.302, 0.792, 2.167, 2.354]
- **camera_peak_fw_s**: [0.268, 0.792, 1.556, 2.149, 3.095]
- **ease_family_share**: {'out': 0.457, 'inOut': 0.234, 'in': 0.162, 'linear': 0.148}
- **ease_share**: {'expo.out': 0.295, 'linear': 0.148, 'expo.inOut': 0.1, 'expo.in': 0.072, 'power1.out': 0.056, 'power1.in': 0.053, 'power4.out': 0.05, 'power3.inOut': 0.039}
- **camera_ease_family_share**: {'out': 0.5, 'inOut': 0.375, 'in': 0.125}
- **transition_share**: {'hard-cut': 0.346, 'hard-cut-on-motion': 0.335, 'morph/in-place': 0.176, 'colour-flood': 0.096, 'camera-push': 0.016, 'dissolve': 0.011, 'camera-pan': 0.011, 'wipe-vertical': 0.005, 'continuous': 0.005}
- **gradual_transition_frames**: [3.4, 5.0, 8.0, 13.0, 17.0]
- **text_event_sec**: [0.167, 0.333, 1.167, 2.167, 3.5]
- **text_event_words**: [2.0, 3.0, 6.0, 16.0, 28.0]
- **text_size_pct_h**: [3.08, 3.7, 5.87, 11.19, 16.83]
- **text_build_sec**: [0.167, 0.667, 2.833]
- **hold_by_words**: {'1-2': {'n': 70, 'p10': 0.167, 'p25': 0.209, 'median': 0.667}, '3-4': {'n': 65, 'p10': 0.167, 'p25': 0.167, 'median': 0.5}, '5-7': {'n': 45, 'p10': 0.167, 'p25': 0.167, 'median': 0.833}, '8+': {'n': 147, 'p10': 0.167, 'p25': 0.333, 'median': 1.833}}
- **still_hold_sec**: [0.292, 0.333, 0.542, 0.833, 1.425]
- **n_shots**: 179
- **n_moves**: 359
- **n_camera**: 8
- **n_text_events**: 327

### all

- **shot_sec**: [0.24, 0.52, 1.147, 2.73, 4.946]
- **move_sec**: [0.167, 0.292, 0.5, 0.967, 1.583]
- **move_frames_at30**: [5.0, 8.8, 15.0, 29.0, 47.5]
- **tween_sec_est**: [0.137, 0.271, 0.562, 1.152, 2.12]
- **move_peak_fw_s**: [0.189, 0.41, 0.968, 1.957, 3.089]
- **move_peak_pos**: [0.0, 0.0, 0.3, 0.653, 1.0]
- **clean_ease_family_share**: {'out': 0.493, 'inOut': 0.333, 'in': 0.156, 'linear': 0.017}
- **clean_ease_share**: {'expo.out': 0.344, 'expo.inOut': 0.167, 'expo.in': 0.082, 'power4.out': 0.058, 'power3.inOut': 0.048, 'power2.inOut': 0.041, 'sine.inOut': 0.037, 'power3.out': 0.037, 'power2.out': 0.027, 'power1.out': 0.027}
- **clean_tween_sec_by_family**: {'out': [0.104, 0.188, 0.396, 0.775, 1.481], 'inOut': [0.083, 0.17, 0.464, 0.835, 1.392], 'in': [0.082, 0.213, 0.372, 0.618, 1.091]}
- **clean_peak_fw_s_by_family**: {'out': [0.137, 0.288, 0.602, 1.316, 2.369], 'inOut': [0.14, 0.288, 0.714, 1.553, 2.192], 'in': [0.212, 0.36, 1.224, 1.752, 2.652]}
- **n_clean_moves**: 294
- **camera_sec**: [0.171, 0.292, 0.774, 2.167, 2.479]
- **camera_peak_fw_s**: [0.219, 0.407, 1.465, 2.149, 3.539]
- **ease_family_share**: {'out': 0.445, 'inOut': 0.211, 'in': 0.176, 'linear': 0.168}
- **ease_share**: {'expo.out': 0.255, 'linear': 0.168, 'expo.inOut': 0.1, 'expo.in': 0.082, 'power1.out': 0.068, 'power1.in': 0.051, 'power4.out': 0.046, 'power2.out': 0.04}
- **camera_ease_family_share**: {'out': 0.417, 'in': 0.25, 'inOut': 0.25, 'linear': 0.083}
- **transition_share**: {'hard-cut': 0.468, 'hard-cut-on-motion': 0.264, 'morph/in-place': 0.124, 'colour-flood': 0.109, 'wipe-vertical': 0.011, 'dissolve': 0.006, 'camera-push': 0.006, 'wipe-horizontal': 0.004, 'camera-pan': 0.004, 'continuous': 0.002}
- **gradual_transition_frames**: [4.0, 6.0, 10.0, 14.0, 20.4]
- **text_event_sec**: [0.167, 0.333, 0.833, 2.0, 3.167]
- **text_event_words**: [1.0, 2.0, 4.0, 10.0, 25.0]
- **text_size_pct_h**: [3.24, 4.33, 6.94, 12.97, 20.37]
- **text_build_sec**: [0.167, 0.5, 2.333]
- **hold_by_words**: {'1-2': {'n': 155, 'p10': 0.167, 'p25': 0.327, 'median': 0.64}, '3-4': {'n': 102, 'p10': 0.167, 'p25': 0.167, 'median': 0.667}, '5-7': {'n': 70, 'p10': 0.167, 'p25': 0.209, 'median': 0.833}, '8+': {'n': 170, 'p10': 0.167, 'p25': 0.333, 'median': 1.667}}
- **still_hold_sec**: [0.28, 0.333, 0.5, 0.792, 1.54]
- **n_shots**: 434
- **n_moves**: 631
- **n_camera**: 12
- **n_text_events**: 497


## Per video

| video | sec | fps | shots | shot med s | cuts/min | hard% | moving | still | move f med | peak fw/s | top ease | palette | bg L | disp words med | font %H med/max | text s med | bpm | cut<=2f beat (chance) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intro-01 | 13.28 | 25.0 | 15 | 0.52 | 63.3 | 0.929 | 0.102 | 0.178 | 12.0 | 1.187 | linear | 11 | 19.4 | 1.0 | 7.717/35.492 | 2.24 | 120.2 | 0.214 (0.341) |
| intro-02 | 20.0 | 25.0 | 29 | 0.52 | 84.0 | 0.684 | 0.0 | 0.686 | 13.0 | 0.8 | linear | 18 | 26.3 | 1.0 | 8.646/16.508 | 1.92 | 112.3 | 0.447 (0.301) |
| intro-03 | 43.9 | 30.0 | 11 | 2.9 | 13.7 | 0.727 | 0.01 | 0.292 | 16.0 | 0.914 | expo.inOut | 12 | 79.1 | 3.0 | 6.792/22.225 | 2.667 | 90.5 | 0.455 (0.198) |
| intro-04 | 50.07 | 30.0 | 62 | 0.667 | 73.1 | 0.905 | 0.101 | 0.11 | 15.0 | 1.535 | expo.out | 14 | 58.7 | 2.0 | 10.188/67.442 | 0.5 | 110.2 | 0.206 (0.247) |
| intro-05 | 46.47 | 30.0 | 31 | 0.467 | 38.7 | 0.512 | 0.052 | 0.21 | 20.0 | 2.612 | linear | 10 | 38.4 | 1.0 | 6.942/7.1 | 6.5 | 121.0 | 0.341 (0.268) |
| intro-06 | 12.73 | 59.94 | 3 | 5.389 | 9.4 | 0.0 | 0.0 | 0.646 | 8.0 | 1.427 | expo.inOut | 4 | 13.4 | 5.0 | 11.108/39.2 | 3.504 | 122.9 | 0.0 (0.131) |
| intro-07 | 40.0 | 30.0 | 39 | 0.833 | 57.0 | 0.78 | 0.213 | 0.14 | 15.0 | 1.214 | expo.out | 9 | 33.0 | 2.0 | 6.792/28.55 | 0.333 | 101.8 | 0.195 (0.225) |
| intro-08 | 35.0 | 25.0 | 33 | 0.96 | 54.9 | 0.853 | 0.118 | 0.174 | 19.0 | 1.602 | linear | 12 | 51.9 | 3.0 | 7.1/45.992 | 0.48 | 104.8 | 0.206 (0.284) |
| intro-09 | 15.01 | 23.976 | 2 | 7.508 | 4.0 | 0.0 | 0.1 | 0.172 | 24.0 | 0.607 | power4.in | 5 | 56.4 | 4.0 | 11.033/12.667 | 2.502 | 90.7 | None (None) |
| intro-10 | 38.8 | 25.0 | 30 | 1.1 | 44.8 | 0.818 | 0.028 | 0.196 | 18.0 | 1.272 | linear | 16 | 78.5 | 2.0 | 7.25/65.125 | 0.96 | 81.9 | 0.242 (0.22) |
| launch-01 | 37.46 | 24.0 | 10 | 3.604 | 14.4 | 0.615 | 0.048 | 0.305 | 17.0 | 0.733 | expo.out | 6 | 0.1 | 5.0 | 6.713/20.367 | 1.0 | 103.8 | 0.0 (0.3) |
| launch-02 | 47.29 | 24.0 | 23 | 1.417 | 27.9 | 0.522 | 0.024 | 0.347 | 15.0 | 0.826 | expo.out | 7 | 1.3 | 6.0 | 6.325/23.458 | 0.667 | 105.2 | 0.391 (0.299) |
| launch-03 | 90.0 | 24.0 | 19 | 3.625 | 12.0 | 0.889 | 0.0 | 0.562 | 6.0 | 0.372 | expo.out | 3 | 89.1 | 14.0 | 4.942/41.975 | 1.667 | 121.2 | 0.556 (0.335) |
| launch-04 | 60.04 | 24.0 | 19 | 2.167 | 18.0 | 1.0 | 0.0 | 0.464 | 8.0 | 0.553 | expo.out | 3 | 92.3 | 8.0 | 5.4/20.833 | 1.5 | 142.1 | 0.5 (0.404) |
| launch-05 | 81.58 | 24.0 | 14 | 3.292 | 9.6 | 0.5 | 0.008 | 0.385 | 14.0 | 0.801 | expo.out | 6 | 93.5 | 6.0 | 4.325/12.192 | 0.666 | 171.8 | 0.556 (0.49) |
| launch-06 | 81.5 | 24.0 | 34 | 1.77 | 24.3 | 0.541 | 0.038 | 0.252 | 14.5 | 1.047 | expo.out | 5 | 75.8 | 7.0 | 4.783/17.283 | 1.167 | 105.2 | 0.162 (0.29) |
| launch-07 | 35.03 | 23.976 | 13 | 1.335 | 20.6 | 0.846 | 0.032 | 0.248 | 14.5 | 1.68 | expo.out | 2 | 0.1 | 2.0 | 14.2/44.6 | 0.5 | 120.3 | 0.231 (0.327) |
| launch-08 | 68.08 | 12.0 | 31 | 1.917 | 26.4 | 0.75 | 0.12 | 0.047 | 11.0 | 0.771 | expo.out | 14 | 48.0 | 4.0 | 5.558/24.692 | 1.5 | 126.1 | 0.774 (0.709) |
| launch-09 | 38.53 | 30.0 | 8 | 3.484 | 10.9 | 0.857 | 0.0 | 0.648 | 8.5 | 0.546 | linear | 5 | 1.4 | 3.0 | 4.167/25.308 | 0.833 | 132.5 | 0.286 (0.305) |
| launch-10 | 33.03 | 30.0 | 8 | 2.567 | 12.7 | 0.444 | 0.08 | 0.143 | 33.0 | 1.446 | expo.inOut | 5 | 97.2 | 3.0 | 7.558/19.908 | 1.5 | 118.7 | 0.333 (0.282) |