"""
Smart crop: uses OpenCV face detection to compute a better crop offset than
a blind center-crop, so a speaker/subject isn't cut off when reformatting
to a narrower aspect ratio (e.g. 16:9 -> 9:16 for TikTok/Reels/Shorts).

Approach:
  1. Sample frames from the source video at a fixed interval (not every
     frame — this keeps it fast and CPU-only friendly).
  2. Run a Haar cascade face detector (bundled with OpenCV, no extra
     download / model weights needed) on each sampled frame.
  3. Take the median of detected face centers across all samples as a
     single, stable crop offset for the whole clip.
  4. Fall back to dead-center (0.5, 0.5) if no faces are found anywhere —
     identical behavior to the original naive center-crop.

This computes one static offset for the whole video rather than tracking
frame-by-frame (which would need a dynamic/expression-based ffmpeg crop
and per-frame smoothing) — a deliberate scope tradeoff: much simpler and
more robust, and still meaningfully better than a blind center-crop for
typical talking-head content.
"""

from pathlib import Path

import cv2
import numpy as np

_face_cascade = None  # lazy-loaded on first use, not at import time


def _get_face_cascade():
    """
    Lazily construct the Haar cascade classifier. Deferring this to first
    use (rather than at import time) means a broken/incompatible OpenCV
    install surfaces as a caught exception inside detect_face_center_offset
    (which degrades to a plain center-crop) instead of crashing the whole
    app or failing test collection just from importing this module.
    """
    global _face_cascade
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    return _face_cascade


def detect_face_center_offset(
    video_path: Path,
    sample_every_s: float = 1.0,
    max_samples: int = 30,
) -> tuple[float, float]:
    """
    Return (x_frac, y_frac) in [0, 1]: the median detected face center,
    normalized to frame dimensions. (0.5, 0.5) is dead-center — used both
    as the no-face-found result and as the safe fallback if face detection
    itself fails for any reason (e.g. an incompatible OpenCV/NumPy build).
    """
    try:
        cascade = _get_face_cascade()
    except Exception:
        # OpenCV unusable in this environment — behave exactly like the
        # original center-crop rather than taking the app down.
        return 0.5, 0.5

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0.5, 0.5

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frame_interval = max(int(fps * sample_every_s), 1)

    centers: list[tuple[float, float]] = []
    frame_idx = 0

    try:
        while len(centers) < max_samples:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
                )
                if len(faces) > 0:
                    # Largest detected face wins (most likely the main subject).
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    frame_h, frame_w = frame.shape[:2]
                    centers.append(((x + w / 2) / frame_w, (y + h / 2) / frame_h))

            frame_idx += 1
    except Exception:
        return 0.5, 0.5
    finally:
        cap.release()

    if not centers:
        return 0.5, 0.5

    arr = np.array(centers)
    return float(np.median(arr[:, 0])), float(np.median(arr[:, 1]))
