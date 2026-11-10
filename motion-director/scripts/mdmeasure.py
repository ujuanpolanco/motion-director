#!/usr/bin/env python3
"""
mdmeasure - measure motion-design craft in a video, frame by frame, at its real frame rate.

Subcommands
  analyze  VIDEO [--out DIR] [--sheets] [--no-ocr]   full measurement -> DIR/<name>.json (+ contact sheets)
  aggregate JSON... [--out FILE]                     group stats (by parent folder of the video) -> markdown + json
  check    VIDEO --profile launch|intro [--rules R]   analyze a render and compare it with the pros' ranges
  stills   PNG... --profile launch|intro [--rules R]  per-frame checks (type size, words, palette, safe area)
  plan     PLAN.json [--rules R]                     check the master prompt's shot list before building
  grid     AUDIO [--fps 30] [--bpm B --offset S]      beat and bar grid in frames, for timing a new film

Every number is measured with the same instrument for the references and for your own renders,
so a render can be compared with the pros directly.

Units
  time       seconds and frames (at the video's own fps)
  speed      fw/s = frame widths per second (0.5 fw/s = crosses half the frame in a second)
  type size  estimated CSS font-size as % of frame height (OCR line box / 1.2, calibrated on Arial/Segoe)
  colour     hex; distinct colours merged at Delta-E 76 < 15

Needs: ffmpeg/ffprobe on PATH, numpy, scipy, opencv; OCR uses rapidocr_onnxruntime when installed
(pip install rapidocr-onnxruntime); without it, text metrics are skipped.
Beat grid: `npx hyperframes beats` when it finds a steady beat, else the built-in tracker.
"""
import argparse, json, math, os, re, subprocess, sys, shutil
from difflib import SequenceMatcher

import numpy as np
import cv2

cv2.setNumThreads(1)   # one process per video; OpenCV's own pool oversubscribes the CPU

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES = os.path.join(HERE, "..", "reference", "rules.json")

OCR_BOX_TO_FONT = 1.2       # OCR line box height / CSS font-size (calibrated)
DISPLAY_MIN_H = 0.03        # OCR box >= 3% of frame height -> "display" text (font >= ~2.5% H)
FLOW_W = 240                # optical-flow working width
ANA_W = 960                 # decode width (OCR uses this)


# ----------------------------------------------------------------------------- io

def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    dur = float(d["format"].get("duration", v.get("duration", 0)))
    has_audio = any(s["codec_type"] == "audio" for s in d["streams"])
    return dict(fps=fps, w=int(v["width"]), h=int(v["height"]), duration=dur, has_audio=has_audio)


def frames(path, w, h, keep=None):
    """Yield (index, bgr frame) for every decoded frame at native rate."""
    cmd = ["ffmpeg", "-v", "error", "-threads", "2", "-i", path, "-an", "-fps_mode", "passthrough",
           "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=w * h * 3)
    n = w * h * 3
    i = 0
    try:
        while True:
            buf = p.stdout.read(n)
            if len(buf) < n:
                break
            if keep is None or i in keep:
                yield i, np.frombuffer(buf, np.uint8).reshape(h, w, 3)
            i += 1
    finally:
        p.stdout.close()
        p.wait()


WORD_RE = re.compile(r"[^\W\d_][\w'’]*|\d+[^\W\d_][\w'’]*", re.UNICODE)


def words_of(t):
    return [w for w in WORD_RE.findall(t) if len(w) >= 2 or w.lower() in ("a", "i")]


def get_ocr():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception:
        return None
    try:
        return RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1, use_cls=False)
    except TypeError:
        return RapidOCR()


def hexc(bgr):
    b, g, r = [int(max(0, min(255, round(float(x))))) for x in bgr]
    return f"#{r:02x}{g:02x}{b:02x}"


def lab_of(bgr_pixels):
    px = np.asarray(bgr_pixels, np.float32).reshape(-1, 1, 3) / 255.0
    return cv2.cvtColor(px, cv2.COLOR_BGR2Lab).reshape(-1, 3)


def lab_hex(hx):
    return lab_of([[int(hx[5:7], 16), int(hx[3:5], 16), int(hx[1:3], 16)]])[0]


def pct(a, q):
    a = [x for x in a if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return float(np.percentile(a, q)) if a else None


def rnd(x, n=3):
    if x is None:
        return None
    if isinstance(x, (list, tuple)):
        return [rnd(v, n) for v in x]
    return round(float(x), n)


# ----------------------------------------------------------------------------- eases

def _ease_funcs():
    def p_out(k): return lambda t: 1 - (1 - t) ** k
    def p_in(k): return lambda t: t ** k
    def p_io(k): return lambda t: np.where(t < 0.5, (2 * t) ** k / 2, 1 - (2 * (1 - t)) ** k / 2)
    E = {"linear": lambda t: t, "sine.inOut": lambda t: -(np.cos(np.pi * t) - 1) / 2}
    for k, nm in [(2, "power1"), (3, "power2"), (4, "power3"), (5, "power4")]:
        E[nm + ".out"] = p_out(k); E[nm + ".in"] = p_in(k); E[nm + ".inOut"] = p_io(k)
    E["expo.out"] = lambda t: 1 - 2 ** (-10 * t)
    E["expo.in"] = lambda t: 2 ** (10 * t - 10)
    E["expo.inOut"] = lambda t: np.where(t < 0.5, 2 ** (20 * t - 10) / 2, (2 - 2 ** (-20 * t + 10)) / 2)
    return E


EASES = _ease_funcs()
_TT = np.linspace(0, 1, 2001)
EASE_VEL = {k: np.gradient(np.asarray(f(_TT), float) * np.ones_like(_TT), _TT) for k, f in EASES.items()}


def fit_ease(v, floor_ratio):
    """Fit an observed speed profile v (one move) to GSAP eases.
    The visible part of a move is where speed > floor; each candidate is truncated the same way
    before comparing shapes. Returns (best, rmse, visible_fraction_of_tween, ranking)."""
    v = np.asarray(v, float)
    n = len(v)
    if n < 3 or v.max() <= 0:
        return None, None, None, []
    obs = v / v.max()
    res = []
    for name, vel in EASE_VEL.items():
        m = vel / vel.max()
        vis = np.where(m >= min(floor_ratio, 0.95))[0]
        if len(vis) < 2:
            continue
        a, b = vis[0], vis[-1]
        seg = m[a:b + 1]
        x = np.linspace(0, 1, len(seg))
        cand = np.interp(np.linspace(0, 1, n), x, seg)
        cand = cand / cand.max()
        err = float(np.sqrt(np.mean((cand - obs) ** 2)))
        res.append((err, name, (b - a) / len(_TT)))
    res.sort()
    best = res[0]
    return best[1], best[0], best[2], [(r[1], round(r[0], 3)) for r in res[:4]]


SAT_PX = 28.0   # DIS flow saturates around here (px per frame at 240 px wide)


def fit_ease_model(v, max_px=SAT_PX):
    """Fit per-frame displacement v[k] (k = 0..n-1, with a few still frames padded on each side) to
    A * |E((k - s0)/D) - E((k - 1 - s0)/D)| for every GSAP ease E, tween length D (frames) and start s0.
    Returns (ease, D_frames, s0, rmse_rel, ranking). Saturation is modelled by clipping both sides."""
    v = np.asarray(v, float)
    n = len(v)
    if n < 4 or v.max() <= 0:
        return None, None, None, None, []
    vis = int(np.sum(v > 0.15 * v.max()))
    Ds = np.arange(max(2.0, vis * 0.6), max(4.0, vis * 4.0) + 0.01, 0.5)
    k = np.arange(n, dtype=float)
    vc = np.minimum(v, max_px)
    best_all = []
    for name, f in EASES.items():
        best = (1e18, None, None)
        for D in Ds:
            s0s = np.arange(-1.0, n - D * 0.3, 0.25)
            if len(s0s) == 0:
                continue
            t1 = np.clip((k[None, :] - s0s[:, None]) / D, 0, 1)
            t0 = np.clip((k[None, :] - 1 - s0s[:, None]) / D, 0, 1)
            d = np.abs(np.asarray(f(t1), float) - np.asarray(f(t0), float))
            # amplitude by least squares on unsaturated frames, then clip the prediction
            w = (v < max_px * 0.95)[None, :]
            A = (d * vc[None, :] * w).sum(1) / ((d * d * w).sum(1) + 1e-12)
            pred = np.minimum(A[:, None] * d, max_px)
            err = ((pred - vc[None, :]) ** 2).sum(1)
            j = int(np.argmin(err))
            if err[j] < best[0]:
                best = (float(err[j]), float(D), float(s0s[j]))
        if best[1] is not None:
            best_all.append((best[0], name, best[1], best[2]))
    best_all.sort()
    e, name, D, s0 = best_all[0]
    rel = math.sqrt(e / n) / max(1e-6, vc.max())
    return name, D, s0, rel, [(b[1], round(math.sqrt(b[0] / n) / max(1e-6, vc.max()), 3), b[2]) for b in best_all[:4]]


def ease_family(name):
    if name is None:
        return None
    if name == "linear":
        return "linear"
    return name.split(".")[1]  # out / in / inOut


# ----------------------------------------------------------------------------- audio

def audio_wav(path, sr=22050):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr),
                        "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.float32), sr


