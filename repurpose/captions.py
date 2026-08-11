"""
Auto-caption generation.

Uses faster-whisper (local, offline speech-to-text) to transcribe the video's
audio track, writes an SRT file, then burns the captions into the video with
ffmpeg's `subtitles` filter using a bold, center-bottom style similar to
common short-form-video captions.

Install: pip install faster-whisper
The first run downloads a whisper model (requires internet once); after that
it runs fully offline.
"""

import subprocess
from pathlib import Path


def _format_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe_to_srt(
    video_path: Path,
    srt_path: Path,
    model_size: str = "small",
    language: str | None = None,
    max_words_per_caption: int = 6,
) -> None:
    """
    Transcribe `video_path` and write short, punchy caption chunks to `srt_path`.

    max_words_per_caption keeps each on-screen caption short (readable at a
    glance), which is the standard style for TikTok/Reels/Shorts captions.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise ImportError(
            "faster-whisper is required for captions. Install with:\n"
            "  pip install faster-whisper --break-system-packages"
        ) from e

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        str(video_path), language=language, word_timestamps=True
    )

    entries = []
    for segment in segments:
        words = segment.words or []
        if not words:
            continue
        chunk = []
        for word in words:
            chunk.append(word)
            if len(chunk) >= max_words_per_caption:
                entries.append(chunk)
                chunk = []
        if chunk:
            entries.append(chunk)

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(entries, start=1):
            start = chunk[0].start
            end = chunk[-1].end
            text = " ".join(w.word.strip() for w in chunk)
            f.write(f"{i}\n")
            f.write(f"{_format_timestamp(start)} --> {_format_timestamp(end)}\n")
            f.write(f"{text}\n\n")


def burn_captions(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
    font_size: int = 18,
) -> None:
    """Burn `srt_path` captions into `video_path`, writing `output_path`."""
    # force_style controls the look: bold white text, black outline, centered
    # near the bottom third of the frame (Alignment=2 is bottom-center in ASS).
    style = (
        f"FontName=Arial,FontSize={font_size},Bold=1,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=80"
    )
    # Escape path for the subtitles filter (colons/backslashes need escaping).
    srt_escaped = str(srt_path).replace("\\", "\\\\").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"subtitles='{srt_escaped}':force_style='{style}'",
        "-c:v", "libx264", "-preset", "medium",
        "-c:a", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
