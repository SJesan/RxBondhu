"""Fuse two AI readers plus our CNN into GREEN / YELLOW / UNVERIFIED / RED.

Safety rules:
- A brand outside the verified lexicon is never GREEN and never auto-accepted.
- GREEN also needs a DGDA DAR No. A box-checked-only or conflicted identity
  (Napa, Fexo, Ace, ...) is capped at YELLOW with explicit wording — never
  "DGDA not matched" next to a GREEN badge, and never "not approved".
- RED/YELLOW/UNVERIFIED lines always need a human confirmation step.
- The CNN is a safety veto and proof of an own trained model, except when both
  readers independently make an EXACT (100) match to the same DAR-backed DGDA
  brand. That exception prevents the 78-class word-crop CNN from red-flagging
  real photos it was never trained on (e.g. Pantonix, Lysivin); final
  confirmation is still mandatory on Screen 3. A contradictory CNN guess is
  disclosed in More info, not in the main reading line.
"""

import os
import re
from difflib import SequenceMatcher

from .lexicon import (GREEN_SCORE, conflict_for, load_brands, lookup_exact,
                      match_brand, normalise_name, suggest_brands)

CNN_CONFIDENT = 0.60
CNN_LOW = 0.35
# Candidate threshold, selected on the 5-image dev split (answer-key rows
# 1-5) from {85, 90}: 90 gave combined 0.60 vs 0.52 with zero unsafe-GREEN.
# Rows 6-10 are holdout and are reported once. GREEN_SCORE = 95 is a fixed
# safety policy, not tuned. The env override is for reproducible before/after
# evaluator runs; the app never sets it.
VLM_SCORE = int(os.getenv("RX_VLM_SCORE", "90"))
# Only a perfect normalised match from BOTH readers can override a confident
# CNN guess. Near-exact (95-99) dual matches keep the veto.
EXACT_MATCH_SCORE = 100
BOX_ONLY_REASON = "Verified by box check, not found in DGDA snapshot — confirm on paper"
CNN_NOT_APPLICABLE = "not applicable to this name"


def _dar_backed(hit: dict | None) -> bool:
    """True only when the matched row carries a DGDA DAR No."""
    return bool(hit and str(hit.get("dar_no") or "").strip())


def _close_spelling(first: str, second: str) -> bool:
    """Two readers spelled nearly the same name differently (e.g. Panicel/Paricel)."""
    if not first or not second:
        return False
    return SequenceMatcher(None, first.casefold(), second.casefold()).ratio() >= 0.6


