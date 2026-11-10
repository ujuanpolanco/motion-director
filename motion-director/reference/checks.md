# The check loop

Three checks, from cheapest to most complete. All three use `scripts/mdmeasure.py`, the same instrument
that measured the 20 references, so "pros" in its output means the measured range, not an opinion.

| When | Command | Sees | Cost |
| --- | --- | --- | --- |
| Before building | `MD plan plan.json` | the master prompt's numbers: shot lengths, holds, words, eases, frames, beats | instant |
| Before rendering | `MD stills <png…> --profile P` | each frame: words, type size, safe area, colours, accent, black frames | ~0.5 s a frame |
| Draft render | `MD check draft.mp4 --profile P --out .md/draft` | the motion: cuts, transitions, moves, eases, speed, holds, text timing, palette, beat sync | ~1 s per second of film |

`MD` = `python .claude/skills/motion-director/scripts/mdmeasure.py`. Exit code 1 when anything FAILs.

## What the instrument measures, and how far to trust it

- **Cuts**: HSV-histogram distance between consecutive frames with a local-median spike test; a single
  inserted frame that returns to the previous picture counts as a flash, not two cuts. Reliable for hard cuts.
- **Gradual transitions**: twin-comparison over the histogram distance, then classified: fade through
  black/white (luminance), dissolve (each frame is a blend of the two ends), wipe (the "already new" region is
  a straight-edged band), camera push/pan (one global motion explains the flow), else morph/in-place.
  The class is a best guess; look at the transition sheet (`*_trans*.jpg`) before believing it.
- **Moves**: DIS optical flow at 240 px wide on every frame. The speed signal is the 90th percentile of flow over
  the pixels that changed, so a small mover counts as much as a large one. A move is a run above 0.8 px/frame at
  240 px, extended while above 0.4 px. Its ease, tween length and start are fitted together against every GSAP
  ease (a model of per-frame displacement, saturation included). Calibrated on rendered moves with known eases:
  family 6/6, exact ease 4/6 (the other two one power step off), tween length ±20%. Only "clean" fits
  (rmse < 0.15) count for ease shares; overlapping movers and footage fit nothing well and are left out.
  Speeds above ~30 px/frame at 240 px (12% of the frame width per frame) are underestimated.
- **Holds**: frames where nothing exceeds 0.4 px/frame and under 0.4% of pixels change.
- **Text**: OCR (RapidOCR, PP-OCRv4) at ~6 Hz on a 960 px frame. Font size = line box ÷ 1.2 (calibrated on
  Arial and Segoe at 28–240 px: ratio 1.04–1.36). "Display" text is font ≥ 2.5% of frame height.
  Only tokens with letters count as words (dial numbers in footage do not). Text durations are ±1 sample
  (±0.17 s). Very stylised, rotated or letter-spaced type may not be read: look at the frame.
  A line with few descenders (all caps, "Ember & Oak") reads 20–30% smaller than its font size; judge such a
  headline by the px you set, and use the measured size for mixed-case lines.
- **Colour**: k-means in Lab per shot (3 frames), merged at ΔE < 15, weighted by shot length.
  Background = the cluster that owns the frame border. Accent = chroma > 35 and < 25% of the frame.
- **Beat**: `npx hyperframes beats` when it finds a steady beat, else the built-in onset/DP tracker.
  Because trackers can be off by a constant phase, cuts are also tested for phase locking (do all cuts sit at
  the same phase of the beat, whatever that phase is?).

## Reading a FAIL and fixing it

| Finding | Fix in the master prompt / HTML |
| --- | --- |
| text-hold FAIL | lengthen the shot to the hold, or cut words; never shrink the type |
| words on screen > max | split the line across two beats, or cut words |
| headline font below the floor | raise it to the profile's headline size; quiet lines may be smaller but not below the floor |
| text outside the safe box | move it in: display text keeps 5% from every edge (90% box), unless it is hero type meant to bleed |
| more colours than the profile allows | merge greys, remove the decorative colour, keep one accent |
| accent covers too much | the accent goes on one word, one mark or the payoff; the rest goes neutral |
| shot median too short / long | retime on the grid: move cuts to the next or previous beat |
| hard-cut share too high (launch) | replace seams between worlds with a cause: a morph, a push through an object, a wipe carried by an element |
| linear moves | give every non-constant move its role's ease (enter = out, camera = inOut, exit/zoom-through = in) |
| move frames too long / short | set the tween to the role's frame range |
| moving fraction too low (dead frames) | add the continuous layer: the UI working, a slow camera drift, footage playing |
| too static (still_time_frac high) | pros are fully still 33% (launch) / 19% (intro) of the time in stretches of 0.3–1.5 s; let the UI act, move the camera, or cut sooner |
| no cut near the beat | snap each cut to the nearest beat frame from `MD grid`; never add rounded beats |
| frame is black / frame 0 empty | start on a picture; frame 0 is the thumbnail |

**Short films** (under ~15 s): the end card is a third of the film, so `still_time_frac` runs high and
`cuts_per_min` low. That is expected; keep the WARN with that reason, or keep something moving behind the mark
(footage, a slow travel) as the measured 13 s sting did.

After a fix, re-run only the check that covers it. Three rounds at most; then report what is left and why.

## Contact sheets

`--out` (check) and `--sheets` (analyze) write three sheets next to the JSON:
`*_shots*.jpg` (the middle of every shot, with its length), `*_time*.jpg` (every 0.5 s) and
`*_trans*.jpg` (six frames across every transition). Look at them: the instrument cannot tell a good picture
from a bad one, a crop from a composition, or a logo from a label.
