from repurpose.presets import get_preset
from repurpose.resize import build_video_filter


def test_crop_fill_default_is_centered():
    vf = build_video_filter(1920, 1080, get_preset("tiktok"))
    assert "(iw-1080)*0.5" in vf
    assert "(ih-1920)*0.5" in vf


def test_crop_fill_respects_custom_offset():
    vf = build_video_filter(1920, 1080, get_preset("tiktok"), crop_center=(0.8, 0.2))
    assert "(iw-1080)*0.8" in vf
    assert "(ih-1920)*0.2" in vf


def test_crop_fill_clamps_out_of_range_offsets():
    vf = build_video_filter(1920, 1080, get_preset("tiktok"), crop_center=(1.7, -0.3))
    assert "*1.0" in vf
    assert "*0.0" in vf


def test_pad_fit_ignores_crop_center():
    # Letterbox mode never crops, so a crop_center argument should have no effect.
    vf_default = build_video_filter(1920, 1080, get_preset("youtube"))
    vf_offset = build_video_filter(1920, 1080, get_preset("youtube"), crop_center=(0.9, 0.1))
    assert vf_default == vf_offset
    assert "pad=" in vf_default


def test_unknown_mode_raises():
    import pytest
    from dataclasses import replace

    bad_preset = replace(get_preset("tiktok"), mode="stretch")
    with pytest.raises(ValueError, match="Unknown fit mode"):
        build_video_filter(1920, 1080, bad_preset)
