"""Bangla text-to-speech: local MMS-TTS first, gTTS as backup.

Both engines are real models/services; if neither works, the caller gets a
clear error instead of a silent/fake audio file.
"""

import os
import tempfile


def speak_bangla(text: str, output: str | None = None, prefer: str = "auto") -> dict:
    """Create an audio file from Bangla text.

    Returns {"path": str, "engine": str, "error": str}.
    """
    if not text or not text.strip():
        return {"path": "", "engine": "", "error": "Nothing to speak"}
    output = output or os.path.join(tempfile.gettempdir(), "rxbondhu_schedule.wav")
    errors = []

    if prefer in ("auto", "mms"):
        try:
            import numpy as np
            import soundfile as sf
            import torch
            from scipy.io import wavfile
            from transformers import pipeline

            pipe = pipeline("text-to-speech", model="facebook/mms-tts-ben",
                            torch_dtype=torch.float32)
            result = pipe(text)
            audio = result["audio"]
            if hasattr(audio, "numpy"):
                audio = audio.numpy()
            audio = np.asarray(audio, dtype="float32").reshape(-1)
            rate = int(result["sampling_rate"])
            wav_path = os.path.splitext(output)[0] + ".wav"
            wavfile.write(wav_path, rate, audio)
            return {"path": wav_path, "engine": "facebook/mms-tts-ben", "error": ""}
        except Exception as exc:
            errors.append(f"MMS-TTS: {exc}")

    if prefer in ("auto", "gtts"):
        try:
            from gtts import gTTS
            mp3_path = os.path.splitext(output)[0] + ".mp3"
            gTTS(text=text, lang="bn", slow=False).save(mp3_path)
            return {"path": mp3_path, "engine": "gTTS", "error": ""}
        except Exception as exc:
            errors.append(f"gTTS: {exc}")

    return {"path": "", "engine": "", "error": " | ".join(errors) or "No TTS engine available"}
