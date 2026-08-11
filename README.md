# Video Repurposing Bot

![Tests](https://github.com/YOUR_USERNAME/video-repurposing-bot/actions/workflows/tests.yml/badge.svg)

FFmpeg-based tool that resizes/crops a video for TikTok, Instagram Reels,
YouTube Shorts, and horizontal YouTube. Includes two applied-ML pieces on
top of plain video processing:

- **Auto-generated captions** — local speech-to-text (faster-whisper /
  OpenAI Whisper) transcribes the audio, then burns short, readable
  captions into the video.
- **Smart crop** — instead of blindly cropping to the center when
  reformatting to a narrower aspect ratio, an OpenCV face detector finds
  the subject and shifts the crop window toward them, so speakers don't
  get cut off.

Two ways to use it:
- **`main.py`** — CLI, for local/batch processing with no size limits.
- **`streamlit_app.py`** — web app with upload/download UI, deployable free
  on Streamlit Community Cloud.

## Live demo

[Add your deployed Streamlit Community Cloud link here]

## How it works

```
                 ┌─────────────┐
   video in ───▶ │   ffprobe   │  inspect: dimensions, duration, audio
                 └──────┬──────┘
                        │
        ┌───────────────┼────────────────┐
        │ (optional)                      │
        ▼                                 ▼
┌────────────────┐              ┌───────────────────┐
│  smart_crop.py  │              │   resize.py        │
│  OpenCV face     │──offset──▶  │   ffmpeg scale +    │
│  detection       │              │   crop / pad        │
└────────────────┘              └─────────┬───────────┘
                                            │
                       ┌────────────────────┼───────────────────┐
                       │ (optional, --captions)                   │
                       ▼                                           │
              ┌──────────────────┐                                │
              │  captions.py      │                                │
              │  Whisper transcribe│                               │
              │  → SRT → burn-in   │                                │
              └──────────┬─────────┘                                │
                          │                                         │
                          ▼                                         ▼
                                platform-ready .mp4 output(s)
```

### Smart crop, in more detail

A blind center-crop (the usual approach when reformatting 16:9 → 9:16) cuts
off subjects that aren't centered in frame. `repurpose/smart_crop.py`:

1. Samples frames from the source video at a fixed interval (not every
   frame — keeps it fast and CPU-only friendly).
2. Runs a Haar cascade face detector (bundled with OpenCV, no extra model
   download) on each sampled frame.
3. Takes the **median** of detected face centers across all samples as a
   single, stable crop offset for the whole clip — deliberately a static
   offset rather than frame-by-frame tracking, which keeps the ffmpeg
   filter graph simple (a plain `crop=w:h:x:y` instead of a dynamic
   per-frame expression) while still meaningfully improving on a naive
   center-crop for typical talking-head content.
4. Falls back to dead-center automatically if no face is found anywhere —
   identical to the original behavior, so it never makes things worse.

## Local setup

```bash
pip install -r requirements.txt
```
Also install ffmpeg: https://ffmpeg.org/download.html

### CLI usage
```bash
python main.py -i input.mp4 -o output/ --platforms tiktok reels shorts
python main.py -i videos/ -o output/ --platforms tiktok --captions
python main.py -i input.mp4 -o output/ --platforms tiktok --smart-crop
```

### Web app locally
```bash
streamlit run streamlit_app.py
```
Opens at http://localhost:8501

## Testing

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests cover the pure logic (preset lookup, ffmpeg filter-string
construction including crop-offset math and clamping, SRT timestamp
formatting) plus the smart-crop fallback behavior (no face found / file
missing → degrades to center-crop rather than erroring). A GitHub Actions
workflow (`.github/workflows/tests.yml`) runs the full suite on every push
and pull request.

## Deploying the web app (free)

Streamlit Community Cloud is the free host used here — Hugging Face
Spaces now requires a paid plan for Gradio/Docker Spaces on CPU, so
this project uses Streamlit instead.

1. Push this repo to GitHub (public).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick this repo/branch, set **Main file path** to
   `streamlit_app.py`.
4. Click **Deploy**. First build takes a few minutes (installs ffmpeg via
   `packages.txt` plus Python deps from `requirements.txt`).
5. You get a public URL like `https://your-app-name.streamlit.app`.
6. Streamlit Cloud auto-redeploys on every push to `main` — no manual
   redeploy step needed.

Free tier limits: about 1GB RAM, app sleeps after roughly 12 hours of no
traffic (wakes up on next visit, takes about 30 seconds). The app enforces
video length/size caps (`MAX_DURATION_S`, `MAX_FILE_MB` in
`streamlit_app.py`) to stay within that.

## Platform presets

| Platform | Canvas    | Fit mode             | Max duration |
|----------|-----------|-----------------------|---------------|
| tiktok   | 1080x1920 | crop-fill              | 10 min        |
| reels    | 1080x1920 | crop-fill              | 90s           |
| shorts   | 1080x1920 | crop-fill              | 60s           |
| youtube  | 1920x1080 | pad-fit (letterbox)    | none          |
| square   | 1080x1080 | crop-fill              | none          |

Edit `repurpose/presets.py` to add platforms or change dimensions/duration caps.

## Project structure

```
video_repurposing_bot/
├── main.py                  # CLI entry point
├── streamlit_app.py         # web app entry point
├── conftest.py               # pytest import path setup
├── packages.txt              # apt deps for Streamlit Cloud (ffmpeg)
├── .streamlit/config.toml    # upload size limit
├── repurpose/
│   ├── presets.py            # platform canvas/duration definitions
│   ├── resize.py              # ffmpeg crop/pad logic
│   ├── captions.py            # whisper transcription + caption burn-in
│   ├── smart_crop.py          # OpenCV face-detection based crop offset
│   └── metadata.py            # title/description tag writing
├── tests/
│   ├── test_presets.py
│   ├── test_resize.py
│   ├── test_captions.py
│   └── test_smart_crop.py
├── .github/workflows/tests.yml  # CI: runs pytest on push/PR
├── requirements.txt
└── requirements-dev.txt
```

## Possible resume framing

> Built and deployed an end-to-end video-processing pipeline (Python,
> FFmpeg, OpenCV, Whisper) that reformats video for TikTok/Reels/Shorts,
> applies OpenCV face detection to choose a smarter crop than a naive
> center-crop, and auto-generates burned-in captions via local
> speech-to-text — with a pytest suite and CI (GitHub Actions), deployed
> as a public web app on Streamlit Community Cloud.

## Notes

This tool focuses on legitimate repurposing — reformatting your own video
for different platform aspect ratios and adding captions. It does not
include features aimed at evading platform spam/duplicate-content
detection systems.

