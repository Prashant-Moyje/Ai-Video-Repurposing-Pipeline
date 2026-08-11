import pytest

from repurpose.presets import get_preset, PRESETS


def test_get_preset_valid():
    preset = get_preset("tiktok")
    assert preset.width == 1080
    assert preset.height == 1920
    assert preset.mode == "crop_fill"


def test_get_preset_case_insensitive():
    assert get_preset("TikTok") == get_preset("tiktok")


def test_get_preset_unknown_raises():
    with pytest.raises(ValueError, match="Unknown platform"):
        get_preset("myspace")


def test_all_presets_have_positive_dimensions():
    for name, preset in PRESETS.items():
        assert preset.width > 0, f"{name} has non-positive width"
        assert preset.height > 0, f"{name} has non-positive height"


def test_youtube_is_letterbox_not_crop():
    # Horizontal YouTube should never crop into the source, only pad.
    assert get_preset("youtube").mode == "pad_fit"
