"""
Platform output presets.

Each preset defines the target canvas for a platform. `mode` controls how the
source video is fit onto that canvas:
  - "crop_fill": scale to cover the canvas, then center-crop overflow (no bars,
    but edges may be cut off). Good default for vertical shorts/reels/tiktok.
  - "pad_fit":   scale to fit inside the canvas, then pad the remainder
    (e.g. blurred background or solid color). Nothing gets cropped.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    name: str
    width: int
    height: int
    mode: str  # "crop_fill" or "pad_fit"
    max_duration_s: int | None = None  # None = no limit
    video_bitrate: str = "6M"
    audio_bitrate: str = "128k"


PRESETS: dict[str, Preset] = {
    "tiktok": Preset(
        name="tiktok",
        width=1080,
        height=1920,
        mode="crop_fill",
        max_duration_s=600,
    ),
    "reels": Preset(
        name="reels",
        width=1080,
        height=1920,
        mode="crop_fill",
        max_duration_s=90,
    ),
    "shorts": Preset(
        name="shorts",
        width=1080,
        height=1920,
        mode="crop_fill",
        max_duration_s=60,
    ),
    "youtube": Preset(
        name="youtube",
        width=1920,
        height=1080,
        mode="pad_fit",
        max_duration_s=None,
    ),
    "square": Preset(
        name="square",
        width=1080,
        height=1080,
        mode="crop_fill",
        max_duration_s=None,
    ),
}


def get_preset(name: str) -> Preset:
    try:
        return PRESETS[name.lower()]
    except KeyError:
        valid = ", ".join(PRESETS)
        raise ValueError(f"Unknown platform '{name}'. Valid options: {valid}")
