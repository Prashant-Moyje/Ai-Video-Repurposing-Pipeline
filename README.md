# 🎥 Video Repurposing Bot

An AI-powered video processing application that automatically reframes long-form content for social media platforms (TikTok, Instagram Reels, YouTube Shorts), applies computer vision-based smart cropping, and burns in accurate audio captions using speech-to-text transcription.

🚀 **[Live Demo on Streamlit](https://video-repurposing-bot-zbvg35gxvwgtgqrczqyyvr.streamlit.app/)**

---

## ✨ Features

- **Smart Crop (OpenCV):** Uses face detection to automatically center subject framing during aspect ratio conversion (16:9 to 9:16).
- **Automated Captions (Whisper):** Transcribes speech and burns SRT subtitles directly into the generated video output.
- **Platform Presets:** Built-in settings for TikTok, Instagram Reels, YouTube Shorts, and square format videos.
- **Dual Support:** Use via command-line interface (CLI) for batch operations or Streamlit UI for web interaction.
- **CI & Automated Testing:** Covered by a full `pytest` suite and GitHub Actions workflow.

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Frontend / Framework:** Streamlit
- **AI & Computer Vision:** OpenAI Whisper, OpenCV
- **Media Processing:** FFmpeg, MoviePy
- **DevOps:** GitHub Actions, Streamlit Community Cloud

---

## ⚙️ How It Works

```text
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

## ⚡ Quick Start

### Prerequisites
Ensure [FFmpeg](https://ffmpeg.org/download.html) is installed on your system.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Prashant-Moyje/video-repurposing-bot.git
   cd video-repurposing-bot
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   - **Streamlit Web App:**
     ```bash
     streamlit run streamlit_app.py
     ```
   - **CLI Batch Mode:**
     ```bash
     python main.py -i input.mp4 -o output/ --platforms tiktok --smart-crop
     ```

---

## 📊 Platform Presets

| Platform | Canvas | Fit Mode | Max Duration |
|---|---|---|---|
| **TikTok** | 1080x1920 | Crop-fill | 10 min |
| **Reels** | 1080x1920 | Crop-fill | 90s |
| **Shorts** | 1080x1920 | Crop-fill | 60s |
| **YouTube** | 1920x1080 | Pad-fit (letterbox) | Unlimited |
| **Square** | 1080x1080 | Crop-fill | Unlimited |

---

## 📁 Project Structure

```text
video_repurposing_bot/
├── main.py               # CLI Entry Point
├── streamlit_app.py      # Streamlit Web App Entry Point
├── repurpose/            # Core Processing Package
│   ├── smart_crop.py     # OpenCV Face Detection Logic
│   ├── captions.py       # Whisper Transcription & Burn-in
│   ├── resize.py         # FFmpeg Resizing Logic
│   └── presets.py        # Platform Dimensions & Parameters
├── tests/                # Pytest Test Suite
└── requirements.txt      # Project Dependencies
```
