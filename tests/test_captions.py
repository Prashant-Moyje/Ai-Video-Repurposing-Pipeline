from repurpose.captions import _format_timestamp


def test_format_timestamp_zero():
    assert _format_timestamp(0) == "00:00:00,000"


def test_format_timestamp_seconds_and_millis():
    assert _format_timestamp(1.5) == "00:00:01,500"


def test_format_timestamp_minutes():
    assert _format_timestamp(75) == "00:01:15,000"


def test_format_timestamp_hours():
    assert _format_timestamp(3661.25) == "01:01:01,250"
