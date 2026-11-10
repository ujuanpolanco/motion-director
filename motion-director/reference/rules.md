# Measured rules

Every number here was measured frame by frame, at each film's own frame rate, on 20 professional films with
`scripts/mdmeasure.py`: 10 **launch films** (product and feature launches from well-known software companies, 33–90 s) and 10 **intros** (brand intros, a logo sting and studio motion reels, 13–50 s).
Ranges are p10–p90 across films; "median" is the median film unless it says "pooled" (all shots or moves
together). Frame counts are given at 30 fps; at another rate, scale by fps/30. How each number was taken,
and how far to trust it, is in `checks.md`. The per-film data is in `measurements.md`.

A rule says what the pros do. Where a person's own reference contradicts it, measure their reference and
follow it.

## 0. Pick the profile

| | launch | intro |
| --- | --- | --- |
| Purpose | explain a product, show it working | leave a feeling, land a name |
| Length | 33–90 s (median 54) | 13–50 s (median 37) |
| Median shot | 2.4 s (films 1.4–3.6) | 0.9 s (films 0.5–1.6; one-take films excepted) |
| Cuts per minute | 16 (11–27) | 50 (9–74) |
| Display text on screen | 83% of the time | 54% of the time |
| Words on screen (median) | 5.5 (with UI); headlines ≤ 8 | 2 (p90 4.5) |
| Ground | 94% neutral; one or two grounds | 62% neutral; 3–4 grounds per film |
| Colours ≥ 1% of the film | 5 (3–8) | 11.5 (5–16) |
| Fraction of frame moving (median) | 2.8% | 7.6% |
| Frames where nothing moves | 33% | 19% |
| End card (claim/CTA + mark) | 4.9–13.9 s (median 8.1) | 1.8–9.8 s; the mark alone 1.8–6.5 s (median 2.7) |

Use **launch** for anything the viewer must read and understand (a product, a feature, a how-to);
**intro** for a brand intro, sting, title sequence, reel or a mood piece. A hybrid (a brand film with one
product beat) takes intro rhythm and launch reading times for its readable lines.

## 1. Structure

- **Open on a picture.** 15 of 20 films show a picture on frame 0; the other 5 come up from black within
  1.0–1.8 s. 9 of 10 launch films have readable words by 1.4 s (median 0.6 s).
