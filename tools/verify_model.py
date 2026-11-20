"""Quick local check after copying Kaggle outputs into models/.

Run:  .\\venv\\Scripts\\python.exe tools\\verify_model.py
Prints real model metadata and predictions on the UI smoke-test image.
Does not modify anything.
"""

import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rxbondhu import recognizer, segmentation  # noqa: E402
from rxbondhu.pipeline import analyse  # noqa: E402

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "samples", "sample_ui_smoke.png")


def main() -> int:
    info = recognizer.model_info()
    print("CNN metadata:", info)
    if not info.get("available"):
        print("CNN checkpoint missing — copy the four Kaggle outputs into models/ first.")
        return 1

    image = Image.open(SAMPLE)
    words = segmentation.segment(image)[:5]
    predictions = recognizer.predict_words([w["image"] for w in words])
    print("Word crops:", len(words))
    for index, top in enumerate(predictions):
        print(f"  crop {index}: {top[:3]}")

    report = analyse(image)
    print("Gemini error:", report["vlm_error"] or "none")
    print("Fusion:", [(i["name"], i["colour"], i["cnn_confidence"])
                      for i in report["items"][:5]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
