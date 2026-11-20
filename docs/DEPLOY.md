# Deploy the live link (Hugging Face Spaces)

The rulebook accepts a live link **or** a ≤3-minute demo video. Do both if possible.

## 1. Create the Space
1. Go to https://huggingface.co/new-space
2. Name it `RxBondhu`, choose **Public**, SDK **Streamlit**.
3. After creation, open the Space → **Settings** → **Repository secrets** → add
   `GEMINI_API_KEY` = your Google AI Studio key. Never put the key in a file.

## 2. Push the code
In `D:\OpenCode\cu` (replace `YOUR_HF_NAME` with your Hugging Face username):

```bash
git remote add hf https://huggingface.co/spaces/YOUR_HF_NAME/RxBondhu
git push hf main
```

Keep the GitHub `origin` remote as well — both must exist. The GitHub repo is the judged submission repo; HF only serves the live demo.

## 3. Wait for build
The Space installs `requirements.txt` and starts `app.py`. The first boot can take a few minutes because `torch` is large. Check the Logs tab for errors.

## 4. Verify
- Upload `samples/sample_ui_smoke.png`, press **Read with both AI models**.
- Sidebar must show `Gemini key: yes` once the secret is set.
- After the CNN files are added to `models/` and pushed, sidebar must show `CNN ready · test acc 0.xxxx`.

## 5. No key yet?
The app still runs in CNN-only mode with an honest warning. Add the secret later and restart the Space.

## Important
Do not commit `.env`. Do not commit any API key. The model file `models/rx_cnn.pt` is ours and is fine to commit.
