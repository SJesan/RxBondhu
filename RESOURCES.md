# Resources, credits and licences

## Datasets
- **Doctor's Handwritten Prescription BD** — Kaggle, user `mamun1113`. 4,680 cropped handwritten medicine-name images, 78 brands, 15 generics; splits 3,120 / 780 / 780. Used for CNN training and evaluation. Credit the original dataset authors in the final README/slides.
- **Our own test prescriptions** — handwritten by team volunteers, no real patient data. Answer keys kept in the test log.

## Models
- **EfficientNet-B0** (torchvision, ImageNet pretrained) — base of our handwriting CNN. Apache-2.0 / BSD style torchvision licence; ImageNet terms apply.
- **Google Gemini Flash** via Google AI Studio — in-app vision-language reader. Subject to Google's terms; own API key required.
- **facebook/mms-tts-ben** (Hugging Face) — Bangla TTS. Licence **CC-BY-NC-4.0** (non-commercial use — fine for this hackathon).
- **gTTS** — backup Bangla speech (requires internet).

## Libraries and assets
Python 3.11, PyTorch, torchvision, OpenCV, RapidFuzz, Streamlit, streamlit-cropper, pandas, NumPy, Matplotlib,
python-dotenv, google-genai, transformers, SciPy, uroman, tabulate — each under its own open-source licence, used via pip.
**Three.js** (MIT licence) — bundled locally as `static/three.min.js` for the capsule animation on screen 1.

## Services
Kaggle (free T4 GPU for training), GitHub (public repo + Actions CI), Streamlit Community Cloud (live app).

## AI tools used while building
Claude (Anthropic) and OpenCode (Big Pickle) as coding assistants — see README section 4 for exactly what each was used for.
