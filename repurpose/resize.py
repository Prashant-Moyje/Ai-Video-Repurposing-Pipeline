"""FFmpeg-based resizing/cropping for a target platform preset."""

import json
import subprocess
from pathlib import Path

from .presets import Preset


def probe(video_path: Path) -> dict:
    """Return basic stream info (width, height, duration, has_audio) via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_streams", "-show_format",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio_stream = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if video_stream is None:
        raise ValueError(f"No video stream found in {video_path}")

    return {
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "duration": float(data["format"].get("duration", 0.0)),
        "has_audio": audio_stream is not None,
    }


def build_video_filter(src_w: int, src_h: int, preset: Preset) -> str:
    """Build the ffmpeg -vf filter string to fit src dimensions onto preset canvas."""
    tw, th = preset.width, preset.height

    if preset.mode == "crop_fill":
        # Scale so the video covers the canvas, then crop the overflow from center.
        return (
            f"scale={tw}:{th}:force_original_aspect_ratio=increase,"
            f"crop={tw}:{th}"
        )
    elif preset.mode == "pad_fit":
        # Scale to fit inside the canvas, pad remainder with black (letterbox).
        return (
            f"scale={tw}:{th}:force_original_aspect_ratio=decrease,"
            f"pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:color=black"
        )
    else:
        raise ValueError(f"Unknown fit mode: {preset.mode}")


def resize_video(
    src: Path,
    dst: Path,
    preset: Preset,
    trim_to_max_duration: bool = True,
    extra_vf: str | None = None,
) -> None:
    """Resize/crop `src` to fit `preset` and write to `dst`."""
    info = probe(src)
    vf = build_video_filter(info["width"], info["height"], preset)
    if extra_vf:
        vf = f"{vf},{extra_vf}"

    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-b:v", preset.video_bitrate,
        "-pix_fmt", "yuv420p",
    ]

    if info["has_audio"]:
        cmd += ["-c:a", "aac", "-b:a", preset.audio_bitrate]
    else:
        cmd += ["-an"]

    if trim_to_max_duration and preset.max_duration_s:
        cmd += ["-t", str(preset.max_duration_s)]

    cmd += [str(dst)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
