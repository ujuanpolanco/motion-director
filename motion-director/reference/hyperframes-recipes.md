# The rules in HyperFrames

How each measured rule (`rules.md`) is written in a HyperFrames composition. HyperFrames' own contract
(`/hyperframes`: `class="clip"`, `data-start`/`data-duration`, one paused timeline per scene registered in
`window.__timelines`, `fromTo` inside scenes, no `Date.now()`/random/timers, never tween `display`/`visibility`
on a `.clip`) always applies. These snippets assume 30 fps; at another rate multiply frame counts by fps/30.

## Time in frames

```js
const FPS = 30;
const f = (n) => n / FPS;                         // frames -> seconds
const BPM = 110.2, BEAT0 = 0.412;                // from `mdmeasure.py grid`
const beat = (i) => Math.round((BEAT0 + i * 60 / BPM) * FPS) / FPS;   // from the index, never accumulated
```

Write every position and duration as `f(n)` or `beat(i)`, so the master prompt's frame numbers are the code's.

## Eases by role (measured shares in brackets)

```js
const EASE = {
  enter:  "expo.out",     // arrivals, UI appearing, type landing        (launch 38%, intro 28% of clean moves)
  travel: "expo.inOut",   // camera, carried objects, morphs, floods      (15–20%)
  exit:   "expo.in",      // leaving, zoom-through                        (8%)
  soft:   "power3.out",   // a gentler arrival; power4.out for a harder one
  linear: "none",         // only constant motion that is the point (1–3%)
};
const DUR = {             // frames at 30 fps: launch | intro
  enter:  { launch: 12, intro: 10 },   // p25–p75: 6–24 | 5–22
  travel: { launch: 19, intro: 7 },    // 7–26 | 4–17
  exit:   { launch: 11, intro: 11 },   // 7–20 | 4–17; exits move ~2x faster than arrivals
};
```

## Arrival of a headline (launch: 10.7%H ≈ 116 px; intro: 14%H ≈ 151 px at 1080)

```js
// whole line: lands in 12 f on expo.out, then holds dead still
tl.fromTo("#h1", { opacity: 0, y: 40, filter: "blur(8px)" },
                 { opacity: 1, y: 0, filter: "blur(0px)", duration: f(12), ease: EASE.enter }, f(6));
```

Word reveal (a line revealed, read when complete): 2–4 frames between words.

```js
tl.fromTo("#h1 .w", { opacity: 0, y: "0.35em" },
                    { opacity: 1, y: 0, duration: f(10), ease: EASE.enter, stagger: f(3) }, f(6));
```

Spoken build (a kinetic sentence, read while it builds; 03, 06): one word every 0.5 s (15 f), each lands in 6–8 f.

```js
tl.fromTo("#line .w", { opacity: 0 }, { opacity: 1, duration: f(6), ease: EASE.enter, stagger: f(15) }, 0);
```

Slot word (06): one word in a fixed line swaps every 15–20 frames. Stack the options in one slot and move it:

```js
// .slot is a fixed-height mask (overflow hidden); .reel holds the words stacked, 1em apart
["bands", "groups", "playlists"].forEach((_, i) =>
  tl.to("#reel", { yPercent: -100 * (i + 1) / 4, duration: f(6), ease: EASE.travel }, f(18 * (i + 1))));
```

## Hold, then leave

The hold is the master prompt's number: launch ≥ 0.45 + 0.13 × words s, aim 0.5 + 0.25 × words;
intro ≥ 0.4 + 0.06 × words, aim 0.45 + 0.15 × words. Nothing on the line moves while it is held.

```js
const words = 4, hold = 0.5 + 0.25 * words;          // launch target = 1.5 s
const landed = f(6) + f(12);
tl.to("#h1", { opacity: 0, y: -30, filter: "blur(6px)", duration: f(8), ease: EASE.exit }, landed + hold);
```

## Stillness and amount of motion

- One hero move per moment; the median frame of a launch film has 2.8% of its pixels moving (intro 7.6%).
- Between moves, hold everything still for 0.3–1.5 s (median 0.5 s). Do not add breathing, floating or drifting
  loops to fill it.
- Launch: the product's UI acting (a cursor click, a field filling, a list sorting) is the motion; the camera
  holds the framing 2–7 s while it acts.

## Cuts

- A cut is a seam between two scene hosts (two sub-compositions, or two clips inside one).
- **Cut on motion** (half of launch cuts): start the incoming move before the seam so the cut lands at the
  move's fastest frame, and keep the direction on both sides.

```js
// outgoing scene: the card exits right, expo.in, ending exactly on the seam
tlA.to("#card", { x: 900, duration: f(9), ease: EASE.exit }, SEAM_A - f(9));
// incoming scene: the next card is already moving right when it appears, expo.out from the seam
tlB.fromTo("#next", { x: -500 }, { x: 0, duration: f(14), ease: EASE.enter }, 0);
```

- **Shape match cut** (01, 02): put the shared shape at the same place and size on both sides of the cut
  (same centre, ±2% of the frame); only its material and the world change.
- **Type over cutting plates** (02): the word is a clip on a higher z-index spanning several short image/video
  clips of 6–20 frames each; the word never moves.
- **Never crossfade** two worlds; dissolves are 1% of the pros' transitions.

## Colour flood (10–12% of transitions)

The layout stays, the colours change, over 8–15 frames:

```js
tl.to("#ground", { backgroundColor: "var(--ground-2)", duration: f(10), ease: EASE.travel }, SEAM);
tl.to(".ink",    { color: "var(--ink-2)",             duration: f(10), ease: EASE.travel }, SEAM);
```

## Morph / object becomes the next frame (9–18%)

A container grows into the next scene over 8–13 frames on `expo.inOut`; its fill becomes the next ground
(see HyperFrames `motion.md`, "Transitions with a cause", for the built recipes).

## Camera

A camera move is a transform on a wrapper inside the scene (HyperFrames `motion.md`, "The right mechanism"):
0.3–2.2 s (median 0.8 s), `expo.inOut`, peaking around 1.3 fw/s (≈ 2500 px/s at 1920 wide).
A one-take film keeps a slow travel running underneath (09, 20) and stages each idea as a stop.

## Palette as variables

```css
:root {
  /* launch: one neutral ground, its ink, at most one accent on <= 7% of the frame */
  --ground: #f6f4ef;  --ink: #141414;  --muted: #8a8780;  --accent: #e8572a;
  /* intro: ~4 core colours; each section may own a ground */
  --ground-2: #1f6b4f; --ink-2: #fff6e8;
}
```

## Type sizes at 1080 (font-size; × 2 at 2160)

| Role | launch | intro |
| --- | --- | --- |
| Headline | 104–150 px (9.6–14%H), median 116 | 86–237 px (8–22%H), median 151 |
| Hero word | up to 240 px (22%H) | up to 700 px (65%H), may bleed off frame |
| Quiet line / CTA | 65–90 px (6–8%H) | 65–90 px |
| Product UI text | 16–35 px (1.5–3.2%H) = UI at 1.5–2× | — |
| Never below | 16 px | 24 px |

## End card

```html
<div id="end" class="clip" data-start="…" data-duration="4.5">
  <img id="mark" src="assets/logo.svg" style="width: 12%; …" />   <!-- 5–15% of frame width, centred -->
</div>
```

The mark lands on `expo.out` in 10–14 frames (or is carried in by the last move), then holds still for
≥ 2.5 s; a launch puts the claim or CTA (3–6 words, ≥ 2 s) before or with it.
