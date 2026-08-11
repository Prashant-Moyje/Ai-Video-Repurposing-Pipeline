"""Write standard metadata tags (title, description) onto an output video."""

import subprocess
from pathlib import Path


def apply_metadata(
    video_path: Path,
    output_path: Path,
    title: str | None = None,
    description: str | None = None,
) -> None:
    """Copy `video_path` to `output_path` with metadata tags set (no re-encode)."""
    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-map", "0", "-c", "copy"]
    if title:
        cmd += ["-metadata", f"title={title}"]
    if description:
        cmd += ["-metadata", f"description={description}", "-metadata", f"comment={description}"]
    cmd += [str(output_path)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
