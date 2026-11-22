"""Groq vision reader (the second, independent photo-to-text reader).

Uses Groq's OpenAI-compatible chat completions endpoint with a vision model.
No API key is stored here: it is read from Streamlit Secrets first, then .env.
Failures are reported honestly in the same shape as ``vlm.read``.
"""

import base64
import io
import json
import os
import re
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

DEFAULT_MODELS = ("qwen/qwen3.8-27b",)
API_URL = "https://api.groq.com/openai/v1/chat/completions"

_PROMPT = """You are transcribing a handwritten Bangladeshi doctor's prescription.
Read the image carefully. List ONLY the medicine names and dose instructions you can actually see.

Return a JSON array and nothing else, like:
[{"medicine": "Napa", "dose": "1+0+1"}]

Rules:
- Keep Latin brand names as written; Bangla text may be returned in Bangla.
- Dose notation may be 1+0+1, BD, TDS, HS, before/after meal, or Bangla text.
- If a word is unsure, put your best reading with a trailing "?" - never invent a medicine.
- Do NOT diagnose, prescribe, explain, or add invisible medicines.
- If there is no readable medicine, return [].
"""


def _secret(name: str, default: str = "") -> str:
    load_dotenv()
    try:
        import streamlit as st
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


def _model_chain(explicit: str | None = None) -> list[str]:
    if explicit:
        return [explicit.strip()]
    raw = _secret("RX_GROQ_MODELS", "") or _secret("RX_GROQ_MODEL", "")
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    return parts or list(DEFAULT_MODELS)


def available() -> tuple[bool, str]:
    """Check key availability without making a network call."""
    if not _secret("GROQ_API_KEY"):
        return False, "GROQ_API_KEY is empty"
    return True, ""


def _extract_lines(raw: str) -> list[dict]:
    cleaned = (raw or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    start, end = cleaned.find("["), cleaned.rfind("]")
    data = None
    if start >= 0 and end > start:
        try:
            data = json.loads(cleaned[start:end + 1])
        except (ValueError, TypeError):
            data = None
    if not isinstance(data, list):
        return [{"medicine": line.strip(" -•*\t"), "dose": ""}
                for line in cleaned.splitlines() if line.strip()]
    lines = []
    for item in data:
        if isinstance(item, dict):
            name = str(item.get("medicine") or item.get("name") or "").strip()
            dose = str(item.get("dose") or item.get("doses") or "").strip()
        else:
            name, dose = str(item).strip(), ""
        if name:
            lines.append({"medicine": name, "dose": dose})
    return lines


def read(image, model: str | None = None) -> dict:
    """Send one image to a Groq vision model; return the vlm.read() shape."""
    key = _secret("GROQ_API_KEY")
    if not key:
        return {"lines": [], "raw": "", "error": "GROQ_API_KEY is empty", "model": model or ""}

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=90)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    errors: list[str] = []
    for candidate in _model_chain(model):
        payload = {
            "model": candidate,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
                ],
            }],
            "temperature": 0.1,
            "max_completion_tokens": 512,
            "stream": False,
        }
        request = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "Accept": "application/json",
                     "User-Agent": "RxBondhu/2.0 (+local-demo)"},
            method="POST",
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    body = json.loads(response.read().decode("utf-8"))
                raw = (body["choices"][0]["message"]["content"] or "").strip()
                if raw:
                    return {"lines": _extract_lines(raw), "raw": raw,
                            "error": "", "model": candidate}
                errors.append(f"{candidate}: empty response")
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:300]
                if exc.code == 429 and attempt < 3:
                    # Groq free tier is ~7k input tokens/minute; one image uses ~2.2k.
                    # Honour Retry-After when present, otherwise wait 20 seconds.
                    try:
                        wait = float(exc.headers.get("Retry-After") or 20)
                    except (TypeError, ValueError):
                        wait = 20.0
                    time.sleep(min(max(wait, 1.0), 45.0))
                    continue
                errors.append(f"{candidate}: HTTP {exc.code} {detail}")
                break
            except Exception as exc:
                errors.append(f"{candidate}: {exc}")
                break
    return {"lines": [], "raw": "",
            "error": "Groq models failed: " + " | ".join(errors),
            "model": model or ""}