def onset_envelope(y, sr, hop=256, n_fft=1024):
    if len(y) < n_fft * 2:
        return np.zeros(1), sr / hop
    win = np.hanning(n_fft).astype(np.float32)
    nfr = 1 + (len(y) - n_fft) // hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(nfr)[:, None]
    S = np.abs(np.fft.rfft(y[idx] * win, axis=1))
    freqs = np.fft.rfftfreq(n_fft, 1 / sr)
    edges = np.geomspace(40, sr / 2, 65)
    bands = np.stack([S[:, (freqs >= edges[i]) & (freqs < edges[i + 1])].sum(1) for i in range(64)], 1)
    L = np.log1p(100 * bands)
    flux = np.maximum(0, np.diff(L, axis=0)).sum(1)
    flux = np.concatenate([[0], flux])
    flux = flux - np.convolve(flux, np.ones(16) / 16, mode="same")
    flux = np.maximum(flux, 0)
    if flux.max() > 0:
        flux = flux / flux.max()
    return flux, sr / hop


def track_beats(env, rate):
    """Ellis-style dynamic-programming beat tracker. Returns (bpm, beat_times, pulse_clarity)."""
    if len(env) < rate * 4:
        return None, [], 0.0
    e = env - env.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    ac = ac / (ac[0] + 1e-9)
    lags = np.arange(len(ac))
    bpm_of = 60 * rate / np.maximum(lags, 1)
    ok = (bpm_of >= 60) & (bpm_of <= 200)
    prior = np.exp(-0.5 * (np.log2(bpm_of / 120.0) / 1.0) ** 2)
    score = np.where(ok, ac * prior, -1)
    lag = int(np.argmax(score))
    clarity = float(ac[lag])
    bpm = 60 * rate / lag
    period = lag
    N = len(env)
    cum = env.copy().astype(float)
    back = -np.ones(N, int)
    lo, hi = int(round(period * 0.5)), int(round(period * 2))
    tight = 100.0
    for i in range(N):
        a, b = max(0, i - hi), i - lo
        if b <= a:
            continue
        prev = np.arange(a, b)
        pen = -tight * (np.log((i - prev) / period)) ** 2
        cand = cum[prev] + pen
        j = int(np.argmax(cand))
        if cand[j] > 0:
            cum[i] = env[i] + cand[j]
            back[i] = prev[j]
    tail = np.arange(max(0, N - period), N)
    i = int(tail[np.argmax(cum[tail])])
    beats = []
    while i >= 0:
        beats.append(i)
        i = back[i]
    beats = np.array(beats[::-1]) / rate
    return float(bpm), beats.tolist(), clarity


def hf_beats(path):
    exe = shutil.which("npx") or shutil.which("npx.cmd")
    if not exe:
        return None
    try:
        out = subprocess.run(f'npx hyperframes beats "{path}" --json', capture_output=True, text=True,
                             timeout=180, shell=True).stdout
        d = json.loads(out[out.index("{"):])
        if d.get("ok") and d.get("count", 0) >= 8:
            return float(d["bpm"]), [float(t) for t in d["beatTimes"]]
    except Exception:
        return None
    return None


