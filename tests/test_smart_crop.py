import subprocess
import shutil

import pytest

from repurpose.smart_crop import detect_face_center_offset


def _make_blank_video(path, width=320, height=180, duration_s=1):
    """Generate a tiny solid-color test video with ffmpeg (no faces in it)."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=gray:s={width}x{height}:d={duration_s}:r=10",
            str(path),
        ],
        check=True, capture_output=True,
    )


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_no_face_falls_back_to_center(tmp_path):
    video_path = tmp_path / "blank.mp4"
    _make_blank_video(video_path)

    x, y = detect_face_center_offset(video_path)
    assert (x, y) == (0.5, 0.5)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_offset_is_normalized_range(tmp_path):
    video_path = tmp_path / "blank2.mp4"
    _make_blank_video(video_path)

    x, y = detect_face_center_offset(video_path)
    assert 0.0 <= x <= 1.0
    assert 0.0 <= y <= 1.0


def test_missing_file_falls_back_gracefully(tmp_path):
    # OpenCV can't open a nonexistent file — should degrade to center, not crash.
    x, y = detect_face_center_offset(tmp_path / "does_not_exist.mp4")
    assert (x, y) == (0.5, 0.5)
