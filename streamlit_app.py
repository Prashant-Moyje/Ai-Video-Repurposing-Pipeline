"""
Video Repurposing Bot — web app (Streamlit)

Upload a video, pick target platform(s), optionally add auto-captions,
download the resized results. Designed to run on Streamlit Community
Cloud's free tier (1GB RAM, CPU only), so it enforces sane limits on
input duration/size to keep processing time and memory use reasonable.
"""

import shutil
import tempfile
from pathlib import Path

import streamlit as st

from repurpose.presets import PRESETS, get_preset
from repurpose.resize import resize_video, probe
from repurpose.captions import transcribe_to_srt, burn_captions

# Free-tier guardrails (1GB RAM on Streamlit Community Cloud). Raise these
# if you deploy somewhere with more headroom.
MAX_DURATION_S = 60
MAX_FILE_MB = 60
CAPTION_MODEL = "base"  # smaller than "small" — fits comfortably in 1GB RAM

st.set_page_config(page_title="Video Repurposing Bot", page_icon="🎬")

st.title("🎬 Video Repurposing Bot")
st.markdown(
    "Upload a video and get it resized/cropped for TikTok, Reels, Shorts, "
    "or YouTube — with optional auto-generated burned-in captions.\n\n"
    f"*Free-tier demo limits: videos under {MAX_DURATION_S}s and "
    f"{MAX_FILE_MB}MB. For longer videos, run the CLI version locally "
    "(see the GitHub repo linked below).*"
)

uploaded_file = st.file_uploader("Upload your video", type=["mp4", "mov", "mkv", "avi", "webm"])

platforms = st.multiselect(
    "Target platform(s)",
    options=list(PRESETS.keys()),
    default=["tiktok"],
)

add_captions = st.checkbox(
    "Add auto-generated captions (slower — local speech-to-text)",
    value=False,
)

run_button = st.button("Repurpose video", type="primary", disabled=uploaded_file is None)

if run_button:
    if not platforms:
        st.error("Pick at least one platform.")
        st.stop()

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        st.error(f"File too large ({size_mb:.0f}MB). Limit is {MAX_FILE_MB}MB on this free-tier demo.")
        st.stop()

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        src = tmp / uploaded_file.name
        src.write_bytes(uploaded_file.getbuffer())

        info = probe(src)
        if info["duration"] > MAX_DURATION_S:
            st.error(f"Video is {info['duration']:.0f}s long. Limit is "
                      f"{MAX_DURATION_S}s on this free-tier demo.")
            st.stop()

        progress_bar = st.progress(0.0)
        status = st.empty()
        results = []

        for i, platform_name in enumerate(platforms):
            frac = i / len(platforms)
            status.text(f"Resizing for {platform_name}...")
            progress_bar.progress(frac)

            preset = get_preset(platform_name)
            resized_path = tmp / f"{src.stem}_{platform_name}_resized.mp4"
            resize_video(src, resized_path, preset)
            current = resized_path

            if add_captions:
                status.text(f"Transcribing audio ({platform_name})...")
                progress_bar.progress(frac + 0.3 / len(platforms))
                srt_path = tmp / f"{src.stem}_{platform_name}.srt"
                transcribe_to_srt(current, srt_path, model_size=CAPTION_MODEL)

                status.text(f"Burning in captions ({platform_name})...")
                progress_bar.progress(frac + 0.7 / len(platforms))
                captioned_path = tmp / f"{src.stem}_{platform_name}_captioned.mp4"
                burn_captions(current, srt_path, captioned_path)
                current = captioned_path

            final_path = tmp / f"{src.stem}_{platform_name}_final.mp4"
            shutil.copy2(current, final_path)
            results.append((platform_name, final_path.read_bytes()))

        progress_bar.progress(1.0)
        status.text("Done!")

        st.subheader("Your repurposed videos")
        for platform_name, video_bytes in results:
            st.video(video_bytes)
            st.download_button(
                label=f"Download {platform_name} version",
                data=video_bytes,
                file_name=f"{Path(uploaded_file.name).stem}_{platform_name}.mp4",
                mime="video/mp4",
            )

st.markdown("---")
st.markdown(
    "Built with FFmpeg + faster-whisper. "
    "[Source code](https://github.com/YOUR_USERNAME/video-repurposing-bot)"
)