- **Launch beat shares** (the measured films follow HyperFrames' launch shape): one headline promise in the first
  2 s, the product working for ~70% of the running time, a one-line claim, then the end card.
  The verb-card pattern (14, 12, 16): a 2–4 word title card (1.2–2.2 s) alternating with the product
  doing exactly that (2–7 s).
- **Intro beat shares**: a fast build (shots 0.4–1.4 s) for 70–85% of the running time, then 1–3 longer
  shots that resolve into the mark.
- **End card**: the mark alone, centred, on a plain ground, 5–15% of the frame width. The mark by itself holds
  **2.4–6.5 s** (median 3.3 s; measured where OCR reads it). A launch film puts a claim or call to action
  (a URL or "Get started …", 3–6 words, held 1.3–4.3 s, median 2.5 s) right before or with it, so its last shot
  runs **4.9–13.9 s** (median 8.1). Plan: launch end card ≥ 4 s in total, the mark alone ≥ 2.5 s; intro mark ≥ 2.5 s.

## 2. Cutting

| | launch | intro |
| --- | --- | --- |
| Pooled shot length p10 / p25 / p50 / p75 / p90 | 0.21 / 1.17 / 2.33 / 4.04 / 7.2 s | 0.24 / 0.44 / 0.80 / 1.35 / 2.8 s |
| Shortest deliberate shot | 0.4 s (12 f) | 3 frames (0.1 s) |
| Longest single framing | 7–17 s, only while the UI performs | 3.5 s, unless the camera keeps travelling (one-take films: 13–15 s) |
| Hard-cut share of seams | 68% (49–90%) | 75% (50–91%) |
| … of which cut **during** a move | 49% | 28% |
| Colour floods (same layout, new colours) | 10% | 12% |
| Morph / in-place transforms | 18% | 9% |
| Wipes | 0.5% | 2% |
| Dissolves / crossfades | 1.1% | 0.4% |
| Kinds of transition per film | 4 (3–6) | 4 (2–5) |
| Length of a gradual transition | 8 frames (5–13) | 11 frames (8–15) |

Rules:
- **Cut hard, and cut on motion.** About 7 seams in 10 are hard cuts. In launch films half of them happen while
  something is moving (the move continues across the cut, or the next shot starts mid-move).
- **Never crossfade.** Dissolves are 1% of transitions. Change worlds with a cut, a colour flood (8–12 frames,
  inOut) or an object that becomes the next frame.
- **Vary the length.** In every film the p90 shot is at least 2.4× the p10 shot (median 5.8×); equal shot
  lengths read as a slideshow.
- **Intros**: when the montage runs on shape, every shot repeats one shape in the same place in the frame
  (an arc, a circle, a horizon), so the cut reads as one continuous object (seen in 01 and 02).

## 3. Text

### Holds (how long a line stays on screen)

Measured on headline lines only (≤ 8 words, font ≥ 5% of the frame height, little other text on screen):

| Words | launch median (p25) | intro median (p25) |
| --- | --- | --- |
| 1 | 1.25 s (0.92) | 0.65 s (0.48) |
| 2 | 0.83 s (0.63) | 0.67 s (0.50) |
| 3–4 | 1.50 s (1.17) | 0.83 s (0.58) |
| 5–8 | 1.83 s (1.17) | 1.50 s (0.73) |

- **launch**: hold ≥ **0.45 + 0.13 × words** s (floor, the pros' p25); aim for **0.5 + 0.25 × words** s (median).
- **intro**: hold ≥ **0.4 + 0.06 × words** s; aim for **0.45 + 0.15 × words** s. Intros can be this short
  because the line builds word by word and is read while it builds.
- **The last line before the mark**: ≥ 2 s (claims and CTAs measured 1.3–4.3 s, median 2.5 s; 8 of 9 ≥ 1.76 s).
- A line that builds: words arrive **0.06–0.12 s apart** (2–4 frames; a line revealed) or **0.5 s apart**
  (a sentence spoken in type, 06 and 03). One word swapping on a fixed line: every **0.5–0.67 s** (06).

### Amount

- launch: a headline is **≤ 8 words**, one or two lines; the median title card has 3–4 words ("It drafts your
  emails"). Product UI around it may carry more words: they are not meant to be read one by one.
- intro: **2 words** on screen at the median, **≤ 7** at once (p90 4.5).
- Type that persists while the pictures cut beneath it is a pattern of its own (02: "discover" held 3.5 s
  across 10 cuts of 6–20 frames).

### Size (estimated CSS font size as % of frame height; 1% = 10.8 px at 1080)

| | launch | intro |
| --- | --- | --- |
| Headline (each film's p90) | **10.7%** (9.6–17.7) = 116 px | **14%** (7.9–21.9) = 151 px |
| Title lines, pooled p10–p90 | 6.3–21.8% | 6.3–31.4% |
| Hero word (each film's max) | 22% (17–42) | 32% (12–65) |
| Widest line | 71% of frame width (56–88) | 67% (27–96) |
| Product UI text | 2.3% median (p10 1.5%) = 16–25 px, i.e. UI at ~1.5–2× | — |

- Nothing readable is under **1.5% (16 px)**; UI labels sit at 1.5–3%, copy to read at ≥ 6%.
- Display text stays inside the **90% action-safe box** (85% of all measured display text does). The exceptions
  are deliberate: hero type that bleeds off the frame and UI cropped by the camera.

## 4. Motion

Measured with optical flow on every frame; eases fitted against GSAP curves (calibrated: the family is right on
6/6 test moves, the exact ease on 4/6 and one power step off on the other 2, tween length ±20%).
Only "clean" moves (one ease fits with rmse < 0.15: 294 of 631) count for ease shares.

| | launch | intro |
| --- | --- | --- |
| Moves per second | 0.59 (0.44–0.82) | 0.87 (0.24–1.46) |
| Ease family: out / inOut / in / linear | **52 / 35 / 12 / 1 %** | **45 / 31 / 21 / 3 %** |
| Most used eases | expo.out 38%, expo.inOut 15%, expo.in 8%, power4.out 7%, power3.inOut 7% | expo.out 28%, expo.inOut 20%, expo.in 8%, power3.out 6%, power4.out 5% |
| ease-out tween, p25 / median / p75 | 0.21 / **0.41** / 0.78 s = 6 / **12** / 24 f | 0.16 / **0.33** / 0.73 s = 5 / **10** / 22 f |
| ease-inOut tween | 0.25 / **0.63** / 0.87 s = 7 / **19** / 26 f | 0.14 / **0.24** / 0.58 s = 4 / **7** / 17 f |
| ease-in tween | 0.25 / **0.38** / 0.65 s = 7 / **11** / 20 f | 0.14 / **0.36** / 0.56 s = 4 / **11** / 17 f |
| Peak speed, median move | 0.55 fw/s (out), 0.98 (in) | 0.95 fw/s (out), 1.32 (in) |
| Peak speed, fastest tenth | 2.1 fw/s | 3.3 fw/s |
| Peak position within a move | 32% of the way through | 41% |

(fw/s = frame widths per second: 1 fw/s crosses the frame in one second.)

Rules:
- **Expo is the house curve.** expo.out for anything that arrives, expo.inOut for anything that travels
  (camera, carried objects, morphs), expo.in for anything that leaves or is zoomed through.
  power3/power4 are the softer alternates. Linear is 1–3%: only for constant motion that is the point
  (a ticker, a rotation, a progress bar).
- **Arrivals decelerate long**: the speed peaks in the first third of the move.
- **Exits are faster than arrivals**: ease-in moves peak at ~2× the speed of ease-out moves.
- **Durations (30 fps)**: arrival **12 f** (6–24); travel/camera **19 f** launch, **7 f** intro;
  exit **11 f**. Intros run everything ~20% shorter and ~70% faster.
- **Few moves at once.** The median frame has 2.8% (launch) / 7.6% (intro) of its pixels moving; even the
  busiest tenth of frames moves only 37%. One hero move; the rest holds.
- **Hold still between moves.** Launch films are fully still 33% of the time, intros 19%. Still stretches last
  0.3–1.5 s (median 0.5 s) before the next move.
- **Camera moves** (the whole frame moves coherently) are rare: 12 across all 20 films, 0.3–2.2 s each (median
  0.8 s), peaking at 1.3 fw/s. The one-take films (09, 20) are the exception: their camera travels the whole film.

## 5. Colour

| | launch | intro |
| --- | --- | --- |
| Colours covering ≥ 1% of the film | **5** (3–8) | **11.5** (5–16) |
| … covering ≥ 5% | **2** (1–3) | **4** (2–5) |
| Share of the film in neutrals (chroma < 12) | **94%** (81–99) | **62%** (44–76) |
| Saturated accents (chroma > 35, < 25% of frame) | **0** (0–2) | **2.5** (0–4) |
| Area covered by accents | ≤ 7% | 7% (≤ 18%) |
| Distinct grounds per film | 1.5 (1–2.5) | 3.5 (2–5) |
| Ground lightness | light (L ≥ 85) in 5/10, near-black (L ≤ 5) in 4/10 | mid; light and dark alternate |

Rules:
- **launch**: one neutral ground (off-white #f5f2ed–#f8f7f6 or near-black #000000–#0a0a10) and its ink; at most
  one accent, on ≤ 7% of the frame (a button, one word, the mark). The colour comes from the product UI itself.
- **intro**: a palette of ~4 core colours; each shot may own a different flat ground (03, 10: cream, green, pink,
  orange), and a colour flood between grounds is a transition (8–15 frames).

## 6. Rhythm and sound

- Music under every film; tempo **121 BPM** launch (105–145), **108 BPM** intro (90–121).
- **Frame-accurate beat cutting is not what most pros do.** Across the 17 films with music and cuts,
  cuts sit a median 3.2 frames from the nearest beat, and land within ±2 frames of a beat about as often as
  chance (29% vs 30%). Only the two high-energy reels (05, 07) put cuts on musical onsets beyond chance
  (z = 3.6, 4.5), and 01 paces its montage at exactly one shot per beat (12–13 frames at 120 BPM).
- So: **lay the story on the beat grid** (shot lengths in beats, sections on bar lines), and
  - **intro / reel cut to music** (`cut_to_music: true`): every cut within **±1 frame** of a beat or half beat;
    shot lengths of 1–2 beats in the build;
  - **launch**: cuts follow the action (a click, a landing, a move); put only section changes and the end card
    on bar lines.

## 7. Patterns the eye caught (not in the numbers)

- **Shape match cuts** (01, 02): every shot of a montage repeats one shape in the same place: arcs, dials,
  horizons. The cut reads as the same object changing material.
- **Type over cutting plates** (02): one word holds while 6–20-frame shots cut beneath it.
- **Kinetic sentence** (03, 06): a single sentence carries the whole intro, word by word across colour fields.
- **Slot word** (06): one word of a fixed line swaps every 0.5–0.67 s ("All your favourite singers / bands / …").
- **Verb cards** (14): "It organizes itself", "It drafts your emails", "It schedules your meetings": each card
  is followed by the product doing it.
- **Product at scale** (13–16, 18): UI shown at 1.5–2× (text 16–25 px), a large cursor that causes every change,
  white or near-black ground, almost no decoration.
- **One continuous camera** (09, 20): no cuts; the camera dives through layers into the next world.
- **Colour fields** (03, 10, 18): flat saturated grounds that change with every section.
- **The mark alone at the end**, small (5–15% of width), held 3–14 s, often after the claim line.

## 8. Where the two groups differ (summary)

| | launch | intro |
| --- | --- | --- |
| Shot | 2.4 s | 0.9 s |
| Text | readable lines, held 0.5 + 0.25 s/word | short words, held 0.45 + 0.15 s/word, read while building |
| Type | headline 10.7%H, UI 2.3%H | headline 14%H, hero to 65%H |
| Motion | 2.8% of frame moving; still 33% of the time | 7.6% moving; still 19% |
| Speed | 0.55 fw/s arrival | 0.95 fw/s arrival |
| Eases | expo.out 38% | expo.out 28%, more ease-in (21%) |
| Colour | 5 colours, 94% neutral, ≤ 1 accent | 11.5 colours, 62% neutral, 2–4 accents |
| End card | ≥ 4 s, median 8 s | ≥ 2.5 s, median 3.7 s |

## 9. Notes from the person → numbers

| They say | Change |
| --- | --- |
| "too slow" | shorten shots toward the profile's p25 (launch 1.2 s, intro 0.44 s); arrivals to 8–10 f; keep holds ≥ the floor |
| "too fast" / "can't read it" | raise every hold to the target formula; arrivals to 14–18 f; peak speed ≤ 0.6 fw/s |
| "more energy" | intro rhythm: shots 0.4–0.9 s, `cut_to_music`, cut half the cuts mid-move, speed fastest moves to 2–3 fw/s |
| "cleaner" / "calmer" | fewer colours (≤ 5), one accent ≤ 7%, still 30–40% of the time, one move at a time |
| "more premium" | larger type (headline 10–14%H), longer holds (target), expo eases only, end card ≥ 6 s |
| "feels like slides" | cut on motion (≥ 40% of cuts mid-move), vary shot length (p90 ≥ 3× p10), add a colour flood or a morph |
| "too busy" | moving fraction ≤ 3% at the median; one hero move per shot; remove a third of the moves |
