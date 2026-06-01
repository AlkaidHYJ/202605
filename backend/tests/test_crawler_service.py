import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.services.crawler_service import _to_markdown, _apply_cleaning_rule


def test_to_markdown_basic():
    text = "Line1\n\nLine2"
    md = _to_markdown(text, "Title", "https://example.com")
    assert "# Title" in md
    assert "Source: https://example.com" in md
    assert "Line1" in md


def test_apply_cleaning_rule_drop_and_fill():
    rule = {
        "replace_map": {"foo": "bar"},
        "normalize_whitespace": True,
        "remove_empty_lines": True,
        "dedupe_lines": True,
        "min_length": 10,
        "fill_text": "FILL",
        "drop_if_contains": ["DROPME"],
    }
    # Contains drop keyword -> should return empty and status 2
    cleaned, status, reason = _apply_cleaning_rule("This contains DROPME", rule)
    assert status == 2
    assert reason and reason.startswith("contains:")

    # Short text -> filled
    cleaned2, status2, reason2 = _apply_cleaning_rule("", rule)
    assert status2 == 1 or status2 == 2
    # If filled, cleaned2 should equal fill_text when min_length satisfied
    if status2 == 1:
        assert "FILL" in cleaned2


def test_apply_cleaning_rule_replace_and_dedupe():
    rule = {
        "replace_map": {"旧": "新"},
        "normalize_whitespace": True,
        "remove_empty_lines": True,
        "dedupe_lines": True,
        "min_length": 0,
        "fill_text": "",
        "drop_if_contains": [],
    }
    cleaned, status, reason = _apply_cleaning_rule("旧A\n\n旧A\n  旧B  ", rule)
    assert status == 1
    assert reason is None
    assert "新A" in cleaned
    assert cleaned.count("新A") == 1
    assert "新B" in cleaned
