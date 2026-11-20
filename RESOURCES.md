# Resources, credits and licences

## Datasets
- **Doctor's Handwritten Prescription BD** — Kaggle, user `mamun1113`. 4,680 cropped handwritten medicine-name images, 78 brands, 15 generics; splits 3,120 / 780 / 780. Used for CNN training and evaluation. Credit the original dataset authors in the final README/slides.
- **Our own test prescriptions** — handwritten by team volunteers, no real patient data. Answer keys kept in the test log.

## Models
- **EfficientNet-B0** (torchvision, ImageNet pretrained) — base of our handwriting CNN. Apache-2.0 / BSD style torchvision licence; ImageNet terms apply.
- **Google Gemini Flash** via Google AI Studio — in-app vision-language reader. Subject to Google's terms; own API key required.
- **facebook/mms-tts-ben** (Hugging Face) — Bangla TTS. Licence **CC-BY-NC-4.0** (non-commercial use — fine for this hackathon).
- **gTTS** — backup Bangla speech (requires internet).

## Libraries
Python 3.11, PyTorch, torchvision, OpenCV, RapidFuzz, Streamlit, streamlit-cropper, pandas, NumPy, Matplotlib, python-dotenv, google-genai, transformers, SciPy, uroman, tabulate. Each library keeps its own open-source licence; used as-is via pip.

## Services
Kaggle (free T4 GPU), GitHub (public repo), Hugging Face Spaces (live demo).

## AI tools used while building
See README section 4. Disclose exactly what was used and for what.