def clean_display_name(text: str) -> str:
    """Short editable default from a raw reader line (strengths/forms removed)."""
    value = str(text or "").strip()
    if not value:
        return ""
    value = re.sub(
        r"^(ts|tab|tablet|cap|capsule|syp|syrup|inj|injection|supp|suppository|"
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
    """What one reader said: a GREEN-eligible brand, a fuzzy candidate, or a name."""
    raw = str(text or "").strip()
    hit = match_brand(raw, brands, threshold=VLM_SCORE) if raw else None
    score = int(hit["score"]) if hit else 0
    green_eligible = bool(hit and score >= GREEN_SCORE)
    return {
        "raw": raw,
        # A candidate brand is kept for agreement checks, but its generic is
        # withheld: a fuzzy hit must never assert the wrong drug identity.
        "brand": hit["brand"] if hit else "",
        "generic": hit["generic"] if green_eligible else None,
        "display": (hit["brand"] if green_eligible else clean_display_name(raw)),
        "score": score,
        "green_eligible": green_eligible,
        "dar_backed": _dar_backed(hit),
        "candidate": bool(hit and not green_eligible),
        "match_kind": hit["match_kind"] if hit else "none",
        "hit": hit,
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
    min_match = min(first["score"], second["score"])
    both_dar_backed = bool(first["dar_backed"] and second["dar_backed"])
    both_green_eligible = both_agree and min_match >= GREEN_SCORE and both_dar_backed
    # An exact dual match on a DAR-backed DGDA row is the only case where the
    # CNN veto is set aside. A box-only identity never reaches GREEN.
    dual_exact = bool(both_green_eligible and min_match >= EXACT_MATCH_SCORE)
    one_confident = bool(first["brand"] or second["brand"]) and not both_confident

    cnn_contradiction = bool(
        cnn_confident and names and cnn_row["brand"] not in names and not dual_exact
    )

    # An exact dual agreement on a box/pharmacist-only row (no DGDA DAR No) is
    # capped at YELLOW with honest box-check wording. An out-of-distribution
    # CNN guess is disclosed in More info but never escalates this line to RED
    # or promotes it to GREEN — the readers' agreement is the deciding signal.
    box_only_exact = bool(
        both_agree and min_match >= GREEN_SCORE and not both_dar_backed
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
    elif (not both_green_eligible
          and first["display"] and second["display"]
          and first["display"].casefold() != second["display"].casefold()
          and (both_confident or _close_spelling(first["display"], second["display"]))):
        # Readers spelled nearly the same name differently. Never auto-approve
        # the disagreement, even when one side happens to match a DGDA row.
        colour = "RED"
        reason = "The two photo readers disagree on this brand - confirm with the prescriber"
        chosen, generic = first["display"], None
    elif box_only_exact:
        # Exact box-only identity (Napa/Fexo/Ace): useful to display, but it
        # must never sit under a GREEN badge with "DGDA not matched" nearby and
        # must never be turned RED by an out-of-distribution CNN guess.
        colour = "YELLOW"
        reason = BOX_ONLY_REASON
        chosen = first["display"] or second["display"]
        generic = None
    elif cnn_contradiction:
        colour = "RED"
        reason = "Our CNN disagrees with both photo readers - confirm this line"
        chosen, generic = next(iter(names)), first["generic"] or second["generic"]
    elif both_green_eligible:
        colour = "GREEN"
        if dual_exact and cnn_confident and names and cnn_row["brand"] not in names:
            # Honest disclosure: the CNN is out of distribution here, so its
            # guess is ignored rather than silently dropped from the UI.
            reason = ("Two readers agree on an exact DGDA-registered brand; "
                      "CNN guess is outside its training set")
        else:
            reason = "Two independent readers agree on a DGDA-registered brand (score >= 95)"
        chosen = next(iter(names))
        generic = first["generic"] or second["generic"]
    elif both_agree:
        # 85-94.9 is a fuzzy-only identity: never GREEN, and no generic is
        # asserted until a human confirms the spelling on the paper.
        colour = "YELLOW"
        reason = "Readers agree, but the brand match is fuzzy-only — confirm on paper"
        chosen = first["display"] or second["display"]
        generic = None
    elif one_confident:
        colour = "YELLOW"
        reason = "Only one photo reader is confident"
        confident = first if first["brand"] else second
        chosen = confident["display"]
        generic = confident["generic"]
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

    # The side card shows provenance only. A fuzzy hit is labelled as such and
    # never presented as a confirmed DGDA identity.
    record_hit = (first["hit"] if first["green_eligible"] else
                  second["hit"] if second["green_eligible"] else
                  first["hit"] or second["hit"])
    dgda_record = None
    if record_hit:
        conflict = conflict_for(record_hit["brand"])
        dgda_record = {
            "brand": record_hit["brand"],
            "generic": record_hit["generic"],
            "strength": record_hit["strength"],
            "form": record_hit["form"],
            "company": record_hit["company"],
            "dar_no": record_hit["dar_no"],
            "source": record_hit["source"],
            "source_url": record_hit["source_url"],
            "accessed_at": record_hit["accessed_at"],
            "score": record_hit["score"],
            "match_kind": record_hit["match_kind"],
            "green_eligible": bool(record_hit["score"] >= GREEN_SCORE
                                   and _dar_backed(record_hit)),
            "dar_backed": _dar_backed(record_hit),
            "conflict_reason": str((conflict or {}).get("reason") or ""),
            "conflict_generics": str((conflict or {}).get("dgda_generics") or ""),
        }

    # Main view: a wrong/conflicting CNN guess is never printed as a reading.
    # Its raw score stays available for the More info expander.
    cnn_conflicts = bool(
        cnn_brand and (
            not names or cnn_row is None or cnn_row["brand"] not in names
        )
    )
    if cnn_conflicts:
        cnn_display = CNN_NOT_APPLICABLE
    elif cnn_brand and cnn_conf >= low:
        cnn_display = f"{cnn_brand} ({cnn_conf:.2f})"
    else:
        cnn_display = "not used for this line"

    return {
        "colour": colour,
        "reason": reason,
        "name": chosen,
        "generic": generic,
        "cnn_brand": cnn_brand,
        "cnn_confidence": round(cnn_conf, 3),
        "cnn_display": cnn_display,
        "cnn_conflicts": cnn_conflicts,
        "vlm_text": vlm_text,
        "vlm_guess": first["display"],
        "vlm_verified": first["brand"] if first["green_eligible"] else "",
        "vlm2_guess": second["display"],
        "vlm2_verified": second["brand"] if second["green_eligible"] else "",
        "vlm2_text": second_vlm_text,
        "match_scores": {"reader1": first["score"], "reader2": second["score"]},
        "match_kinds": {"reader1": first["match_kind"], "reader2": second["match_kind"]},
        "min_match_score": min_match,
        "green_score": GREEN_SCORE,
        "dgda_record": dgda_record,
        "agreement": ("agree" if both_agree else
                      "disagree" if both_confident else
                      "one-reader" if one_confident else "unverified"),
        "suggestions": suggestions,
        "needs_confirm": colour != "GREEN",
    }
