# 🎥 AI Video Repurposing Pipeline

**One long video in → platform-ready vertical clips out, with the subject kept in frame and captions already burned in.**

Cutting a 20-minute talk into TikToks by hand means re-cropping every shot so the speaker isn't sliced off, then typing subtitles. This does both automatically: OpenCV face detection drives the crop window, Whisper writes the captions, FFmpeg renders to each platform's exact spec.

<!-- TODO: Replace with a real GIF — 16:9 source on the left, 9:16 captioned output on the right.
     This is the single highest-value addition to this README. Save it to docs/demo.gif.
     A 5-second loop is enough. -->
![Before and after: 16:9 source reframed to 9:16 with burned-in captions](docs/demo.gif)

<!-- TODO: Replace WORKFLOW_FILE with your actual workflow filename from .github/workflows/
     (e.g. ci.yml or tests.yml). Delete this badge if the workflow is currently failing. -->
[![CI](https://github.com/Prashant-Moyje/Ai-Video-Repurposing-Pipeline/actions/workflows/WORKFLOW_FILE/badge.svg)](https://github.com/Prashant-Moyje/Ai-Video-Repurposing-Pipeline/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

🚀 **[Try it in your browser](https://video-repurposing-bot-zbvg35gxvwgtgqrczqyyvr.streamlit.app/)** — no install needed.

```bash
python main.py -i talk.mp4 -o clips/ --platforms tiktok reels --smart-crop --captions
```

**Built for:** podcasters, course creators, and anyone repurposing long-form video who doesn't want to open a video editor.

---

## ✨ Features

- **Smart crop (OpenCV)** — Face detection picks the crop window during aspect-ratio conversion, so the speaker stays centred instead of drifting off the edge of a 9:16 frame.
- **Automatic captions (Whisper)** — Transcribes the audio, generates an SRT, and burns the subtitles into the output video.
- **Platform presets** — Correct canvas size, fit mode, and duration cap for TikTok, Instagram Reels, YouTube Shorts, YouTube, and square.
- **CLI *and* web UI** — `main.py` for scripted batch runs, `streamlit_app.py` for a point-and-click interface.
- **Tested** — `pytest` suite run on every push via GitHub Actions.

---

## 🛠️ Tech stack

| Layer | Tools |
| --- | --- |
| Language | Python 3.10+ |
| Web UI | Streamlit |
| AI / computer vision | OpenAI Whisper, OpenCV |
| Media processing | FFmpeg, MoviePy |
| CI / hosting | GitHub Actions, Streamlit Community Cloud |

---

## ⚙️ How it works

```
                  ┌─────────────┐
   video in ───▶  │   ffprobe   │  inspect: dimensions, duration, audio
                  └──────┬──────┘
                         │
         ┌───────────────┼────────────────┐
         │ (optional)                     │
         ▼                                ▼
┌────────────────┐               ┌───────────────────┐
│ smart_crop.py  │               │     resize.py     │
│ OpenCV face    │──offset──▶    │   ffmpeg scale +  │
│ detection      │               │   crop / pad      │
└────────────────┘               └─────────┬─────────┘
                                           │
                         ┌─────────────────┼───────────────────┐
                         │ (optional, --captions)              │
                         ▼                                     │
                ┌──────────────────┐                           │
                │   captions.py    │                           │
                │ Whisper transcribe                           │
                │ → SRT → burn-in  │                           │
                └──────────┬───────┘                           │
                           │                                   │
                           ▼                                   ▼
                             platform-ready .mp4 output(s)
```

---

## ⚡ Quick start

### Prerequisites

[FFmpeg](https://ffmpeg.org/download.html) must be installed and on your `PATH`. Check with:

```bash
ffmpeg -version
```

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/Prashant-Moyje/Ai-Video-Repurposing-Pipeline.git
cd Ai-Video-Repurposing-Pipeline
```

**2. Create and activate a virtual environment**

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

### Run it

Web app:

```bash
streamlit run streamlit_app.py
```

CLI:

```bash
python main.py -i input.mp4 -o output/ --platforms tiktok --smart-crop
```

<!-- TODO: Add a full CLI flag reference here (or link to `python main.py --help` output).
     Right now a user has to read main.py to discover the available options. -->

---

## 📊 Platform presets

| Platform | Canvas | Fit mode | Max duration |
| --- | --- | --- | --- |
| **TikTok** | 1080×1920 | Crop-fill | 10 min |
| **Reels** | 1080×1920 | Crop-fill | 90 s |
| **Shorts** | 1080×1920 | Crop-fill | 60 s |
| **YouTube** | 1920×1080 | Pad-fit (letterbox) | Unlimited |
| **Square** | 1080×1080 | Crop-fill | Unlimited |

---

## ⏱️ Performance notes

<!-- TODO: Replace the bracketed placeholders with numbers from an actual run on your machine.
     Concrete figures here prevent users from assuming the tool has hung. -->

- **Resizing alone** is fast — roughly [X]× realtime, since FFmpeg does the work.
- **Captions are the slow part.** Whisper transcription on CPU runs at roughly [X]× realtime, so a 20-minute video can take [X] minutes before any output appears. This is expected, not a hang.
- Default Whisper model: **[base / small / medium]**. Smaller models are faster and less accurate; change this in `repurpose/captions.py`.
- A GPU, if available, cuts transcription time substantially.

---

## 📁 Project structure

```
Ai-Video-Repurposing-Pipeline/
├── main.py               # CLI entry point
├── streamlit_app.py      # Streamlit web app entry point
├── repurpose/            # Core processing package
│   ├── smart_crop.py     # OpenCV face detection logic
│   ├── captions.py       # Whisper transcription and burn-in
│   ├── resize.py         # FFmpeg resizing logic
│   └── presets.py        # Platform dimensions and parameters
├── tests/                # Pytest suite
├── conftest.py           # Shared pytest fixtures
├── packages.txt          # System (apt) dependencies for Streamlit Cloud — installs FFmpeg
├── requirements.txt      # Runtime dependencies
└── requirements-dev.txt  # Development and test dependencies
```

---

## 🧪 Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 🗺️ Roadmap

<!-- TODO: Keep this honest and short. An accurate three-item roadmap signals an active project;
     a long aspirational list signals an abandoned one. Delete this section if you'd rather
     not commit to anything. -->

- [ ] Multi-speaker tracking (currently follows a single detected face)
- [ ] Automatic highlight detection to pick clip-worthy segments
- [ ] Caption styling options (font, position, colour)

---

## 🤝 Contributing

Issues and pull requests are welcome. For substantial changes, please open an issue first to discuss the approach.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

<!-- TODO: The repository currently has no LICENSE file. Without one, the default is
     all-rights-reserved and nobody may legally use or fork this. Add one via
     GitHub: Add file → Create new file → type "LICENSE" → "Choose a license template" → MIT. -->
