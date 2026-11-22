"""Fuse two AI readers plus our CNN into GREEN / YELLOW / UNVERIFIED / RED.

Safety rules (never relaxed):
- A brand outside the verified lexicon is never GREEN and never auto-accepted.
- RED/YELLOW/UNVERIFIED lines always need a human confirmation step.
- The CNN is a safety veto and proof of an own trained model, not a free pass.
"""

import re

from .lexicon import load_brands, lookup_exact, match_brand, normalise_name, suggest_brands

CNN_CONFIDENT = 0.60
CNN_LOW = 0.35
VLM_SCORE = 70


def clean_display_name(text: str) -> str:
    """Short editable default from a raw reader line (strengths/forms removed)."""
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
    # Bangla vowel signs are combining marks, not \w — keep the whole 0980–09FF block.
    value = re.sub(r"[^\w+\-\s\u0980-\u09ff]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip(" -")


def _reader_view(text: str, brands: list[dict]) -> dict:
    """What one reader said: a verified brand, or an unverified readable name."""
    raw = str(text or "").strip()
    hit = match_brand(raw, brands, threshold=VLM_SCORE) if raw else None
    verified = bool(hit and hit.get("score", 0) >= VLM_SCORE)
    return {
        "raw": raw,
        "brand": hit["brand"] if verified else "",
        "generic": hit["generic"] if verified else None,
        "display": (hit["brand"] if verified else clean_display_name(raw)),
        "score": int(hit["score"]) if hit else 0,
    }


def fuse(cnn: dict | None = None, vlm_text: str = "", brands: list[dict] | None = None,
         threshold: float = CNN_CONFIDENT, low: float = CNN_LOW,
         second_vlm_text: str = "") -> dict:
    """Fuse one line's three readings into one safe decision.

    ``cnn``           - {"brand": str|None, "confidence": float}
    ``vlm_text``      - primary photo reader's line text
    ``second_vlm_text`` - second, independent photo reader's line text
    """
    brands = brands if brands is not None else load_brands()
    cnn = cnn or {}
    cnn_brand = str(cnn.get("brand") or "").strip()
    cnn_conf = float(cnn.get("confidence") or 0.0)
    cnn_row = lookup_exact(cnn_brand, brands) if cnn_brand else None
    cnn_verified = cnn_row is not None
    cnn_confident = bool(cnn_verified and cnn_conf >= threshold)

    first = _reader_view(vlm_text, brands)
    second = _reader_view(second_vlm_text, brands)

    names = {view["brand"] for view in (first, second) if view["brand"]}
    both_confident = bool(first["brand"] and second["brand"])
    both_agree = both_confident and first["brand"] == second["brand"]
    one_confident = bool(first["brand"] or second["brand"]) and not both_confident

    cnn_contradiction = bool(
        cnn_confident and names and cnn_row["brand"] not in names
    )

    # A readable but unverified name must stay UNVERIFIED (editable), not RED.
    # Only a low-confidence CNN *and* no readable name at all is a RED case.
    readable = (first["display"] or second["display"]
                or (cnn_brand if cnn_conf >= low else ""))

    if cnn_conf < low and not names and not readable:
        colour = "RED"
        reason = "CNN confidence below the safety threshold and no readable medicine name"
        chosen, generic = "", None
    elif both_confident and not both_agree:
        colour = "RED"
        reason = "The two photo readers disagree - confirm with the prescriber"
        chosen, generic = first["display"] or second["display"], None
    elif cnn_contradiction:
        colour = "RED"
        reason = "Our CNN disagrees with both photo readers - confirm this line"
        chosen, generic = next(iter(names)), first["generic"] or second["generic"]
    elif both_agree:
        colour = "GREEN"
        reason = "Two independent readers agree on a verified brand"
        chosen = next(iter(names))
        generic = first["generic"] or second["generic"]
    elif one_confident:
        colour = "YELLOW"
        reason = "Only one photo reader is confident"
        chosen = next(iter(names))
        generic = first["generic"] or second["generic"]
    elif cnn_confident:
        colour = "YELLOW"
        reason = "Only our CNN is confident — confirm the brand on the paper"
        chosen, generic = cnn_row["brand"], cnn_row["generic"]
    else:
        if readable:
            colour = "UNVERIFIED"
            reason = "Brand could not be verified against the checked medicine list - please check"
            chosen = readable
            generic = None
        else:
            colour = "RED"
            reason = ("Neither reader could read this line"
                      if cnn_conf >= low else
                      "CNN confidence below the safety threshold and readers are unsure")
            chosen, generic = "", None

    suggestions = suggest_brands(vlm_text or second_vlm_text or cnn_brand or "", brands, n=3)

    return {
        "colour": colour,
        "reason": reason,
        "name": chosen,
        "generic": generic,
        "cnn_brand": cnn_brand,
        "cnn_confidence": round(cnn_conf, 3),
        "vlm_text": vlm_text,
        "vlm_guess": first["display"],
        "vlm_verified": first["brand"],
        "vlm2_text": second_vlm_text,
        "vlm2_guess": second["display"],
        "vlm2_verified": second["brand"],
        "agreement": ("agree" if both_agree else
                      "disagree" if both_confident else
                      "one-reader" if one_confident else "unverified"),
        "suggestions": suggestions,
        "needs_confirm": colour != "GREEN",
    }
