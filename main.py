#!/usr/bin/env python3
"""
Video Repurposing Bot
======================
Resize/crop a video (or a whole folder of videos) into platform-ready
versions for TikTok, Instagram Reels, YouTube Shorts, and horizontal YouTube
— with optional auto-generated burned-in captions.

Usage:
    python main.py -i input.mp4 -o output/ --platforms tiktok reels shorts
    python main.py -i videos/ -o output/ --platforms tiktok --captions
    python main.py -i input.mp4 -o output/ --platforms youtube --title "My video" --description "..."

Requires: ffmpeg + ffprobe on PATH. For --captions: `pip install faster-whisper`.
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from repurpose.presets import PRESETS, get_preset
from repurpose.resize import resize_video
from repurpose.captions import transcribe_to_srt, burn_captions
from repurpose.metadata import apply_metadata

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def gather_inputs(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        files = sorted(
            p for p in input_path.iterdir()
            if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
        )
        if not files:
            raise FileNotFoundError(f"No video files found in {input_path}")
        return files
    raise FileNotFoundError(f"Input path not found: {input_path}")


def process_one(
    src: Path,
    out_dir: Path,
    platforms: list[str],
    add_captions: bool,
    caption_model: str,
    title: str | None,
    description: str | None,
    smart_crop: bool = False,
) -> None:
    print(f"\n== {src.name} ==")
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        crop_center = (0.5, 0.5)
        if smart_crop:
            from repurpose.smart_crop import detect_face_center_offset
            print("  detecting face position for smart crop...")
            crop_center = detect_face_center_offset(src)
            print(f"  smart crop offset: x={crop_center[0]:.2f}, y={crop_center[1]:.2f}")

        for platform_name in platforms:
            preset = get_preset(platform_name)
            stem = src.stem
            resized_path = tmp / f"{stem}_{platform_name}_resized.mp4"

            print(f"  [{platform_name}] resizing to {preset.width}x{preset.height} "
                  f"({preset.mode})...")
            resize_video(src, resized_path, preset, crop_center=crop_center)

            current = resized_path

            if add_captions:
                print(f"  [{platform_name}] transcribing audio for captions "
                      f"(model={caption_model})...")
                srt_path = tmp / f"{stem}_{platform_name}.srt"
                transcribe_to_srt(current, srt_path, model_size=caption_model)

                captioned_path = tmp / f"{stem}_{platform_name}_captioned.mp4"
                print(f"  [{platform_name}] burning in captions...")
                burn_captions(current, srt_path, captioned_path)
                current = captioned_path

            final_path = out_dir / f"{stem}_{platform_name}.mp4"
            if title or description:
                print(f"  [{platform_name}] writing metadata...")
                apply_metadata(current, final_path, title=title, description=description)
            else:
                shutil.copy2(current, final_path)

            print(f"  [{platform_name}] -> {final_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repurpose a video (or folder of videos) for multiple platforms."
    )
    parser.add_argument("-i", "--input", required=True, type=Path,
                         help="Path to a video file or a folder of videos.")
    parser.add_argument("-o", "--output", required=True, type=Path,
                         help="Output folder for repurposed videos.")
    parser.add_argument("--platforms", nargs="+", default=["tiktok"],
                         choices=list(PRESETS.keys()),
                         help=f"Target platforms. Options: {', '.join(PRESETS)}")
    parser.add_argument("--captions", action="store_true",
                         help="Auto-generate and burn in captions (requires faster-whisper).")
    parser.add_argument("--caption-model", default="small",
                         help="Whisper model size: tiny, base, small, medium, large-v3. "
                              "Bigger = more accurate but slower.")
    parser.add_argument("--title", default=None, help="Metadata title tag for outputs.")
    parser.add_argument("--description", default=None, help="Metadata description tag.")
    parser.add_argument("--smart-crop", action="store_true",
                         help="Use face detection (OpenCV) to choose a better crop offset "
                              "than a blind center-crop, for crop-fill platforms.")

    args = parser.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        sys.exit("Error: ffmpeg/ffprobe not found on PATH. Install ffmpeg first.")

    args.output.mkdir(parents=True, exist_ok=True)

    try:
        inputs = gather_inputs(args.input)
    except FileNotFoundError as e:
        sys.exit(f"Error: {e}")

    print(f"Found {len(inputs)} video(s). Platforms: {', '.join(args.platforms)}. "
          f"Captions: {'on' if args.captions else 'off'}.")

    for src in inputs:
        try:
            process_one(
                src, args.output, args.platforms,
                args.captions, args.caption_model,
                args.title, args.description,
                smart_crop=args.smart_crop,
            )
        except Exception as e:
            print(f"  !! Failed on {src.name}: {e}", file=sys.stderr)

    print("\nDone.")


if __name__ == "__main__":
    main()
