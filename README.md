# motion-director

**A free Claude Code skill for motion graphics.** You describe an idea in plain English. It writes a full master prompt (beats, timings on the music's beat grid, palette, type and motion rules), builds the video in [HyperFrames](https://github.com/heygen-com/hyperframes), checks its own frames against rules measured from 20 professional launch films and studio reels, and renders the MP4.

It comes from the Wiredeep video "How To Make Insane Motion Graphics With Claude (No Claude Motion Needed)". Claude Code (Opus 5.5) studied 20 pro videos frame by frame, wrote its own measuring tool, and turned what it found into rules with numbers. This repo is that skill. No reference frames, images or logos are included: only the rules and the tool.

## Install

1. Install the HyperFrames skills in your project:

   ```bash
   npx skills add heygen-com/hyperframes
   ```

   The 4 core skills are enough.
2. Copy `motion-director/` into your project's `.claude/skills/` folder.
3. Start Claude Code in that folder and ask it:

   ```
   Use the motion-director skill. Make a 6-second launch intro for my channel...
   ```

## What's inside

Measured by Claude on 20 professional films: 10 launch films and 10 intros and motion reels. Numbers are launch / intro.

1. **Shot length.** The median shot is 2.4 s / 0.9 s. In every film, the longest tenth of shots is at least 2.4× the shortest tenth.
2. **Text hold.** Launch lines stay on screen at least 0.45 s + 0.13 s per word, and aim for 0.5 + 0.25 s per word. The last line before the logo holds at least 2 s.
3. **Words.** A launch headline is at most 8 words (3–4 is typical). An intro shows 2 words at a time, never more than 7.
4. **Type size.** A headline is about 10.7% / 14% of frame height (116 / 151 px at 1080p). Nothing is smaller than 1.5% (16 px).
5. **Eases.** Arrivals ease out, travel eases in-out, exits ease in. Expo is the house curve. Linear is only 1–3% of moves.
6. **Durations at 30 fps.** An arrival takes about 12 / 10 frames, a camera or travel move 19 / 7, an exit 11.
7. **Stillness.** The median frame has only 2.8% / 7.6% of its pixels moving. Nothing moves at all 33% / 19% of the time.
8. **Cuts.** About 7 seams in 10 are hard cuts. Dissolves are about 1%. Each film uses about 4 kinds of transition.
9. **Colour.** Launch films: 5 colours, 94% neutral, at most one accent covering 7% of the frame or less. Intros: about 4 core colours.
10. **Music.** Most pros don't cut exactly on the beat: their cuts land within 2 frames of a beat about as often as chance (29% vs 30%). Lay the story on the beat grid, and cut on the beat only for reels and stings.

The full tables, the measuring tool and how each number was taken are in `motion-director/reference/`.

## The prompts from the video

### 1 · Building the skill (Claude studies the 20 films)

```
I want you to become a motion designer I can direct in plain English.

In refs/ there are 20 professional videos: launch films from Framer, Notion, Claude, Apple, Figma and Raycast (refs/ui), and brand intros and motion design reels from top studios (refs/intro). They are here only for you to study. Never copy their frames, images or logos into anything you make.

1. Study them properly. Don't just look at a few frames: go through every video frame by frame at its real frame rate. Write your own measuring tool for that (Python with ffmpeg, numpy and OpenCV is fine, they're installed). For each video, measure at least: every cut and the length of every shot; how long text stays on screen and how many words are on screen at once; how fast things move and how they speed up and slow down (how many frames a move takes, the easing); how much of the frame is moving; the colors (how many, the background, the accent); how big the type is compared to the frame; how one scene turns into the next (hard cut, wipe, morph, camera move); and, where there's music, how close the cuts land to the beat. Make contact sheets and look at them too, because some things only the eye catches.

2. Write down what you found as rules with numbers, not adjectives. For example "a headline holds at least X seconds" or "an entrance takes X frames on this curve", never "smooth" or "premium". Note where the two groups (launch films and intros/reels) are different.

3. Turn it into a reusable Claude Code skill in .claude/skills/motion-director/. When I give it an idea in plain English (plus footage, a script, references or brand assets if I have them), it should:
   - first write a full master prompt for itself: the story beat by beat with timings (on the music's beat grid when there is music), the palette, the type, and the motion rules that apply;
   - then build the video in HyperFrames (its skills are already installed here);
   - check still frames against the rules before rendering, and fix whatever breaks them;
   - render the MP4.
   Put the measured rules and your measuring tool inside the skill, so it can check its own work against the pros. Keep it readable: a SKILL.md plus reference files.

4. When you're done, give me a short summary: the 10 rules that matter most, with their numbers.
```

### 2 · The lazy prompt

```
Add motion graphics to my clip raw/claude-motion-raw.mp4.
```

### 3 · Test 1: graphics on raw footage

```
Use the motion-director skill.

raw/claude-motion-raw.mp4 is my raw clip: my voice reading Anthropic's Claude Motion announcement over a plain screen recording of the page. raw/script.txt is exactly what I say.

Turn it into a finished edit for my YouTube channel, Wiredeep. Here's what I'm going for:
- Keep my voice as the only audio, and keep the clip the same length.
- Big captions that land on each phrase as I say it.
- "Claude Motion" deserves a real title moment.
- "your words, your charts, your shapes": show each one as I say it.
- "Claude writes the code that animates every frame": make that visible.
- "only on Team and Enterprise plans" is the key line. Make it impossible to miss.
- Use the screen recording where it helps, like moving in on the line I'm reading, and cover it with graphics where it's boring.
- The end should feel like a turn: you already have it.

My brand is in brand/ (logo, colours, font). Look at the references in refs/ for the style.
Render the final video to out/edit-v1.mp4.
```

### 4 · Test 1: the follow-up, in the same chat

```
This is good. The CLAUDE MOTION title, the chart that builds on "your words, your charts, your shapes", the code with the frame counter, and the orange TEAM AND ENTERPRISE card all work. Keep them exactly as they are.

Change three things:
- When the screen recording is on screen, my captions sit on top of the page's text and it gets cluttered (around "No video model draws the pictures" and "It's in beta"). Give the captions a clean area, or darken the page behind them.
- Around 5 seconds, right after the /motion prompt, there's an empty dark box. Nothing should ever sit empty on screen.
- Some page shots crop the interface awkwardly (the "Project or folder" bar cut off at the top). Frame each push-in so it shows one clear line, nothing half cut.

Keep my voice and the same length. Render it to out/edit-v2.mp4.
```

### 5 · Test 2: a launch intro from scratch

```
Use the motion-director skill.

Make a 6-second launch intro for my YouTube channel, Wiredeep. It will open every video.

The channel tests AI tools on a real machine, every week. The logo is a cable seen from the end: a copper ring with five glowing cyan fibers that form a W (it's in brand/).

The vibe: we're travelling inside a cable. A pulse of light races along it, then we see the cable from the end and it builds into the logo, layer by layer, on the beat. Fast and precise, a bit of tech, but not the usual neon AI look.

End on the logo with WIREDEEP and "AI tools, tested on a real machine." underneath, held long enough to read.

Music: assets/music/visions.mp3. Use its best 6 seconds, around the drop, and cut to the beat.

Look at the references in refs/ for the level I want. Render the final video with the music to out/intro-v1.mp4.
```

### 6 · Test 2: the follow-up, in the same chat

```
Good start. The story works: the tunnel, the pulse along the cable, the cable from the end, the W. Keep that order and the end card.

Now I want it to hit harder:
- The pacing should feel snappier. The tunnel and the side view feel slow: make them shorter, cut them to the beat, and let the pulse really race.
- Make the light feel real: glow and motion blur on the pulse, so it streaks instead of sliding.
- The logo build should be a moment: the fibers light up one by one on the beat, then the W snaps on with a flash, right on the strongest hit of the music.
- Make the text pop more: WIREDEEP lands big and heavy, with impact, instead of typing on. The tagline comes in after it.

Keep it 6 seconds, same music. Render it to out/intro-v2.mp4.
```

## Notes

- **Claude Motion:** Anthropic's own tool, in beta on Team and Enterprise plans. This skill does the same kind of work with Claude Code on any plan that includes it.
- **Permissions:** install skills only from sources you trust. They run with your agent's full permissions.
- **License:** MIT. HyperFrames is a separate project by HeyGen, with its own license.
