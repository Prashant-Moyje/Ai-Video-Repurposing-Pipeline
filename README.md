# Video Repurposing Bot — REST API

![Docker build](https://github.com/YOUR_USERNAME/video-repurposing-bot/actions/workflows/docker-publish.yml/badge.svg)
[![Docker Hub](https://img.shields.io/docker/pulls/YOUR_DOCKERHUB_USERNAME/video-repurposing-bot)](https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/video-repurposing-bot)

FFmpeg-based REST API that resizes/crops a video for TikTok, Instagram
Reels, YouTube Shorts, and horizontal YouTube — with optional
auto-generated, burned-in captions (local speech-to-text via
faster-whisper). Built with Flask, deployable free on Render.

Two ways to use it:
- **`main.py`** — CLI, for local/batch processing with no size limits.
- **`app.py`** — Flask REST API with a minimal HTML upload form for
  manual testing, deployable via Docker.

## Live demo

[Add your deployed Render URL here once live]

## API reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Simple HTML upload form (browser testing) |
| `/api/health` | GET | Health check, returns `{"status": "ok"}` |
| `/api/platforms` | GET | Lists platform presets and their specs |
| `/api/repurpose` | POST | Upload a video, get processed output(s) back |

### `POST /api/repurpose`

`multipart/form-data` body:
- `video` (file, required)
- `platforms` (one or more values, e.g. `tiktok`, `youtube`, `reels`, `shorts`, `square`)
- `captions` (`"true"` or `"false"`, optional, default `false`)

Response:
- One platform, no captions requested → returns the `.mp4` file directly.
- Multiple platforms → returns a `.zip` containing all outputs.
- Errors return JSON with an `error` field and an appropriate HTTP status
  (`400` bad input, `413` video too long, `500` processing failure).

Example with curl:
```bash
curl -X POST https://your-app.onrender.com/api/repurpose \
  -F "video=@myvideo.mp4" \
  -F "platforms=tiktok" \
  -F "platforms=youtube" \
  -F "captions=true" \
  -o result.zip
```

## Local setup

```bash
pip install -r requirements.txt
```
Also install ffmpeg locally: https://ffmpeg.org/download.html

### CLI usage
```bash
python main.py -i input.mp4 -o output/ --platforms tiktok reels shorts
python main.py -i videos/ -o output/ --platforms tiktok --captions
```

### Run the API locally
```bash
python app.py
```
Opens at http://localhost:5000 — visit it in a browser for the upload
form, or hit `/api/*` endpoints directly.

### Run with Docker locally (matches production exactly)
```bash
docker build -t video-repurposing-bot .
docker run -p 5000:5000 video-repurposing-bot
```

## Publishing the Docker image (Docker Hub, free)

A GitHub Actions workflow (`.github/workflows/docker-publish.yml`) builds
this image and pushes it to Docker Hub automatically on every push to
`main`, tagged both `:latest` and `:<commit-sha>`.

### One-time setup

1. Create a free account at https://hub.docker.com if you don't have one.
2. Create an **Access Token**: Docker Hub → Account Settings → **Security**
   → **New Access Token**. Copy it (you won't see it again).
3. In your GitHub repo: **Settings** → **Secrets and variables** →
   **Actions** → **New repository secret**. Add two secrets:
   - `DOCKERHUB_USERNAME` — your Docker Hub username
   - `DOCKERHUB_TOKEN` — the access token from step 2
4. Push to `main`. Check the **Actions** tab on GitHub to watch the build.
5. Once it succeeds, your image is public at:
   `docker.io/<your-dockerhub-username>/video-repurposing-bot`

Anyone (including you, from any machine) can then run it with:
```bash
docker pull <your-dockerhub-username>/video-repurposing-bot
docker run -p 5000:5000 <your-dockerhub-username>/video-repurposing-bot
```

### Testing the build locally first

Before relying on CI, confirm the image actually builds on your machine:
```bash
docker build -t video-repurposing-bot .
docker run -p 5000:5000 video-repurposing-bot
curl http://localhost:5000/api/health
```

## Deploying to Render (free)

Render's free web service tier runs Docker containers, which is how we
get ffmpeg installed reliably (via `Dockerfile`, since Render's free tier
doesn't support Streamlit-Cloud-style `packages.txt`).

1. Push this repo to GitHub (public or private).
2. Go to https://dashboard.render.com → **New** → **Web Service**.
3. Connect your GitHub repo.
4. Render should auto-detect the `Dockerfile`. If asked:
   - **Environment**: Docker
   - **Plan**: Free
   - **Health Check Path**: `/api/health`
5. Click **Create Web Service**. First build takes several minutes
   (installs ffmpeg + Python deps inside the container).
6. You get a public URL like `https://video-repurposing-bot.onrender.com`.

Alternatively, if this repo includes `render.yaml`, you can use Render's
**Blueprint** deploy flow to set it up from that file automatically.

### Free tier notes

- ~512MB RAM — this is why captions use the small `base` Whisper model
  and why `MAX_DURATION_S` / `MAX_FILE_MB` in `app.py` are conservative.
- The service **spins down after ~15 minutes of no traffic** and takes
  30-50s to wake up on the next request (cold start). This is normal for
  Render's free tier, not a bug.
- Only one worker process (`gunicorn ... --workers 1`) to keep memory
  usage predictable — fine for a portfolio demo, not for real traffic.

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
├── app.py                  # Flask REST API
├── main.py                 # CLI entry point
├── Dockerfile               # for local Docker runs + Render deployment
├── render.yaml               # Render blueprint config
├── repurpose/
│   ├── presets.py           # platform canvas/duration definitions
│   ├── resize.py             # ffmpeg crop/pad logic
│   ├── captions.py           # whisper transcription + caption burn-in
│   └── metadata.py           # title/description tag writing
└── requirements.txt
```

## Notes

This tool focuses on legitimate repurposing — reformatting your own video
for different platform aspect ratios and adding captions. It does not
include features aimed at evading platform spam/duplicate-content
detection systems.