def analyze_audio(path, cut_times, fps, use_hf=True):
    y, sr = audio_wav(path)
    if len(y) < sr:
        return {"present": False}
    blk = sr // 20
    nb = len(y) // blk
    rms = np.sqrt((y[:nb * blk].reshape(nb, blk) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    active = float(np.mean(db > -45))
    env, rate = onset_envelope(y, sr)
    bpm_own, beats_own, clarity = track_beats(env, rate)
    src = "builtin"
    bpm, beats = bpm_own, beats_own
    hf = hf_beats(path) if use_hf else None
    if hf:
        bpm, beats = hf
        src = "hyperframes"
    out = {"present": True, "active_fraction": rnd(active), "pulse_clarity": rnd(clarity),
           "bpm": rnd(bpm, 1), "bpm_builtin": rnd(bpm_own, 1), "beat_source": src, "n_beats": len(beats)}
    from scipy.signal import find_peaks
    pk, _ = find_peaks(env, height=np.percentile(env, 97), distance=max(1, int(rate * 0.25)))
    hits = pk / rate
    out["hits_per_s"] = rnd(len(hits) / (len(y) / sr), 2)
    if active < 0.3 or not beats or len(cut_times) < 2 or bpm is None:
        return out
    beats = np.array(beats)
    period = 60.0 / bpm
    dur = len(y) / sr
    pre = np.arange(beats[0] - period, -period, -period)[::-1]
    post = np.arange(beats[-1] + period, dur + period, period)
    allb = np.concatenate([pre, beats, post])
    half = np.sort(np.concatenate([allb, allb[:-1] + np.diff(allb) / 2]))
    ct = np.array(cut_times)

    def near(ts, grid_):
        grid_ = np.asarray(grid_)
        j = np.clip(np.searchsorted(grid_, ts), 1, len(grid_) - 1)
        a, b = grid_[j - 1], grid_[j]
        return np.where(np.abs(ts - a) < np.abs(ts - b), ts - a, ts - b)

    off_b = near(ct, allb)
    off_h = near(ct, half)
    f = 1.0 / fps
    rng = np.random.default_rng(7)
    rand = rng.uniform(0.5, dur - 0.5, 4000)
    chance_b = float(np.mean(np.abs(near(rand, allb)) <= 2.01 * f))
    chance_h = float(np.mean(np.abs(near(rand, half)) <= 2.01 * f))
    c = {
        "n": len(ct),
        "median_abs_offset_beat_frames": rnd(np.median(np.abs(off_b)) * fps, 2),
        "within_1f_beat": rnd(np.mean(np.abs(off_b) <= 1.01 * f)),
        "within_2f_beat": rnd(np.mean(np.abs(off_b) <= 2.01 * f)),
        "chance_within_2f_beat": rnd(chance_b),
        "within_2f_halfbeat": rnd(np.mean(np.abs(off_h) <= 2.01 * f)),
        "chance_within_2f_halfbeat": rnd(chance_h),
        "median_signed_offset_ms": rnd(np.median(off_b) * 1000, 1),
    }
    if len(hits) > 1:
        off_hit = near(ct, hits)
        c["within_2f_hit"] = rnd(np.mean(np.abs(off_hit) <= 2.01 * f))
        c["chance_within_2f_hit"] = rnd(float(np.mean(np.abs(near(rand, hits)) <= 2.01 * f)))
    # phase locking: are cuts on a grid of the tempo, whatever the tracker's phase error?
    ph = 2 * np.pi * (ct % period) / period
    R = float(np.abs(np.mean(np.exp(1j * ph))))
    c["phase_lock_R"] = rnd(R)            # 0 = random, 1 = every cut at the same beat phase
    c["phase_lock_R_chance"] = rnd(1 / math.sqrt(len(ct)))
    mean_ph = float(np.angle(np.mean(np.exp(1j * ph))))
    dev = np.angle(np.exp(1j * (ph - mean_ph))) / (2 * np.pi) * period
    c["within_2f_of_locked_grid"] = rnd(np.mean(np.abs(dev) <= 2.01 * f))
    hdev = np.angle(np.exp(1j * 2 * (ph - mean_ph))) / (2 * np.pi) * period / 2
    c["within_2f_of_locked_halfgrid"] = rnd(np.mean(np.abs(hdev) <= 2.01 * f))
    c["grid_phase_ms"] = rnd(mean_ph / (2 * np.pi) * period * 1000, 1)
    out["cuts"] = c
    out["beat_frames"] = rnd(fps * period, 2)
    # shot lengths in beats
    sl = np.diff(ct) / period
    out["shot_len_beats_median"] = rnd(np.median(sl), 2) if len(sl) else None
    out["shot_len_integer_beats_share"] = rnd(np.mean(np.abs(sl - np.round(sl)) < 0.15)) if len(sl) else None
    return out


# ----------------------------------------------------------------------------- analysis

def hist_hsv(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], None, [12, 4, 4], [0, 180, 0, 256, 0, 256]).ravel()
    return h / (h.sum() + 1e-9)


def hdist(a, b):
    return float(1.0 - np.minimum(a, b).sum())


def global_model(flow, mag, thr):
    """Fit a similarity motion (pan + zoom + rotate) to moving pixels.
    Returns (tx, ty, s, coherence) - coherence = share of moving pixels explained within 0.5 px."""
    h, w = mag.shape
    ys, xs = np.mgrid[0:h:3, 0:w:3]
    u = flow[0:h:3, 0:w:3, 0].ravel(); v = flow[0:h:3, 0:w:3, 1].ravel()
    m = mag[0:h:3, 0:w:3].ravel() > thr
    if m.sum() < 30:
        return 0.0, 0.0, 0.0, 0.0
    x = (xs.ravel() - w / 2) / w; y = (ys.ravel() - h / 2) / w
    x, y, u, v = x[m], y[m], u[m], v[m]
    one, zero = np.ones_like(x), np.zeros_like(x)
    A = np.concatenate([np.stack([one, zero, x, -y], 1), np.stack([zero, one, y, x], 1)])
    bvec = np.concatenate([u, v])
    sol, *_ = np.linalg.lstsq(A, bvec, rcond=None)
    pred = A @ sol
    r = np.hypot((pred - bvec)[:len(u)], (pred - bvec)[len(u):])
    return float(sol[0]), float(sol[1]), float(sol[2]) / w, float(np.mean(r < 0.5))


def analyze(path, out_dir=None, sheets=False, use_ocr=True, use_hf=True, verbose=True, reuse_ocr=None):
    info = probe(path)
    fps, W0, H0 = info["fps"], info["w"], info["h"]
    aw = ANA_W
    ah = int(round(aw * H0 / W0 / 2) * 2)
    fw = FLOW_W
    fh = int(round(fw * H0 / W0 / 2) * 2)
    ocr_step = max(1, int(round(fps / 6.0)))   # ~6 Hz text sampling
    cached = None
    if reuse_ocr and os.path.exists(reuse_ocr):
        cached = {smp["f"]: smp for smp in json.load(open(reuse_ocr, encoding="utf-8")).get("ocr_frames", [])}
        if not cached:
            cached = None
    ocr = get_ocr() if (use_ocr and cached is None) else None

    H, D, CH, V95, MOVF, COH, GSPD, ZOOM, LUM, THUMB = ([] for _ in range(10))
    # DIS optical flow: tracks displacements up to ~30 px at 240 px wide (12% of the frame per frame);
    # calibrated against rendered GSAP moves with known eases (reference/measurements.md)
    DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    ocr_samples = []
    prev_g = None
    for i, fr in frames(path, aw, ah):
        small = cv2.resize(fr, (fw, fh), interpolation=cv2.INTER_AREA)
        g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        hh = hist_hsv(small)
        THUMB.append(cv2.resize(small, (160, int(round(160 * fh / fw))), interpolation=cv2.INTER_AREA))
        LUM.append(float(g.mean() / 255))
        if prev_g is None:
            D.append(0.0); CH.append(0.0); V95.append(0.0); MOVF.append(0.0)
            COH.append(0.0); GSPD.append(0.0); ZOOM.append(0.0)
        else:
            D.append(hdist(hh, H[-1]))
            diff = cv2.absdiff(g, prev_g)
            CH.append(float(np.mean(diff > 20)))
            flow = DIS.calc(prev_g, g, None)
            mag = np.hypot(flow[..., 0], flow[..., 1])
            # flat regions with no change carry no measurable motion (Farneback invents it there)
            lap = cv2.Laplacian(g, cv2.CV_32F, ksize=3)
            textured = (diff > 6) | (lap * lap > 50)
            magt = mag * textured
            # speed of the fastest mover, independent of its size: p90 of flow over pixels that changed
            chg = diff > 12
            V95.append(float(np.percentile(mag[chg], 90)) if chg.sum() >= 20 else 0.0)
            MOVF.append(float(np.mean(magt > 0.5)))
            tx, ty, s, coh = global_model(flow, magt, 0.5)
            COH.append(coh); GSPD.append(float(math.hypot(tx, ty))); ZOOM.append(s)
        H.append(hh)
        if cached is not None and i % ocr_step == 0:
            ocr_samples.append(cached.get(i, {"f": i, "items": []}))
        elif ocr is not None and i % ocr_step == 0:
            try:
                r, _ = ocr(fr)
            except Exception:
                r = None
            items = []
            for box, txt, conf in (r or []):
                conf = float(conf)
                if conf < 0.6 or not txt.strip():
                    continue
                b = np.array(box, float)
                items.append({"t": txt, "c": round(conf, 2),
                              "h": round((b[:, 1].max() - b[:, 1].min()) / ah, 4),
                              "w": round((b[:, 0].max() - b[:, 0].min()) / aw, 4),
                              "x": round(b[:, 0].mean() / aw, 3), "y": round(b[:, 1].mean() / ah, 3)})
            ocr_samples.append({"f": i, "items": items})
        prev_g = g
        if verbose and i % 500 == 0:
            print(f"  {os.path.basename(path)} frame {i}", file=sys.stderr, flush=True)
    n = len(D)
    D = np.array(D); CH = np.array(CH); V95 = np.array(V95); MOVF = np.array(MOVF)
    COH = np.array(COH); GSPD = np.array(GSPD); ZOOM = np.array(ZOOM); LUM = np.array(LUM)

    # ---------------- cuts (hard) ----------------
    def local_med(a, i, r=6):
        lo, hi = max(1, i - r), min(len(a), i + r + 1)
        nb = np.concatenate([a[lo:i], a[i + 1:hi]])
        return float(np.median(nb)) if len(nb) else 0.0

    # structure persistence: an in-place colour change (a flood, dark mode, a dim) keeps the layout.
    # Normalised correlation of gradient magnitude: cuts measured <= 0.27, floods >= 0.56 on the references.
    def _gm(t_):
        g_ = cv2.GaussianBlur(cv2.cvtColor(t_, cv2.COLOR_BGR2GRAY).astype(np.float32), (3, 3), 0)
        m_ = np.hypot(cv2.Sobel(g_, cv2.CV_32F, 1, 0), cv2.Sobel(g_, cv2.CV_32F, 0, 1))
        return m_ - m_.mean()

    def edge_keep(i):
        a_, b_ = _gm(THUMB[i - 1]), _gm(THUMB[i])
        return float((a_ * b_).sum() / np.sqrt((a_ * a_).sum() * (b_ * b_).sum() + 1e-6))

    cuts, flashes, floods = [], [], []
    for i in range(1, n):
        lm = local_med(D, i)
        lc = local_med(CH, i)
        hard = (D[i] > 0.28 and D[i] > 3.0 * max(lm, 0.03)) or \
               (CH[i] > 0.45 and D[i] > 0.12 and D[i] > 3.0 * max(lm, 0.02) and CH[i] > 2.5 * max(lc, 0.05))
        if not hard:
            continue
        if edge_keep(i) > 0.5:
            floods.append(i)          # same layout, new colours
            continue
        if cuts and i - cuts[-1] == 1 and i - 2 >= 0 and hdist(H[i - 2], H[i]) < 0.15:
            flashes.append(i - 1)            # one inserted frame, then back
            cuts.pop()
            continue
        cuts.append(i)

    # ---------------- gradual transitions (twin comparison) ----------------
    cutset = set(cuts)
    Ts = max(0.04, 2.5 * float(np.median(D[1:])) if n > 2 else 0.04)
    grads = []
    i = 1
    while i < n:
        if D[i] > Ts and i not in cutset:
            s = i - 1
            j = i
            gap = 0
            while j + 1 < n and (j + 1) not in cutset and (D[j + 1] > Ts * 0.7 or gap < 1):
                gap = gap + 1 if D[j + 1] <= Ts * 0.7 else 0
                j += 1
            e = j - gap
            if e - s >= 3 and hdist(H[s], H[e]) > 0.33:
                grads.append([s, e])
            i = j + 1
        else:
            i += 1

    def classify_grad(s, e):
        L = LUM[s:e + 1]
        mid = L[1:-1] if len(L) > 2 else L
        if e - s > 2.0 * fps:
            return "continuous"
        if mid.min() < 0.05 and L[0] > mid.min() + 0.08 and L[-1] > mid.min() + 0.08:
            return "fade-through-black"
        if mid.max() > 0.93 and L[0] < mid.max() - 0.08 and L[-1] < mid.max() - 0.08:
            return "fade-through-white"
        a = THUMB[s].astype(np.float32); b = THUMB[e].astype(np.float32)
        dab = np.linalg.norm(a - b) + 1e-6
        dvec = (a - b).ravel()
        resid, steps, prof = [], [], []
        for m in range(s + 1, e):
            f = THUMB[m].astype(np.float32)
            al = float(np.clip(np.dot((f - b).ravel(), dvec) / (np.dot(dvec, dvec) + 1e-6), 0, 1))
            resid.append(np.linalg.norm(f - (al * a + (1 - al) * b)) / dab)
            closer_end = (np.abs(f - b).sum(2) < np.abs(f - a).sum(2)).astype(np.float32)
            fr_ = closer_end.mean()
            if 0.15 < fr_ < 0.85:
                col = closer_end.mean(0); row = closer_end.mean(1)
                stepc = float(np.mean(np.minimum(col, 1 - col)))
                stepr = float(np.mean(np.minimum(row, 1 - row)))
                steps.append(min(stepc, stepr))
                prof.append("horizontal" if stepc < stepr else "vertical")
        coh = float(np.mean(COH[s + 1:e + 1]))
        gsp = float(np.mean(GSPD[s + 1:e + 1]))
        zm = float(np.mean(np.abs(ZOOM[s + 1:e + 1])))
        if steps and np.median(steps) < 0.12:
            return "wipe-" + max(set(prof), key=prof.count)
        if coh > 0.55 and float(np.mean(MOVF[s + 1:e + 1])) > 0.4 and (gsp > 1.0 or zm > 0.004):
            return "camera-push" if zm * fw > gsp * 0.6 else "camera-pan"
        if resid and np.median(resid) < 0.22:
            return "dissolve"
        return "morph/in-place"

    # clusters of "cuts" a few frames apart are often one fast wipe / whip: classify the span as a whole
    merged_spans = []
    k_ = 0
    while k_ < len(cuts):
        j_ = k_
        while j_ + 1 < len(cuts) and cuts[j_ + 1] - cuts[j_] <= 6:
            j_ += 1
        if j_ > k_:
            s0, e0 = cuts[k_] - 1, cuts[j_]
            kind0 = classify_grad(s0, e0)
            if kind0.startswith("wipe") or kind0.startswith("camera"):
                merged_spans.append((s0, e0, kind0))
                for c_ in cuts[k_:j_ + 1]:
                    cutset.discard(c_)
        k_ = j_ + 1
    cuts = [c_ for c_ in cuts if c_ in cutset]

    transitions = []
    for s0, e0, kind0 in merged_spans:
        transitions.append({"frame": int((s0 + e0) // 2), "t": rnd((s0 + e0) / 2 / fps), "kind": kind0,
                            "frames": int(e0 - s0), "start": rnd(s0 / fps), "end": rnd(e0 / fps)})
    fl_runs = []
    for f_ in floods:
        if fl_runs and f_ - fl_runs[-1][1] <= 3:
            fl_runs[-1][1] = f_
        else:
            fl_runs.append([f_, f_])
    for a0, b0 in fl_runs:
        transitions.append({"frame": int(a0), "t": rnd(a0 / fps), "kind": "colour-flood",
                            "frames": int(b0 - a0 + 1), "start": rnd(a0 / fps), "end": rnd(b0 / fps)})
    for c in cuts:
        pre = V95[max(1, c - 2):c]
        post = V95[c + 1:c + 3]
        kind = "hard-cut"
        if len(pre) and pre.mean() > 4.0 and len(post) and post.mean() > 4.0:
            kind = "hard-cut-on-motion"
        transitions.append({"frame": c, "t": rnd(c / fps), "kind": kind, "frames": 1})
    fl_set = set(floods)
    for s, e in grads:
        if any(f_ in fl_set for f_ in range(s, e + 2)):
            continue     # the flood already accounts for it
        k = classify_grad(s, e)
        transitions.append({"frame": int((s + e) // 2), "t": rnd((s + e) / 2 / fps), "kind": k,
                            "frames": int(e - s), "start": rnd(s / fps), "end": rnd(e / fps)})
    transitions.sort(key=lambda x: x["frame"])
    bounds = [t["frame"] for t in transitions if t["kind"] not in ("continuous", "colour-flood")]
    shot_edges = [0] + bounds + [n]
    shots = []
    for a, b in zip(shot_edges[:-1], shot_edges[1:]):
        if b - a <= 0:
            continue
        shots.append({"start": a, "frames": b - a, "t": rnd(a / fps), "sec": rnd((b - a) / fps)})

    # ---------------- motion events and easing ----------------
    inval = np.zeros(n, bool)
    inval[0] = True
    for c in cuts:
        inval[c] = True
    for f_ in flashes:
        inval[f_:f_ + 2] = True
    for s, e in grads:   # fades/dissolves are not moves
        pass
    v = V95.copy()
    v[inval] = np.nan
    vs = v.copy()
    for k in range(1, n - 1):
        w_ = v[k - 1:k + 2]
        if not np.isnan(w_).any():
            vs[k] = np.median(w_)
    valid = vs[~np.isnan(vs)]
    noise = float(np.percentile(valid, 10)) if len(valid) else 0.0
    thr_on = max(0.8, noise * 3)         # px @240 wide per frame
    thr_off = max(0.4, noise * 1.5)
    events = []
    k = 1
    while k < n:
        if not np.isnan(vs[k]) and vs[k] > thr_on:
            a = k
            while a - 1 >= 1 and not np.isnan(vs[a - 1]) and vs[a - 1] > thr_off:
                a -= 1
            b = k
            while b + 1 < n and not np.isnan(vs[b + 1]) and vs[b + 1] > thr_off:
                b += 1
            seg = vs[a:b + 1]
            if len(seg) >= 3:
                pk = int(np.nanargmax(seg))
                pa, pb = max(1, a - 3), min(n, b + 4)
                padv = np.nan_to_num(vs[pa:pb], nan=0.0)
                padv = np.where(np.isnan(v[pa:pb]), padv, np.nan_to_num(v[pa:pb]))   # raw speeds, not smoothed
                best, Dfr, s0, err, rank = fit_ease_model(padv)
                coh = float(np.mean(COH[a:b + 1]))
                zm = float(np.mean(np.abs(ZOOM[a:b + 1])))
                cam = bool(coh > 0.6 and MOVF[a:b + 1].mean() > 0.4)
                events.append({
                    "start": a, "frames": len(seg), "t": rnd(a / fps), "sec": rnd(len(seg) / fps),
                    "peak_pos": rnd(pk / max(1, len(seg) - 1)),
                    "accel_frames": pk, "decel_frames": len(seg) - 1 - pk,
                    "peak_fw_s": rnd(seg.max() / fw * fps), "peak_pct_w_per_frame": rnd(seg.max() / fw * 100, 2),
                    "moving_frac": rnd(float(np.mean(MOVF[a:b + 1]))),
                    "camera": cam,
                    "zoom": bool(cam and zm * fw > 0.6 * float(np.mean(GSPD[a:b + 1]))),
                    "ease": best, "ease_family": ease_family(best), "ease_rmse": rnd(err),
                    "tween_sec_est": rnd(Dfr / fps) if Dfr else None, "tween_frames_est": rnd(Dfr, 1) if Dfr else None,
                    "rank": rank})
            k = b + 1
        else:
            k += 1

    # still holds: nothing moves
    still = (~inval) & (np.nan_to_num(vs, nan=99) < thr_off) & (CH < 0.004)
    holds = []
    k = 0
    while k < n:
        if still[k]:
            a = k
            while k + 1 < n and still[k + 1]:
                k += 1
            if (k - a + 1) / fps >= 0.25:
                holds.append(rnd((k - a + 1) / fps))
        k += 1
    still_frac = float(still.mean())

    # ---------------- colour ----------------
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

    def shot_palette(sh):
        idx = [min(n - 1, sh["start"] + int(sh["frames"] * q)) for q in (0.2, 0.5, 0.8)]
        px = np.concatenate([THUMB[j].reshape(-1, 3) for j in idx]).astype(np.float32)
        K = 6
        _, lab, cen = cv2.kmeans(px, K, None, crit, 2, cv2.KMEANS_PP_CENTERS)
        share = np.bincount(lab.ravel(), minlength=K) / len(lab)
        L = lab_of(cen)
        th = THUMB[idx[1]]
        border = np.concatenate([th[0], th[-1], th[:, 0], th[:, -1]]).astype(np.float32)
        bl = lab_of(border)
        bg_k = int(np.bincount(np.argmin(((bl[:, None, :] - L[None]) ** 2).sum(2), 1), minlength=K).argmax())
        cl = [{"hex": hexc(cen[i]), "lab": L[i], "share": float(share[i])} for i in range(K)]
        return cl, bg_k

    all_cl, bgs = [], []
    for sh in shots:
        cl, bg_k = shot_palette(sh)
        wgt = sh["frames"] / n
        bgs.append({"hex": cl[bg_k]["hex"], "lab": cl[bg_k]["lab"], "L": float(cl[bg_k]["lab"][0]), "weight": wgt})
        for c in cl:
            all_cl.append((c["lab"], c["share"] * wgt, c["hex"]))
    merged = []
    for lab_, wgt, hx in sorted(all_cl, key=lambda x: -x[1]):
        for m in merged:
            if np.linalg.norm(m["lab"] - lab_) < 15:
                m["w"] += wgt
                break
        else:
            merged.append({"lab": lab_, "w": wgt, "hex": hx})
    merged.sort(key=lambda m: -m["w"])
    tot = sum(m["w"] for m in merged) or 1
    palette = [{"hex": m["hex"], "share": rnd(m["w"] / tot), "L": rnd(m["lab"][0], 1),
                "chroma": rnd(math.hypot(m["lab"][1], m["lab"][2]), 1)} for m in merged if m["w"] / tot >= 0.01]
    accents = [p for p in palette if p["chroma"] > 35 and p["share"] < 0.25]
    bgm = []
    for b in bgs:
        for m in bgm:
            if np.linalg.norm(m["lab"] - b["lab"]) < 15:
                m["w"] += b["weight"]
                break
        else:
            bgm.append({"lab": b["lab"], "w": b["weight"], "hex": b["hex"]})
    bgm.sort(key=lambda m: -m["w"])
    bg_L = sum(b["L"] * b["weight"] for b in bgs) / max(1e-9, sum(b["weight"] for b in bgs))
    neutral_share = sum(p["share"] for p in palette if p["chroma"] < 12)

    # ---------------- text ----------------
    text = None
    if ocr is not None or cached is not None:
        per_sample_words, per_sample_disp_words, size_h, line_w = [], [], [], []
        open_ev, done_ev = [], []

        def norm(s_):
            return " ".join(words_of(s_.lower()))

        for smp in ocr_samples:
            disp = [it for it in smp["items"] if it["h"] >= DISPLAY_MIN_H]
            disp = [it for it in disp if words_of(it["t"])]
            allw = sum(len(words_of(it["t"])) for it in smp["items"])
            dw = sum(len(words_of(it["t"])) for it in disp)
            per_sample_words.append(allw); per_sample_disp_words.append(dw)
            if disp:
                size_h.append(max(it["h"] for it in disp) / OCR_BOX_TO_FONT)
                line_w.append(max(it["w"] for it in disp))
            s_txt = norm(" ".join(it["t"] for it in sorted(disp, key=lambda z: (z["y"], z["x"]))))
            matched = False
            if s_txt:
                tb = set(s_txt.split())
                for ev in open_ev:
                    ta = set(ev["last"].split())
                    cont = len(ta & tb) / max(1, min(len(ta), len(tb)))
                    if cont >= 0.6 or SequenceMatcher(None, ev["last"], s_txt).ratio() >= 0.7:
                        ev["last"] = s_txt; ev["end"] = smp["f"]
                        if len(tb) > ev["words"]:
                            ev["words"] = len(tb); ev["full_at"] = smp["f"]
                        if len(s_txt) > len(ev["text"]):
                            ev["text"] = s_txt
                        ev["miss"] = 0
                        ev["hmax"] = max(ev["hmax"], max(it["h"] for it in disp) / OCR_BOX_TO_FONT)
                        matched = True
                        break
                if not matched:
                    open_ev.append({"start": smp["f"], "end": smp["f"], "last": s_txt, "text": s_txt,
                                    "words": len(tb), "full_at": smp["f"], "miss": 0,
                                    "hmax": max(it["h"] for it in disp) / OCR_BOX_TO_FONT})
            still_open = []
            for ev in open_ev:
                if ev["end"] != smp["f"]:
                    ev["miss"] += 1
                if ev["miss"] > 1:
                    done_ev.append(ev)
                else:
                    still_open.append(ev)
            open_ev = still_open
        done_ev += open_ev
        # an OCR misreading of a line (merged/split words mid-build) spawns a short parallel event: drop any event
        # whose letters are contained in a longer event that overlaps it in time
        def _letters(t_):
            return re.sub(r"[^a-z]", "", t_.lower())
        keep_ev = []
        for ev in done_ev:
            le = _letters(ev["text"])
            dup = False
            for o in done_ev:
                if o is ev or (o["end"] - o["start"]) < (ev["end"] - ev["start"]):
                    continue
                if o["start"] - ocr_step <= ev["end"] and ev["start"] <= o["end"] + ocr_step:
                    lo = _letters(o["text"])
                    if le and (le in lo or SequenceMatcher(None, le, lo).ratio() >= 0.8):
                        dup = True
                        break
            if not dup:
                keep_ev.append(ev)
        done_ev = keep_ev
        tev = []
        for ev in done_ev:
            dur = (ev["end"] - ev["start"] + ocr_step) / fps
            if ev["end"] == ev["start"] and ev["words"] <= 1:
                continue   # single-sample OCR flicker
            tev.append({"t": rnd(ev["start"] / fps), "sec": rnd(dur), "words": ev["words"],
                        "build_sec": rnd((ev["full_at"] - ev["start"]) / fps),
                        "size_pct_h": rnd(ev["hmax"] * 100, 2), "text": ev["text"][:80],
                        "sec_per_word": rnd(dur / max(1, ev["words"]))})
        with_txt = [w for w in per_sample_disp_words if w > 0]
        text = {
            "samples": len(ocr_samples), "sample_hz": rnd(fps / ocr_step, 2),
            "display_text_time_frac": rnd(len(with_txt) / max(1, len(ocr_samples))),
            "display_words_on_screen_median": pct(with_txt, 50), "display_words_on_screen_p90": pct(with_txt, 90),
            "display_words_on_screen_max": max(with_txt) if with_txt else 0,
            "all_words_on_screen_median": pct([w for w in per_sample_words if w > 0], 50),
            "font_pct_h_median": rnd(pct(size_h, 50) * 100) if size_h else None,
            "font_pct_h_p90": rnd(pct(size_h, 90) * 100) if size_h else None,
            "font_pct_h_max": rnd(max(size_h) * 100) if size_h else None,
            "line_w_pct_median": rnd(pct(line_w, 50) * 100, 1) if line_w else None,
            "line_w_pct_max": rnd(max(line_w) * 100, 1) if line_w else None,
            "events": sorted(tev, key=lambda e: e["t"]),
        }
        text["event_sec_median"] = rnd(pct([e["sec"] for e in tev], 50))
        text["event_sec_p10"] = rnd(pct([e["sec"] for e in tev], 10))
        text["sec_per_word_median"] = rnd(pct([e["sec_per_word"] for e in tev], 50))
        text["sec_per_word_p10"] = rnd(pct([e["sec_per_word"] for e in tev], 10))
        text["words_per_event_median"] = pct([e["words"] for e in tev], 50)
        text["frames"] = ocr_samples

    # ---------------- audio ----------------
    audio = {"present": False}
    if info["has_audio"]:
        try:
            audio = analyze_audio(path, [t["frame"] / fps for t in transitions if t["kind"] != "continuous"], fps, use_hf)
        except Exception as ex:
            audio = {"present": True, "error": repr(ex)}

    # ---------------- summary ----------------
    sl = [s["sec"] for s in shots]
    ev_el = [e for e in events if not e["camera"]]
    ev_cam = [e for e in events if e["camera"]]
    clean = [e for e in ev_el if e["ease_rmse"] is not None and e["ease_rmse"] < 0.15]

    def count(lst):
        c = {}
        for x in lst:
            c[x] = c.get(x, 0) + 1
        return dict(sorted(c.items(), key=lambda x: -x[1]))

    kinds = count([t["kind"] for t in transitions])
    valid_mask = ~inval
    summary = {
        "file": os.path.relpath(path).replace("\\", "/"),
        "group": os.path.basename(os.path.dirname(os.path.abspath(path))),
        "fps": rnd(fps, 3), "w": W0, "h": H0, "frames": n, "sec": rnd(n / fps, 2),
        "shots": len(shots), "cuts_per_min": rnd(len(bounds) / (n / fps) * 60, 1),
        "shot_sec_median": rnd(pct(sl, 50)), "shot_sec_mean": rnd(float(np.mean(sl))),
        "shot_sec_p10": rnd(pct(sl, 10)), "shot_sec_p90": rnd(pct(sl, 90)),
        "shot_sec_min": rnd(min(sl)), "shot_sec_max": rnd(max(sl)),
        "shot_frames_min": min(s["frames"] for s in shots),
        "transitions": kinds, "flash_frames": len(flashes),
        "hard_cut_share": rnd(sum(v_ for k_, v_ in kinds.items() if k_.startswith("hard")) / max(1, len(transitions))),
        "moving_frac_median": rnd(pct(MOVF[valid_mask], 50)), "moving_frac_p90": rnd(pct(MOVF[valid_mask], 90)),
        "changed_frac_median": rnd(pct(CH[valid_mask], 50)),
        "still_time_frac": rnd(still_frac), "hold_sec_median": rnd(pct(holds, 50)), "hold_sec_p90": rnd(pct(holds, 90)),
        "n_holds": len(holds),
        "moves_per_sec": rnd(len(events) / (n / fps), 2),
        "move_frames_median": pct([e["frames"] for e in ev_el], 50),
        "move_frames_p10": pct([e["frames"] for e in ev_el], 10), "move_frames_p90": pct([e["frames"] for e in ev_el], 90),
        "move_sec_median": rnd(pct([e["sec"] for e in ev_el], 50)),
        "tween_sec_est_median": rnd(pct([e["tween_sec_est"] for e in ev_el], 50)),
        "move_peak_fw_s_median": rnd(pct([e["peak_fw_s"] for e in ev_el], 50)),
        "move_peak_fw_s_p90": rnd(pct([e["peak_fw_s"] for e in ev_el], 90)),
        "move_peak_pos_median": rnd(pct([e["peak_pos"] for e in ev_el], 50)),
        "camera_moves": len(ev_cam), "camera_move_sec_median": rnd(pct([e["sec"] for e in ev_cam], 50)),
        "camera_peak_fw_s_median": rnd(pct([e["peak_fw_s"] for e in ev_cam], 50)),
        "ease_families": count([e["ease_family"] for e in ev_el]),
        "eases": count([e["ease"] for e in ev_el]),
        "linear_share": rnd(sum(1 for e in ev_el if e["ease"] == "linear") / max(1, len(ev_el))),
        # moves whose speed profile fits one GSAP ease cleanly (rmse < 0.15): one designed tween, not overlap/footage
        "clean_moves": len(clean),
        "clean_share": {f_: rnd(sum(1 for e in clean if e["ease_family"] == f_) / max(1, len(clean)))
                        for f_ in ("out", "inOut", "in", "linear")},
        "clean_tween_sec_median": rnd(pct([e["tween_sec_est"] for e in clean], 50)),
        "clean_out_tween_sec_median": rnd(pct([e["tween_sec_est"] for e in clean if e["ease_family"] == "out"], 50)),
        "clean_top_ease": max(set(e["ease"] for e in clean), key=[e["ease"] for e in clean].count) if clean else None,
        "palette_n": len(palette), "palette_core_n": sum(1 for p in palette if p["share"] >= 0.05),
        "palette": palette[:12], "accents": accents[:4], "neutral_share": rnd(neutral_share),
        "backgrounds": [{"hex": m["hex"], "share": rnd(m["w"])} for m in bgm[:5]],
        "n_backgrounds": sum(1 for m in bgm if m["w"] >= 0.05),
        "bg_L_mean": rnd(bg_L, 1), "lum_mean": rnd(float(LUM.mean())),
        "audio": audio,
    }
    if text:
        summary["text"] = {k_: v_ for k_, v_ in text.items() if k_ not in ("events", "frames")}
    result = {"summary": summary, "shots": shots, "transitions": transitions, "moves": events,
              "holds": holds, "text_events": text["events"] if text else [],
              "per_frame": {"hist_d": rnd(D.tolist(), 4), "changed": rnd(CH.tolist(), 4), "v97": rnd(V95.tolist(), 3),
                            "moving": rnd(MOVF.tolist(), 3), "coh": rnd(COH.tolist(), 3), "lum": rnd(LUM.tolist(), 3)},
              "ocr_frames": text["frames"] if text else []}
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(path))[0]
        with open(os.path.join(out_dir, base + ".json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)
        if sheets:
            make_sheets(path, result, os.path.join(out_dir, base), fps, n)
    return result


# ----------------------------------------------------------------------------- contact sheets

def _label(img, txt):
    cv2.rectangle(img, (0, 0), (img.shape[1], 16), (0, 0, 0), -1)
    cv2.putText(img, txt, (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def _grid(tiles, cols, tw, th):
    rows = max(1, math.ceil(len(tiles) / cols))
    sheet = np.full((rows * th, cols * tw, 3), 40, np.uint8)
    for k, t in enumerate(tiles):
        r, c = divmod(k, cols)
        sheet[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = t
    return sheet


def make_sheets(path, res, prefix, fps, n):
    tw = 320
    info = probe(path)
    th = int(round(tw * info["h"] / info["w"] / 2) * 2)
    want = set()
    shot_idx = [min(n - 1, s["start"] + s["frames"] // 2) for s in res["shots"]]
    want.update(shot_idx)
    step = max(1, int(round(fps / 2)))
    want.update(range(0, n, step))
    trans = res["transitions"][:60]
    sheet_frames = []
    for t in trans:
        if t["frames"] <= 1:
            fr = [t["frame"] + d for d in (-3, -2, -1, 0, 1, 2)]
        else:
            s = int(round(t["start"] * fps)); e = int(round(t["end"] * fps))
            fr = [int(round(s - 1 + (e - s + 2) * q / 5)) for q in range(6)]
        fr = [min(n - 1, max(0, f)) for f in fr]
        sheet_frames.append(fr)
        want.update(fr)
    got = {i: f.copy() for i, f in frames(path, tw, th, keep=want)}
    tiles = [_label(got[j].copy(), f"#{k} {s['t']:.2f}s  {s['sec']:.2f}s/{s['frames']}f")
             for k, (s, j) in enumerate(zip(res["shots"], shot_idx)) if j in got]
    for part in range(0, len(tiles), 72):
        cv2.imwrite(prefix + f"_shots{part // 72}.jpg", _grid(tiles[part:part + 72], 6, tw, th), [cv2.IMWRITE_JPEG_QUALITY, 82])
    tiles = [_label(got[j].copy(), f"{j / fps:.1f}s") for j in range(0, n, step) if j in got]
    for part in range(0, len(tiles), 96):
        cv2.imwrite(prefix + f"_time{part // 96}.jpg", _grid(tiles[part:part + 96], 8, tw, th), [cv2.IMWRITE_JPEG_QUALITY, 80])
    tiles = []
    for t, fr in zip(trans, sheet_frames):
        for q, f in enumerate(fr):
            if f in got:
                tiles.append(_label(got[f].copy(), (f"{t['kind'][:18]} {t['t']:.2f}" if q == 0 else f"f{f}")))
    for part in range(0, len(tiles), 72):
        cv2.imwrite(prefix + f"_trans{part // 72}.jpg", _grid(tiles[part:part + 72], 6, tw, th), [cv2.IMWRITE_JPEG_QUALITY, 80])


# ----------------------------------------------------------------------------- aggregate

AGG_KEYS = ["sec", "shots", "cuts_per_min", "shot_sec_median", "shot_sec_mean", "shot_sec_p10", "shot_sec_p90",
            "shot_sec_min", "hard_cut_share", "flash_frames", "moving_frac_median", "moving_frac_p90", "still_time_frac",
            "hold_sec_median", "hold_sec_p90", "moves_per_sec", "move_frames_median", "move_frames_p10",
            "move_frames_p90", "move_sec_median", "tween_sec_est_median", "move_peak_fw_s_median",
            "move_peak_fw_s_p90", "move_peak_pos_median", "linear_share", "clean_moves", "clean_share.out",
            "clean_share.inOut", "clean_share.in", "clean_share.linear", "clean_tween_sec_median", "clean_out_tween_sec_median", "camera_moves", "camera_move_sec_median",
            "camera_peak_fw_s_median", "palette_n", "palette_core_n", "neutral_share", "n_backgrounds", "bg_L_mean",
            "text.display_text_time_frac", "text.display_words_on_screen_median", "text.display_words_on_screen_p90",
            "text.display_words_on_screen_max", "text.font_pct_h_median", "text.font_pct_h_p90", "text.font_pct_h_max",
            "text.line_w_pct_max", "text.event_sec_median", "text.event_sec_p10", "text.sec_per_word_median",
            "text.sec_per_word_p10", "text.words_per_event_median", "audio.bpm", "audio.pulse_clarity",
            "audio.cuts.within_2f_beat", "audio.cuts.chance_within_2f_beat", "audio.cuts.within_2f_halfbeat",
            "audio.cuts.chance_within_2f_halfbeat", "audio.cuts.within_2f_hit", "audio.cuts.chance_within_2f_hit",
            "audio.cuts.median_abs_offset_beat_frames", "audio.cuts.phase_lock_R", "audio.cuts.phase_lock_R_chance",
            "audio.cuts.within_2f_of_locked_grid", "audio.cuts.within_2f_of_locked_halfgrid", "audio.shot_len_beats_median", "audio.shot_len_integer_beats_share"]


def dig(d, key):
    for k in key.split("."):
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def _shares(lst, top=None):
    c = {}
    for x in lst:
        c[x] = c.get(x, 0) + 1
    tot = max(1, len(lst))
    items = sorted(c.items(), key=lambda x: -x[1])
    if top:
        items = items[:top]
    return {str(k): rnd(v / tot) for k, v in items}


def _q(lst, qs=(10, 25, 50, 75, 90), n=3):
    return [rnd(pct(lst, q), n) for q in qs]


def _hold_by_words(te):
    out = {}
    for lo, hi, nm in [(1, 2, "1-2"), (3, 4, "3-4"), (5, 7, "5-7"), (8, 99, "8+")]:
        s = [e["sec"] for e in te if lo <= e["words"] <= hi]
        if s:
            out[nm] = {"n": len(s), "p10": rnd(pct(s, 10)), "p25": rnd(pct(s, 25)), "median": rnd(pct(s, 50))}
    return out


def aggregate(paths, out=None):
    rows = [json.load(open(p, encoding="utf-8")) for p in paths]
    groups = {}
    for r in rows:
        groups.setdefault(r["summary"]["group"], []).append(r)
    groups["all"] = rows
    stats = {}
    for g, rs in groups.items():
        st = {}
        for k in AGG_KEYS:
            vals = [dig(r["summary"], k) for r in rs]
            vals = [v for v in vals if isinstance(v, (int, float))]
            if vals:
                st[k] = {"p10": rnd(pct(vals, 10)), "median": rnd(pct(vals, 50)), "p90": rnd(pct(vals, 90)), "n": len(vals)}
        shots = [s["sec"] for r in rs for s in r["shots"]]
        mv = [m for r in rs for m in r["moves"] if not m["camera"]]
        cl = [m for m in mv if m.get("ease_rmse") is not None and m["ease_rmse"] < 0.15]
        cam = [m for r in rs for m in r["moves"] if m["camera"]]
        te = [e for r in rs for e in r["text_events"]]
        st["pooled"] = {
            "shot_sec": _q(shots),
            "move_sec": _q([m["sec"] for m in mv]),
            "move_frames_at30": _q([m["sec"] * 30 for m in mv], n=1),
            "tween_sec_est": _q([m["tween_sec_est"] for m in mv if m["tween_sec_est"]]),
            "move_peak_fw_s": _q([m["peak_fw_s"] for m in mv]),
            "move_peak_pos": _q([m["peak_pos"] for m in mv]),
            "clean_ease_family_share": _shares([m["ease_family"] for m in cl]),
            "clean_ease_share": _shares([m["ease"] for m in cl], top=10),
            "clean_tween_sec_by_family": {f_: _q([m["tween_sec_est"] for m in cl if m["ease_family"] == f_])
                                          for f_ in ("out", "inOut", "in")},
            "clean_peak_fw_s_by_family": {f_: _q([m["peak_fw_s"] for m in cl if m["ease_family"] == f_])
                                          for f_ in ("out", "inOut", "in")},
            "n_clean_moves": len(cl),
            "camera_sec": _q([m["sec"] for m in cam]),
            "camera_peak_fw_s": _q([m["peak_fw_s"] for m in cam]),
            "ease_family_share": _shares([m["ease_family"] for m in mv]),
            "ease_share": _shares([m["ease"] for m in mv], top=8),
            "camera_ease_family_share": _shares([m["ease_family"] for m in cam]),
            "transition_share": _shares([t["kind"] for r in rs for t in r["transitions"]]),
            "gradual_transition_frames": _q([t["frames"] for r in rs for t in r["transitions"] if t["frames"] > 1 and t["kind"] != "continuous"], n=1),
            "text_event_sec": _q([e["sec"] for e in te]),
            "text_event_words": _q([e["words"] for e in te], n=1),
            "text_size_pct_h": _q([e["size_pct_h"] for e in te], n=2),
            "text_build_sec": _q([e["build_sec"] for e in te if e["build_sec"] > 0], (10, 50, 90)),
            "hold_by_words": _hold_by_words(te),
            "still_hold_sec": _q([h for r in rs for h in r["holds"]]),
            "n_shots": len(shots), "n_moves": len(mv), "n_camera": len(cam), "n_text_events": len(te),
        }
        stats[g] = st
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=1)
        md = [f"# Aggregate ({len(rows)} videos)\n"]
        gnames = [g for g in groups if g != "all"] + ["all"]
        md.append("| metric | " + " | ".join(f"{g} p10 / med / p90" for g in gnames) + " |")
        md.append("|---|" + "---|" * len(gnames))
        for k in AGG_KEYS:
            cells = []
            for g in gnames:
                s = stats[g].get(k)
                cells.append(f"{s['p10']} / **{s['median']}** / {s['p90']}" if s else "-")
            md.append(f"| {k} | " + " | ".join(cells) + " |")
        md.append("\n## Pooled distributions (p10, p25, p50, p75, p90)\n")
        for g in gnames:
            md.append(f"### {g}\n")
            for k, v in stats[g]["pooled"].items():
                md.append(f"- **{k}**: {v}")
            md.append("")
        md.append("\n## Per video\n")
        md.append("| video | sec | fps | shots | shot med s | cuts/min | hard% | moving | still | move f med | peak fw/s | top ease | palette | bg L | disp words med | font %H med/max | text s med | bpm | cut<=2f beat (chance) |")
        md.append("|" + "---|" * 20)
        for r in rows:
            s = r["summary"]; t = s.get("text", {}); a = s.get("audio", {}); c = a.get("cuts", {}) if isinstance(a, dict) else {}
            top = next(iter(s["eases"]), "-")
            md.append(f"| {os.path.basename(s['file'])} | {s['sec']} | {s['fps']} | {s['shots']} | {s['shot_sec_median']} | {s['cuts_per_min']} | "
                      f"{s['hard_cut_share']} | {s['moving_frac_median']} | {s['still_time_frac']} | {s['move_frames_median']} | "
                      f"{s['move_peak_fw_s_median']} | {top} | {s['palette_n']} | {s['bg_L_mean']} | {t.get('display_words_on_screen_median')} | "
                      f"{t.get('font_pct_h_median')}/{t.get('font_pct_h_max')} | {t.get('event_sec_median')} | {a.get('bpm')} | "
                      f"{c.get('within_2f_beat')} ({c.get('chance_within_2f_beat')}) |")
        with open(os.path.splitext(out)[0] + ".md", "w", encoding="utf-8") as f:
            f.write("\n".join(md))
    return stats


# ----------------------------------------------------------------------------- checks

def load_rules(path):
    with open(path or DEFAULT_RULES, encoding="utf-8") as f:
        return json.load(f)


def check_video(path, profile, rules_path=None, out_dir=None):
    rules = load_rules(rules_path)
    prof = rules["profiles"][profile]
    res = analyze(path, out_dir=out_dir, sheets=bool(out_dir), use_ocr=True)
    s = res["summary"]
    lines, fails = [], 0
    for r in prof["video"]:
        val = dig(s, r["metric"])
        lo, hi = r.get("min"), r.get("max")
        bad = val is not None and ((lo is not None and val < lo) or (hi is not None and val > hi))
        tag = "n/a" if val is None else ("ok" if not bad else ("WARN" if r.get("level") == "warn" else "FAIL"))
        fails += tag == "FAIL"
        lines.append(f"[{tag:4}] {r['id']:<24} {r['metric']} = {val}   pros {lo}..{hi}   {r.get('why', '')}")
    f = 1 / s["fps"]
    R = prof["read"]
    for e in res["text_events"]:
        if e["size_pct_h"] < R["applies_from_font_pct_h"] or e["words"] > R["max_words"]:
            continue    # product UI text is not copy the viewer must read
        floor = R["floor_base"] + R["floor_per_word"] * e["words"]
        target = R["target_base"] + R["target_per_word"] * e["words"]
        if e["sec"] + f < floor:
            lines.append(f"[FAIL] text-hold t={e['t']}s '{e['text'][:40]}' {e['words']}w held {e['sec']}s < floor {floor:.2f}s")
            fails += 1
        elif e["sec"] + f < target:
            lines.append(f"[WARN] text-hold t={e['t']}s '{e['text'][:40]}' {e['words']}w held {e['sec']}s < pros' median {target:.2f}s")
    sh_min = prof["plan"].get("shot_min_sec")
    if sh_min:
        short = [x for x in res["shots"][1:-1] if x["sec"] < sh_min]
        if short:
            lines.append(f"[WARN] {len(short)} shots shorter than {sh_min}s: " + ", ".join(f"{x['t']}s({x['sec']})" for x in short[:8]))
    print(f"# check {path} against '{profile}'")
    print("\n".join(lines))
    print(f"\n{fails} FAIL")
    return fails, res


def check_stills(pngs, profile, rules_path=None):
    rules = load_rules(rules_path)
    prof = rules["profiles"][profile]["still"]
    ocr = get_ocr()
    if ocr is None:
        print("WARN: rapidocr_onnxruntime not installed; text checks skipped (pip install rapidocr-onnxruntime)")
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    fails = 0
    for p in pngs:
        img = cv2.imread(p)
        if img is None:
            print(f"[skip] {p}")
            continue
        h, w = img.shape[:2]
        img9 = cv2.resize(img, (ANA_W, int(round(ANA_W * h / w))), interpolation=cv2.INTER_AREA)
        hh, ww = img9.shape[:2]
        notes, items = [], []
        if ocr:
            r, _ = ocr(img9)
            for box, txt, conf in (r or []):
                if float(conf) < 0.6:
                    continue
                b = np.array(box, float)
                items.append({"t": txt, "h": (b[:, 1].max() - b[:, 1].min()) / hh,
                              "x0": b[:, 0].min() / ww, "x1": b[:, 0].max() / ww,
                              "y0": b[:, 1].min() / hh, "y1": b[:, 1].max() / hh})
        disp = [i for i in items if i["h"] >= DISPLAY_MIN_H]
        disp = [i for i in disp if words_of(i["t"])]
        words = sum(len(words_of(i["t"])) for i in disp)
        if words > prof["max_display_words"]:
            notes.append(f"FAIL {words} display words on screen > {prof['max_display_words']}")
        m = (1 - prof["title_safe"]) / 2
        for i in items:
            fs = i["h"] / OCR_BOX_TO_FONT * 100
            if fs < prof["min_font_pct_h"]:
                notes.append(f"WARN text '{i['t'][:24]}' font ~{fs:.1f}%H < {prof['min_font_pct_h']}%H (ok only if it is product UI)")
            if i["h"] >= DISPLAY_MIN_H and (i["x0"] < m or i["x1"] > 1 - m or i["y0"] < m or i["y1"] > 1 - m):
                notes.append(f"FAIL text '{i['t'][:24]}' outside {int(prof['title_safe'] * 100)}% title-safe")
        big = max([i["h"] for i in disp], default=0) / OCR_BOX_TO_FONT * 100
        if disp and big > prof["max_font_pct_h"]:
            notes.append(f"WARN headline ~{big:.1f}%H > {prof['max_font_pct_h']}%H")
        sm = cv2.resize(img, (160, int(round(160 * h / w))), interpolation=cv2.INTER_AREA)
        px = sm.reshape(-1, 3).astype(np.float32)
        _, lab, cen = cv2.kmeans(px, 8, None, crit, 2, cv2.KMEANS_PP_CENTERS)
        share = np.bincount(lab.ravel(), minlength=8) / len(lab)
        L = lab_of(cen)
        merged = []
        for k in np.argsort(-share):
            for m_ in merged:
                if np.linalg.norm(m_[0] - L[k]) < 15:
                    m_[1] += share[k]
                    break
            else:
                merged.append([L[k], share[k], hexc(cen[k])])
        cols = [m_ for m_ in merged if m_[1] >= 0.02]
        accents = [m_ for m_ in cols if math.hypot(m_[0][1], m_[0][2]) > 35 and m_[1] < 0.25]
        if len(cols) > prof["max_colors"]:
            notes.append(f"WARN {len(cols)} distinct colours >= 2% of frame (pros: <= {prof['max_colors']})")
        if len(accents) > prof["max_accents"]:
            notes.append(f"WARN {len(accents)} saturated accents (pros: <= {prof['max_accents']}): " + " ".join(a[2] for a in accents))
        acc_share = sum(a[1] for a in accents)
        if acc_share > prof["max_accent_share"]:
            notes.append(f"WARN accent covers {acc_share:.0%} of frame (pros: <= {prof['max_accent_share']:.0%})")
        if float(img.mean()) < 4:
            notes.append("FAIL frame is black")
        nf = sum(1 for x in notes if x.startswith("FAIL"))
        fails += nf
        status = "FAIL" if nf else ("WARN" if notes else "ok")
        print(f"[{status:4}] {os.path.basename(p)}  words={words} headline~{big:.1f}%H colours={len(cols)} "
              f"[{' '.join(c[2] for c in cols[:6])}]")
        for x in notes:
            print("        " + x)
    print(f"\n{fails} FAIL")
    return fails


# ----------------------------------------------------------------------------- plan check (before building)

def check_plan(plan_path, rules_path=None):
    """Check the master prompt's shot list (JSON) against the measured rules before anything is built.
    Plan format (frames at plan fps):
    {"profile": "launch", "fps": 30, "frames": 900, "bpm": 110.2, "beat_offset_s": 0.41,
     "shots": [{"id": "hook", "start": 0, "end": 64, "in": "hard-cut",
                "text": [{"copy": "Notes that write themselves", "start": 8, "end": 64, "font_pct_h": 7}],
                "moves": [{"what": "title", "role": "enter", "frames": 12, "ease": "expo.out"}]}]}"""
    rules = load_rules(rules_path)
    plan = json.load(open(plan_path, encoding="utf-8"))
    prof = rules["profiles"][plan["profile"]]
    P = prof["plan"]
    fps = plan["fps"]
    out, fails = [], 0

    def bad(msg, level="FAIL"):
        nonlocal fails
        fails += level == "FAIL"
        out.append(f"[{level}] {msg}")

    shots = plan["shots"]
    if shots[0]["start"] != 0:
        bad(f"first shot starts at frame {shots[0]['start']}, not 0")
    for a, b in zip(shots, shots[1:]):
        if a["end"] != b["start"]:
            bad(f"gap/overlap between {a['id']} (end {a['end']}) and {b['id']} (start {b['start']})")
    if shots[-1]["end"] != plan["frames"]:
        bad(f"last shot ends at {shots[-1]['end']}, film is {plan['frames']} frames")
    lens = [(s_["end"] - s_["start"]) / fps for s_ in shots]
    med = float(np.median(lens))
    lo, hi = P["shot_median_sec"]
    if not lo <= med <= hi:
        bad(f"median shot {med:.2f}s outside pros' {lo}..{hi}s", "WARN")
    for s_, L in zip(shots[:-1], lens[:-1]):
        if L < P["shot_min_sec"]:
            bad(f"shot {s_['id']} lasts {L:.2f}s < {P['shot_min_sec']}s", "WARN")
        if L > P["shot_max_sec"]:
            bad(f"shot {s_['id']} lasts {L:.2f}s > {P['shot_max_sec']}s with no cut (fine only if the camera keeps travelling)", "WARN")
    if lens[-1] < P["end_hold_sec"]:
        bad(f"end card/last shot holds {lens[-1]:.2f}s < {P['end_hold_sec']}s")
    kinds = [s_.get("in", "hard-cut") for s_ in shots[1:]]
    if kinds:
        hc = sum(1 for k in kinds if k.startswith("hard")) / len(kinds)
        lo, hi = P["hard_cut_share"]
        if not lo <= hc <= hi:
            bad(f"hard-cut share {hc:.0%} outside pros' {lo:.0%}..{hi:.0%}", "WARN")
        nk = len(set(k.split(":")[0] for k in kinds))
        if nk < P["transition_kinds"][0] or nk > P["transition_kinds"][1]:
            bad(f"{nk} kinds of transition; pros use {P['transition_kinds'][0]}..{P['transition_kinds'][1]}", "WARN")
        nd = sum(1 for k in kinds if k in ("dissolve", "crossfade"))
        if nd / len(kinds) > P["dissolve_share_max"]:
            bad(f"{nd} dissolves/crossfades between scenes; pros keep it <= {P['dissolve_share_max']:.0%}", "WARN")
    # text
    for s_ in shots:
        for t in s_.get("text", []):
            w = len(words_of(t["copy"]))
            dur = (t["end"] - t["start"]) / fps
            R = prof["read"]
            floor = R["floor_base"] + R["floor_per_word"] * w
            target = R["target_base"] + R["target_per_word"] * w
            if t.get("ui"):
                pass   # product UI text, not read word by word
            elif dur < floor:
                bad(f"text '{t['copy'][:40]}' ({w} words) on screen {dur:.2f}s < floor {floor:.2f}s")
            elif dur < target and not t.get("kinetic"):
                bad(f"text '{t['copy'][:40]}' ({w} words) on screen {dur:.2f}s < pros' median {target:.2f}s", "WARN")
            if w > P["max_words_on_screen"]:
                bad(f"text '{t['copy'][:40]}' has {w} words on screen > {P['max_words_on_screen']}")
            fp = t.get("font_pct_h")
            if fp is not None and not P["font_pct_h"][0] <= fp <= P["font_pct_h"][1]:
                bad(f"text '{t['copy'][:30]}' at {fp}%H outside {P['font_pct_h'][0]}..{P['font_pct_h'][1]}%H", "WARN")
    # moves
    for s_ in shots:
        for m in s_.get("moves", []):
            role = m.get("role", "enter")
            R = P["moves"].get(role)
            if not R:
                continue
            if not R["frames30"][0] <= m["frames"] * 30 / fps <= R["frames30"][1]:
                bad(f"{s_['id']}/{m.get('what', '?')} {role} takes {m['frames']}f; pros {R['frames30'][0]}..{R['frames30'][1]}f @30fps", "WARN")
            if m.get("ease") and m["ease"] not in R["eases"]:
                bad(f"{s_['id']}/{m.get('what', '?')} {role} uses {m['ease']}; pros use {', '.join(R['eases'])}", "WARN")
    # beat
    if plan.get("bpm"):
        period = 60 / plan["bpm"] * fps
        off = plan.get("beat_offset_s", 0) * fps
        tol = P["beat_tolerance_frames"]
        offs = []
        for s_ in shots[1:]:
            k = (s_["start"] - off) / period
            d_full = (k - round(k)) * period
            d_half = (k * 2 - round(k * 2)) * period / 2
            offs.append(d_full)
            if abs(d_half) > tol and plan.get("cut_to_music"):
                bad(f"cut into {s_['id']} at f{s_['start']} is {d_full:+.1f}f from the beat ({d_half:+.1f}f from a half beat)")
        if offs:
            on = sum(1 for d in offs if abs(d) <= tol) / len(offs)
            out.append(f"[info] {on:.0%} of cuts within ±{tol}f of a beat (cut_to_music={bool(plan.get('cut_to_music'))})")
            if plan.get("cut_to_music") and on < P["beat_share_min"]:
                bad(f"only {on:.0%} of cuts land on the beat", "WARN")
        for s_ in shots:
            if s_.get("downbeat"):
                k = (s_["start"] - off) / (period * plan.get("beats_per_bar", 4))
                d = (k - round(k)) * period * plan.get("beats_per_bar", 4)
                if abs(d) > tol:
                    bad(f"{s_['id']} is marked to land on a downbeat but starts {d:+.1f}f from the bar line")
    print(f"# plan {plan_path}: {len(shots)} shots, {plan['frames'] / fps:.1f}s, profile {plan['profile']}")
    print("\n".join(out) if out else "[ok] no findings")
    print(f"\n{fails} FAIL")
    return fails


# ----------------------------------------------------------------------------- beat grid for a new film

def beat_grid(audio_path, fps=30, beats_per_bar=4, offset=None, bpm=None, duration=None):
    """Beat/bar grid in frames for the master prompt. Each beat frame is computed from its index
    (never by adding a rounded beat repeatedly), so it never drifts."""
    y, sr = audio_wav(audio_path)
    dur = duration or len(y) / sr
    src = "given"
    if bpm is None:
        hf = hf_beats(audio_path)
        if hf:
            bpm, beats = hf; src = "hyperframes"
        else:
            env, rate = onset_envelope(y, sr)
            bpm, beats, _ = track_beats(env, rate); src = "builtin"
        if offset is None and beats:
            period = 60 / bpm
            ph = np.angle(np.mean(np.exp(2j * np.pi * (np.array(beats) % period) / period)))
            offset = (ph / (2 * np.pi) * period) % period
    offset = offset or 0.0
    period = 60.0 / bpm
    # downbeat: the beat phase (mod beats_per_bar) with the strongest low-frequency onsets
    env, rate = onset_envelope(y, sr)
    nb = int((dur - offset) / period) + 1
    strength = np.zeros(beats_per_bar)
    for i in range(nb):
        j = int(round((offset + i * period) * rate))
        if 0 <= j < len(env):
            strength[i % beats_per_bar] += env[max(0, j - 2):j + 3].max()
    bar_shift = int(np.argmax(strength))
    offset = offset + bar_shift * period
    if offset - period * beats_per_bar >= -1e-6:
        offset -= period * beats_per_bar * int(offset // (period * beats_per_bar))
    n = int((dur - offset) / period) + 1
    rows = []
    for i in range(n):
        t = offset + i * period
        rows.append({"beat": i, "bar": i // beats_per_bar + 1, "beat_in_bar": i % beats_per_bar + 1,
                     "t": round(t, 3), "frame": int(round(t * fps))})
    print(f"# {os.path.basename(audio_path)}  bpm={bpm:.2f} ({src})  first beat={offset:.3f}s  "
          f"frames/beat={fps * period:.2f}  frames/bar={fps * period * beats_per_bar:.2f}  @ {fps} fps")
    print("bar  beat  t(s)     frame")
    for r in rows:
        mark = "  <- bar" if r["beat_in_bar"] == 1 else ""
        print(f"{r['bar']:>3}  {r['beat_in_bar']:>4}  {r['t']:7.3f}  {r['frame']:>5}{mark}")
    return {"bpm": bpm, "offset": offset, "fps": fps, "beats": rows}


# ----------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze"); a.add_argument("video"); a.add_argument("--out", default="measure")
    a.add_argument("--sheets", action="store_true"); a.add_argument("--no-ocr", action="store_true")
    a.add_argument("--no-hf-beats", action="store_true")
    a.add_argument("--reuse-ocr", action="store_true", help="take OCR samples from an existing <out>/<name>.json")
    g = sub.add_parser("aggregate"); g.add_argument("json", nargs="+"); g.add_argument("--out", default="aggregate.json")
    c = sub.add_parser("check"); c.add_argument("video"); c.add_argument("--profile", required=True, choices=["launch", "intro"])
    c.add_argument("--rules"); c.add_argument("--out")
    s = sub.add_parser("stills"); s.add_argument("png", nargs="+"); s.add_argument("--profile", required=True, choices=["launch", "intro"])
    s.add_argument("--rules")
    pl = sub.add_parser("plan"); pl.add_argument("plan_json"); pl.add_argument("--rules")
    gr = sub.add_parser("grid"); gr.add_argument("audio"); gr.add_argument("--fps", type=float, default=30)
    gr.add_argument("--bpm", type=float); gr.add_argument("--offset", type=float); gr.add_argument("--beats-per-bar", type=int, default=4)
    gr.add_argument("--json")
    args = ap.parse_args()
    if args.cmd == "analyze":
        prev = os.path.join(args.out, os.path.splitext(os.path.basename(args.video))[0] + ".json")
        r = analyze(args.video, args.out, args.sheets, not args.no_ocr, not args.no_hf_beats,
                    reuse_ocr=prev if args.reuse_ocr else None)
        print(json.dumps(r["summary"], indent=1, ensure_ascii=False))
    elif args.cmd == "aggregate":
        aggregate(args.json, args.out)
        print("wrote", args.out)
    elif args.cmd == "check":
        fails, _ = check_video(args.video, args.profile, args.rules, args.out)
        sys.exit(1 if fails else 0)
    elif args.cmd == "plan":
        sys.exit(1 if check_plan(args.plan_json, args.rules) else 0)
    elif args.cmd == "grid":
        g_ = beat_grid(args.audio, args.fps, args.beats_per_bar, args.offset, args.bpm)
        if args.json:
            json.dump(g_, open(args.json, "w"), indent=1)
    elif args.cmd == "stills":
        import glob
        files = [f for p in args.png for f in (glob.glob(p) or [p])]
        sys.exit(1 if check_stills(files, args.profile, args.rules) else 0)


if __name__ == "__main__":
    main()
