"""
Video Repurposing Bot — REST API (Flask)

Endpoints:
  GET  /                    -> simple HTML upload form (for manual/browser testing)
  GET  /api/health          -> health check
  GET  /api/platforms       -> list available platform presets
  POST /api/repurpose       -> upload a video, get back processed file(s)

POST /api/repurpose expects multipart/form-data:
  video        (file, required)
  platforms    (one or more form fields, e.g. platforms=tiktok&platforms=youtube)
  captions     ("true"/"false", optional, default "false")

Response:
  - If exactly one platform and no captions requested: returns the video file
    directly (video/mp4).
  - Otherwise: returns a ZIP of all requested outputs (application/zip).

Designed to run on Render's free web service tier (512MB RAM), so it
enforces limits on input duration/size and uses a small Whisper model.
"""

import io
import shutil
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, request, jsonify, send_file, render_template_string

from repurpose.presets import PRESETS, get_preset
from repurpose.resize import resize_video, probe
from repurpose.captions import transcribe_to_srt, burn_captions

# Free-tier guardrails (512MB RAM on Render free web service).
MAX_DURATION_S = 45
MAX_FILE_MB = 40
CAPTION_MODEL = "base"

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_MB * 1024 * 1024


UPLOAD_FORM_HTML = """
<!doctype html>
<html>
<head>
  <title>Video Repurposing Bot</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; }
    h1 { font-size: 1.4rem; }
    label { display: block; margin-top: 16px; font-weight: 600; }
    .platforms label { display: inline-block; font-weight: normal; margin-right: 12px; }
    button { margin-top: 20px; padding: 10px 18px; font-size: 1rem; cursor: pointer; }
    .note { color: #666; font-size: 0.9rem; margin-top: 8px; }
    footer { margin-top: 40px; font-size: 0.85rem; color: #888; }
  </style>
</head>
<body>
  <h1>🎬 Video Repurposing Bot</h1>
  <p>Upload a video, pick platforms, get resized/captioned versions back.</p>
  <p class="note">Free-tier limits: videos under {{ max_duration }}s and {{ max_size }}MB.</p>

  <form action="/api/repurpose" method="post" enctype="multipart/form-data">
    <label for="video">Video file</label>
    <input type="file" id="video" name="video" accept="video/*" required>

    <label>Platforms</label>
    <div class="platforms">
      {% for p in platforms %}
        <label><input type="checkbox" name="platforms" value="{{ p }}" {% if p == 'tiktok' %}checked{% endif %}> {{ p }}</label>
      {% endfor %}
    </div>

    <label><input type="checkbox" name="captions" value="true"> Add auto-generated captions (slower)</label>

    <button type="submit">Repurpose video</button>
  </form>

  <footer>
    REST API also available directly:
    <code>POST /api/repurpose</code>, <code>GET /api/platforms</code>, <code>GET /api/health</code>.
    <a href="https://github.com/YOUR_USERNAME/video-repurposing-bot">Source code</a>
  </footer>
</body>
</html>
"""


def _has_allowed_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template_string(
        UPLOAD_FORM_HTML,
        platforms=list(PRESETS.keys()),
        max_duration=MAX_DURATION_S,
        max_size=MAX_FILE_MB,
    )


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/platforms")
def list_platforms():
    return jsonify({
        name: {
            "width": p.width,
            "height": p.height,
            "mode": p.mode,
            "max_duration_s": p.max_duration_s,
        }
        for name, p in PRESETS.items()
    })


@app.route("/api/repurpose", methods=["POST"])
def repurpose():
    if "video" not in request.files:
        return jsonify({"error": "No 'video' file in request."}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not _has_allowed_extension(video_file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}"}), 400

    platforms = request.form.getlist("platforms")
    if not platforms:
        return jsonify({"error": "Provide at least one 'platforms' value."}), 400
    invalid = [p for p in platforms if p not in PRESETS]
    if invalid:
        return jsonify({"error": f"Unknown platform(s): {invalid}. Valid: {list(PRESETS)}"}), 400

    add_captions = request.form.get("captions", "false").lower() == "true"

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        src = tmp / Path(video_file.filename).name
        video_file.save(src)

        try:
            info = probe(src)
        except Exception as e:
            return jsonify({"error": f"Could not read video: {e}"}), 400

        if info["duration"] > MAX_DURATION_S:
            return jsonify({
                "error": f"Video is {info['duration']:.0f}s. Limit is {MAX_DURATION_S}s on this free-tier API."
            }), 413

        outputs = []
        try:
            for platform_name in platforms:
                preset = get_preset(platform_name)
                resized_path = tmp / f"{src.stem}_{platform_name}_resized.mp4"
                resize_video(src, resized_path, preset)
                current = resized_path

                if add_captions:
                    srt_path = tmp / f"{src.stem}_{platform_name}.srt"
                    transcribe_to_srt(current, srt_path, model_size=CAPTION_MODEL)
                    captioned_path = tmp / f"{src.stem}_{platform_name}_captioned.mp4"
                    burn_captions(current, srt_path, captioned_path)
                    current = captioned_path

                final_path = tmp / f"{src.stem}_{platform_name}_final.mp4"
                shutil.copy2(current, final_path)
                outputs.append((platform_name, final_path))
        except Exception as e:
            return jsonify({"error": f"Processing failed: {e}"}), 500

        # Single output, no zip needed.
        if len(outputs) == 1:
            platform_name, path = outputs[0]
            return send_file(
                path,
                mimetype="video/mp4",
                as_attachment=True,
                download_name=f"{src.stem}_{platform_name}.mp4",
            )

        # Multiple outputs -> zip them.
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for platform_name, path in outputs:
                zf.write(path, arcname=f"{src.stem}_{platform_name}.mp4")
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{src.stem}_repurposed.zip",
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
