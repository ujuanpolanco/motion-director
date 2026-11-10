# The master prompt

Write this before building anything, as `MASTER_PROMPT.md` at the project root, and save its shot list as
`plan.json` next to it. It is the director's brief to yourself: every adjective becomes a number from
`rules.md`, every beat gets a frame range. It is a superset of HyperFrames' `SPEC.md`; copy it to `SPEC.md`
so the HyperFrames review loop finds it.

Fill every field. A field you cannot fill is a question for the person or an assumption you state.

```text
# <TITLE> — master prompt

IDEA:      the person's words, verbatim
ONE THING: what the viewer remembers, in their words (one line)
PROFILE:   launch | intro   (rules.md §0 explains the choice); why, in one clause
CUT TO MUSIC: yes | no   (rules.md §6: reels and stings yes, launch films no)
INPUTS:    footage / script / references / brand assets given, each with its path and what it is used for
           references given -> measured with `mdmeasure.py analyze`; their numbers override the profile:
           list each overridden number here
OUTPUT:    1920x1080, 30 fps (or the footage's fps / the asked format), LENGTH s = N frames

MUSIC:     file | "none, delivered silent because …"
           BPM, first downbeat (s), frames/beat, frames/bar  (from `mdmeasure.py grid`)
           the bar where the music opens up / the hit the payoff lands on

STORY (beat by beat; frames are absolute; one row per shot)
| # | frames      | sec       | bar.beat | beat job        | what the viewer sees (objects named) | on-screen copy (words) | hero move (frames, ease) | in-transition (cause) |
|---|-------------|-----------|----------|-----------------|--------------------------------------|------------------------|--------------------------|-----------------------|
| 1 | 0–63        | 0.00–2.10 | 1.1      | hook            | …                                    | "…" (3w, holds 1.9 s)  | push-in 24f power2.inOut | — (frame 0 is a picture, never black) |
| … |             |           |          |                 |                                      |                        |                          |                       |

PALETTE:   ground hex (share of frame), ink hex, ONE accent hex + where it may appear (one word / the payoff / the mark),
           secondary neutrals; total distinct colours <= rules.md limit for the profile
TYPE:      display face + weight, size in px and %H (headline / quiet line / UI label), tracking, case;
           words per line max; lines on screen max
MOTION:    enter: N frames, ease; exit: N frames, ease; camera: N frames, ease; stagger: words/letters/items in frames;
           title after landing: still for >= N s; holds; what moves continuously and at what speed (fw/s)
TRANSITIONS: list of kinds used (3–5 for launch), each with its cause on screen; hard-cut share target
SOUND:     bed, hits (on which frames), levels
BANNED:    HyperFrames' defaults (spec.md "BANNED by default") + this film's own
QA FRAMES: the frames to snapshot and what each must show (one per shot at its readable moment,
           the payoff, the end card, frame 0)
```

## plan.json

The STORY table, machine-readable, so `mdmeasure.py plan plan.json` checks it against the measured rules
before any HTML exists:

```json
{
  "profile": "launch", "fps": 30, "frames": 900,
  "bpm": 110.2, "beat_offset_s": 0.412, "beats_per_bar": 4, "cut_to_music": false,
  "shots": [
    {"id": "hook", "start": 0, "end": 78, "in": "hard-cut",
     "text": [{"copy": "Your notes, finally sorted", "start": 12, "end": 78, "font_pct_h": 7}],
     "moves": [{"what": "headline", "role": "enter", "frames": 12, "ease": "expo.out"},
               {"what": "camera", "role": "camera", "frames": 30, "ease": "power2.inOut"}]},
    {"id": "problem", "start": 78, "end": 143, "in": "wipe"}
  ]
}
```

- `in` is the transition into the shot: `hard-cut`, `hard-cut-on-motion`, `match-cut`, `wipe`, `camera-push`,
  `camera-pan`, `morph`, `zoom-through`, `colour-flood`, `dissolve`, `fade-through-black`.
- `role` is one of `enter`, `exit`, `camera`, `ui`, `kinetic` (see `rules.md` §4); `frames` is the tween length.
- A text item may carry `"kinetic": true` (built word by word and read while it builds: only the floor applies)
  or `"ui": true` (product UI text, not read word by word: no hold check).
- A shot may carry `"downbeat": true`: it must start on a bar line (the payoff, the end card).
- `cut_to_music: true` makes every cut a FAIL unless it is within ±1 frame of a beat or half beat
  (reels, montages and stings cut to music); false keeps the beat report as information (launch films).
- `beat_offset_s` is the first downbeat printed by `mdmeasure.py grid`.
- Times are frames at `fps`. A beat frame is `round(offset_s*fps + i*fps*60/bpm)`, computed from its index.

## Writing the story

- Take the structure from `rules.md` §1 and the shot lengths from §2 for the profile, then put every boundary
  on the grid: sections and the end card on bar lines; with `cut_to_music`, every cut on a beat or half beat.
  Without music, use the profile's shot-length distribution and vary it (p90 ≥ 2.5× p10).
- Give each beat ONE hero move; list it with its frames and ease.
- Write the copy, count the words, compute the hold (`rules.md` §3) and make the shot at least that long.
  Too many words: cut words, never shrink type or shorten the hold.
- Name the cause of every transition (the thing on screen that carries the eye across).
- Then run `mdmeasure.py plan plan.json` and fix every FAIL in the table before building.
