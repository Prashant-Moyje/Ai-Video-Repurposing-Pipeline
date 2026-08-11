# Video Repurposing Bot

FFmpeg-based tool that resizes/crops a video for TikTok, Instagram Reels,
YouTube Shorts, and horizontal YouTube — with optional auto-generated,
burned-in captions (local speech-to-text via faster-whisper).

Two ways to use it:
- **`main.py`** — CLI, for local/batch processing with no size limits.
- **`streamlit_app.py`** — web app with upload/download UI, deployable free
  on Streamlit Community Cloud.

## Live demo

[Add your deployed Streamlit Community Cloud link here once live]

## Local setup

```bash
pip install -r requirements.txt
```
Also install ffmpeg: https://ffmpeg.org/download.html

### CLI usage
```bash
python main.py -i input.mp4 -o output/ --platforms tiktok reels shorts
python main.py -i videos/ -o output/ --platforms tiktok --captions
```

### Web app locally
```bash
streamlit run streamlit_app.py
```
Opens at http://localhost:8501

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
├── main.py                 # CLI entry point
├── streamlit_app.py        # web app entry point
├── packages.txt            # apt deps for Streamlit Cloud (ffmpeg)
├── .streamlit/config.toml  # upload size limit
├── repurpose/
│   ├── presets.py          # platform canvas/duration definitions
│   ├── resize.py           # ffmpeg crop/pad logic
│   ├── captions.py         # whisper transcription + caption burn-in
│   └── metadata.py         # title/description tag writing
└── requirements.txt
```

## Notes

This tool focuses on legitimate repurposing — reformatting your own video
for different platform aspect ratios and adding captions. It does not
include features aimed at evading platform spam/duplicate-content
detection systems.
