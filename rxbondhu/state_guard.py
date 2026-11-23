"""Session-state schema checks.

A Streamlit Cloud redeploy can leave an older browser session holding an
``analysis`` dict from a previous version of the app (word-level items instead
of line-level items). Reading that stale dict directly raises KeyError in the
UI. These pure checks let the app show a friendly "please re-read" message
instead of crashing.
"""

ANALYSIS_KEYS = (
    "items", "line_count", "cnn_available", "vlm_error", "vlm_model",
    "vlm_lines", "vlm2_error", "vlm2_model", "vlm2_lines", "word_count",
)

ITEM_KEYS = (
    "index", "name", "reason", "colour", "cnn_brand", "cnn_confidence",
    "cnn_display", "cnn_conflicts",
    "vlm_guess", "vlm_text", "vlm2_guess", "vlm2_text", "agreement",
    "dose_text", "suggestions", "generic", "box", "dgda_record",
)

CONFIRMED_KEYS = ("index", "name", "options", "dose", "generic", "colour",
                  "editable", "raw_reading", "dgda_record")


def _has_keys(obj, keys):
    return isinstance(obj, dict) and all(key in obj for key in keys)


def analysis_is_current(analysis):
    """True only for a line-level ``pipeline.analyse()`` result."""
    if not _has_keys(analysis, ANALYSIS_KEYS):
        return False
    items = analysis.get("items")
    return isinstance(items, list) and all(_has_keys(item, ITEM_KEYS) for item in items)


def confirmed_rows_are_current(rows):
    """True only for review rows built by the current screen 2."""
    return isinstance(rows, list) and all(_has_keys(row, CONFIRMED_KEYS) for row in rows)
