"""Google Gemini vision reader (the second, independent AI reader).

Requires a real API key in .env. Nothing is cached or hard-coded: every call
goes to the model, and failures are reported honestly to the UI.
"""

import io
import json
import os
import re

from dotenv import load_dotenv

_PROMPT = """You are helping transcribe a handwritten Bangladeshi doctor's prescription.
Read the image carefully. List ONLY the medicine names and their dose instructions that you can actually see.

Return a JSON array, nothing else, like:
[{"medicine": "Napa", "dose": "1+0+1"}, {"medicine": "Maxpro", "dose": "BD"}]

Rules:
- If a word is unclear, put your best reading with a trailing "?" — do not invent a medicine.
- Keep Latin brand names as written; Bangla text may be returned in Bangla.
- Do NOT diagnose, prescribe, explain, or add medicines that are not visible.
- If there is no readable medicine, return [].
"""


DEFAULT_MODELS = (
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
)


def _secret(name: str, default: str = "") -> str:
    """Read a secret from Streamlit Cloud first, then local .env/os.environ."""
    try:
        import streamlit as st
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


def _model_chain(explicit: str | None = None) -> list[str]:
    """Models to try in order; one Gemini key serves all of them."""
    if explicit:
        return [explicit.strip()]
    raw = _secret("RX_VLM_MODELS", "") or _secret("RX_VLM_MODEL", "")
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    return parts or list(DEFAULT_MODELS)


def _client():
    load_dotenv()
    key = _secret("GEMINI_API_KEY")
    if not key:
        return None, "GEMINI_API_KEY is empty"
    try:
        from google import genai
    except ImportError as exc:
        return None, f"google-genai not installed: {exc}"
    try:
        return genai.Client(api_key=key), ""
    except Exception as exc:
        return None, f"Could not create Gemini client: {exc}"


def available() -> tuple[bool, str]:
    """Check key/client availability without making a network call."""
    client, error = _client()
    return (client is not None), error


def _extract_json(text: str):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start >= 0 and end > start:
        try:
            data = json.loads(cleaned[start:end + 1])
            if isinstance(data, list):
                return data
        except (ValueError, TypeError):
            pass
    # Fallback: one plain-text line per medicine.
    return [{"medicine": line.strip(" -•*\t"), "dose": ""}
            for line in cleaned.splitlines() if line.strip()]


def read(image, model: str | None = None) -> dict:
    """Send one image to Gemini; return {"lines": [...], "raw": str, "error": str}.

    Each line is {"medicine": str, "dose": str}. On any failure, lines is empty
    and error explains why — the UI then shows CNN-only mode.
    """
    client, error = _client()
    if client is None:
        return {"lines": [], "raw": "", "error": error, "model": model or ""}

    chain = _model_chain(model)
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=90)
    payload = buffer.getvalue()

    try:
        from google.genai import types
        parts = [types.Part.from_bytes(data=payload, mime_type="image/jpeg"),
                 types.Part.from_text(text=_PROMPT)]
    except Exception as exc:
        return {"lines": [], "raw": "", "error": f"Could not build Gemini request: {exc}", "model": ""}

    errors: list[str] = []
    raw = ""
    used = chain[-1]
    for candidate in chain:
        try:
            response = client.models.generate_content(model=candidate, contents=parts)
            raw = (response.text or "").strip()
            used = candidate
            if raw:
                break
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")
    if not raw:
        return {"lines": [], "raw": "",
                "error": "Gemini models failed: " + " | ".join(errors), "model": used}
    model = used

    lines = []
    for item in _extract_json(raw):
        if isinstance(item, dict):
            name = str(item.get("medicine") or item.get("name") or "").strip()
            dose = str(item.get("dose") or item.get("doses") or "").strip()
        else:
            name, dose = str(item).strip(), ""
        if name:
            lines.append({"medicine": name, "dose": dose})
    return {"lines": lines, "raw": raw, "error": "", "model": model}
