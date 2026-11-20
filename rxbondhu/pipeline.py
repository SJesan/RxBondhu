"""End-to-end core pipeline: crop -> two readers -> fusion -> schedule.

The Streamlit app calls analyse() for screen 2 and build_schedule() after the
user has reviewed and confirmed everything on screen 3. Nothing reaches the
schedule without the user's confirmation.
"""

from .dose_parser import parse
from .fusion import fuse
from .safety import duplicate_warning, has_red


def analyse(image, max_words: int = 30) -> dict:
    """Read one cropped medicine area with both AI models.

    Returns:
      {"items": [ {name, generic, colour, reason, confidence, dose_text, box,
                   cnn_brand, vlm_guess, suggestions, needs_confirm} ],
       "vlm_raw": str, "vlm_error": str, "cnn_available": bool,
       "word_count": int}
    """
    from . import recognizer, segmentation, vlm

    words = segmentation.segment(image)[:max_words]
    cnn_hits = recognizer.predict_words([w["image"] for w in words]) if words else []
    gemini = vlm.read(image)

    items = []
    for index, word in enumerate(words):
        top = cnn_hits[index][0] if index < len(cnn_hits) and cnn_hits[index] else None
        cnn = {"brand": top["brand"] if top else "",
               "confidence": top["confidence"] if top else 0.0}
        vlm_line = gemini["lines"][index] if index < len(gemini["lines"]) else {}
        vlm_text = vlm_line.get("medicine", "")
        result = fuse(cnn, vlm_text)
        items.append({
            **result,
            "dose_text": vlm_line.get("dose", ""),
            "box": word["box"],
            "index": index,
        })

    return {
        "items": items,
        "images": [w["image"] for w in words],
        "vlm_raw": gemini["raw"],
        "vlm_error": gemini["error"],
        "vlm_model": gemini["model"],
        "cnn_available": recognizer.available(),
        "word_count": len(words),
    }


def build_schedule(confirmed: list[dict]) -> dict:
    """Turn user-confirmed rows into a Bangla-ready schedule plus warnings.

    Each confirmed row needs: name, generic, dose (string), colour (optional).
    """
    medicines = []
    for row in confirmed or []:
        name = str(row.get("name") or row.get("brand") or "").strip()
        if not name:
            continue
        parsed = parse(str(row.get("dose") or ""))
        medicines.append({
            "name": name,
            "generic": str(row.get("generic") or "").strip(),
            "dose": parsed,
            "colour": str(row.get("colour") or "GREEN").upper(),
        })

    warnings = duplicate_warning(medicines)
    if has_red(confirmed or []):
        warnings.append("Some lines were uncertain — please confirm them with your pharmacist.")
    for med in medicines:
        warnings.extend(med["dose"]["warnings"])

    return {"medicines": medicines, "warnings": warnings}
