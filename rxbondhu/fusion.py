"""Combine our CNN reader with the Gemini reader into GREEN/YELLOW/RED."""

import re

from .lexicon import load_brands, lookup_exact, match_brand, normalise_name, suggest_brands

CNN_CONFIDENT = 0.60
CNN_LOW = 0.35
VLM_SCORE = 70


def clean_display_name(text: str) -> str:
    """Turn a raw Gemini line into a short, human-readable brand.

    Only used when the CNN guessed a class that is in our 78-class model but
    NOT in the verified lexicon. In that case we must not show the CNN guess
    (e.g. ``Az``); we show what Gemini actually read instead, while keeping the
    RED badge. Dosage forms, strengths and parenthetical generics are removed.
    """
    value = str(text or "").strip()
    if not value:
        return ""
    value = re.sub(
        r"^(tab|tablet|cap|capsule|syp|syrup|inj|injection|supp|suppository|"
        r"drop|drops|cr|cream|oint|ointment)\.?\s+",
        "", value, flags=re.IGNORECASE,
    )
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"\b\d+(?:\.\d+)?\s*(mg|mcg|ml|gm|iu|%|g)?\b", " ", value,
                   flags=re.IGNORECASE)
    value = re.sub(r"[^\w+\-\s]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip(" -")


def fuse(cnn: dict | None = None, vlm_text: str = "", brands: list[dict] | None = None,
         threshold: float = CNN_CONFIDENT, low: float = CNN_LOW) -> dict:
    """Fuse one line's two readings.

    cnn: {"brand": str|None, "confidence": float}
    vlm_text: raw text the vision-language reader produced for this line
    """
    brands = brands if brands is not None else load_brands()
    cnn = cnn or {}
    cnn_brand = cnn.get("brand") or ""
    cnn_conf = float(cnn.get("confidence") or 0.0)
    cnn_confident = bool(cnn_brand and cnn_conf >= threshold)

    cnn_row = lookup_exact(cnn_brand, brands) if cnn_brand else None
    cnn_verified = cnn_row is not None
    cnn_generic = cnn_row["generic"] if cnn_row else None

    vlm_match = match_brand(vlm_text, brands, threshold=60) if vlm_text else None
    vlm_confident = bool(vlm_match and vlm_match["score"] >= VLM_SCORE)
    vlm_name = vlm_match["brand"] if vlm_confident else ""
    vlm_generic = vlm_match["generic"] if vlm_confident else None

    # A CNN class can exist in our 78-class model but not in the 18-brand
    # verified lexicon. Never promote such a guess to GREEN/YELLOW: show it as
    # RED with an explicit reason instead of crashing on cnn_row["brand"].
    # When Gemini supplied a readable brand, show THAT name (e.g. Amdocal)
    # instead of the CNN's meaningless fallback class (e.g. Az).
    if cnn_brand and not cnn_verified:
        colour, reason = "RED", "CNN brand is not in the verified medicine list - please confirm"
        chosen, generic = clean_display_name(vlm_text) or cnn_brand, None
    elif cnn_confident and vlm_confident:
        if normalise_name(cnn_brand) == normalise_name(vlm_name):
            colour, reason = "GREEN", "Both readers agree"
            chosen, generic = cnn_row["brand"], cnn_generic
        else:
            colour, reason = "RED", "The two readers disagree"
            chosen, generic = cnn_row["brand"], cnn_generic
    elif cnn_confident or vlm_confident:
        colour, reason = "YELLOW", "Only one reader is confident"
        if cnn_confident:
            chosen, generic = cnn_row["brand"], cnn_generic
        else:
            chosen, generic = vlm_name, vlm_generic
    else:
        colour, reason = "RED", "Neither reader is confident enough"
        chosen = cnn_brand or (vlm_match or {}).get("brand", "")
        generic = cnn_generic or (vlm_match or {}).get("generic")

    if cnn_conf < low and not vlm_confident:
        colour, reason = "RED", "CNN confidence below the safety threshold"

    suggestions = suggest_brands(vlm_text or cnn_brand or "", brands, n=3)

    return {
        "colour": colour,
        "reason": reason,
        "name": chosen or "",
        "generic": generic,
        "cnn_brand": cnn_brand,
        "cnn_confidence": round(cnn_conf, 3),
        "vlm_text": vlm_text,
        "vlm_guess": vlm_name,
        "suggestions": suggestions,
        "needs_confirm": colour != "GREEN",
    }
