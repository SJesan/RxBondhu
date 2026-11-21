"""Generate the detailed RxBondhu project report PDF.

Reproducible from the repository (needs reportlab, a report-generation-only dependency):
    pip install reportlab
    .\\venv\\Scripts\\python.exe tools\\make_project_report.py

All numbers in the report come from our own files in models/ and docs/EVALUATION.md.
Nothing is invented; the volunteer prescription table is explicitly left pending.
"""

import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "RxBondhu_Project_Report.pdf")

GREEN = colors.HexColor("#0E6B3C")
GREEN_DARK = colors.HexColor("#084C2A")
GREEN_LIGHT = colors.HexColor("#F4FAF5")
BORDER = colors.HexColor("#DCEBDD")
INK = colors.HexColor("#243B2F")
GREY = colors.HexColor("#5C6B62")
AMBER = colors.HexColor("#B26A00")
RED = colors.HexColor("#A32626")
BLUE = colors.HexColor("#1B4F72")

PAGE_W, PAGE_H = A4
MARGIN = 42
CONTENT_W = PAGE_W - 2 * MARGIN

ss = getSampleStyleSheet()
S = {
    "cover_title": ParagraphStyle("cover_title", parent=ss["Title"], fontName="Helvetica-Bold",
                                  fontSize=25, leading=30, textColor=GREEN_DARK, alignment=TA_CENTER),
    "cover_sub": ParagraphStyle("cover_sub", parent=ss["Normal"], fontName="Helvetica",
                                fontSize=12, leading=17, textColor=GREY, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15,
                         leading=19, textColor=GREEN_DARK, spaceBefore=14, spaceAfter=7),
    "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11,
                         leading=15, textColor=INK, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=9.3,
                           leading=13.2, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=5),
    "small": ParagraphStyle("small", parent=ss["Normal"], fontName="Helvetica", fontSize=8,
                            leading=11, textColor=GREY, spaceAfter=3),
    "cell": ParagraphStyle("cell", parent=ss["Normal"], fontName="Helvetica", fontSize=8,
                           leading=10.8, textColor=INK),
    "cell_b": ParagraphStyle("cell_b", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=8,
                             leading=10.8, textColor=GREEN_DARK),
    "code": ParagraphStyle("code", parent=ss["Normal"], fontName="Courier", fontSize=7.6,
                           leading=10.4, textColor=INK, backColor=GREEN_LIGHT,
                           borderColor=BORDER, borderWidth=0.5, borderPadding=5, spaceAfter=6),
    "note": ParagraphStyle("note", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=8.5,
                           leading=12, textColor=AMBER, backColor=colors.HexColor("#FFF7E8"),
                           borderColor=colors.HexColor("#F0D9A8"), borderWidth=0.5,
                           borderPadding=6, spaceBefore=4, spaceAfter=8),
}


def P(text, style="body"):
    return Paragraph(escape(str(text)), S[style])


def B(text, style="body"):
    return Paragraph("<b>%s</b>" % escape(str(text)), S[style])


def rich(text, style="body"):
    """Paragraph with intentional inline markup (caller must escape dynamic data)."""
    return Paragraph(text, S[style])


def C(text):
    """Monospaced block; newlines become explicit line breaks for ReportLab."""
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), S["code"])


def bullets(items, style="body"):
    return ListFlowable(
        [ListItem(P(x, style), leftIndent=12, value="bullet") for x in items],
        bulletType="bullet", start="square", leftIndent=14, bulletFontSize=6,
        spaceBefore=2, spaceAfter=6,
    )


def table(rows, widths, header=True, zebra=True, align_left=True):
    data = []
    for r_i, row in enumerate(rows):
        out = []
        for cell in row:
            if isinstance(cell, Paragraph):
                out.append(cell)
            else:
                out.append(P(cell, "cell_b" if (header and r_i == 0) else "cell"))
        data.append(out)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), GREEN_LIGHT),
                 ("LINEBELOW", (0, 0), (-1, 0), 0.8, GREEN)]
    if zebra:
        for i in range(1 if header else 0, len(data)):
            if i % 2 == (1 if header else 0):
                cmds.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FAFCFA")))
    t.setStyle(TableStyle(cmds))
    return t


def h(text):
    return Paragraph(escape(text), S["h1"])


def h2(text):
    return Paragraph(escape(text), S["h2"])


def decorate(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GREEN)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, PAGE_H - 34, PAGE_W - MARGIN, PAGE_H - 34)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(MARGIN, PAGE_H - 28, "RxBondhu | CoU AI Hackathon 2026")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 28, "Detailed Project Report")
    canvas.line(MARGIN, 34, PAGE_W - MARGIN, 34)
    canvas.drawString(MARGIN, 22, "Reading aid, not a doctor | github.com/SJesan/RxBondhu")
    canvas.drawRightString(PAGE_W - MARGIN, 22, "Page %d" % doc.page)
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=48, bottomMargin=44,
        title="RxBondhu - Detailed Project Report",
        author="M M Sadikul Islam Jesan (Solo)", subject="CoU AI Hackathon 2026",
    )
    story = []

    # ---------------- Cover ----------------
    story += [Spacer(1, 42 * mm), P("CoU AI Hackathon 2026 | Healthcare", "cover_sub"),
              Spacer(1, 5 * mm), P("RxBondhu", "cover_title"),
              P("Handwritten Prescription Reader", "cover_sub"),
              Spacer(1, 3 * mm),
              P("Detailed Project Report: from handwritten photo to verified Bangla schedule", "cover_sub"),
              Spacer(1, 14 * mm)]
    cover = [
        ["Team", "Solo - M M Sadikul Islam Jesan"],
        ["Built", "Fresh code written 21-22 November 2026; public repo and first commit on 21 Nov"],
        ["Core idea", "Two independent AI readers + verified brand list + human confirmation"],
        ["Own CNN", "EfficientNet-B0, 4,680 word images, 78 brands, held-out test accuracy 0.9590"],
        ["Live app", "https://rxbondhu.streamlit.app"],
        ["Source", "https://github.com/SJesan/RxBondhu"],
        ["Report date", "22 November 2026"],
    ]
    story += [table(cover, [105, CONTENT_W - 105], header=False, zebra=True), Spacer(1, 12 * mm)]
    story += [P("Prepared as a technical and rule-compliance record for judges and for future portfolio use. "
                "Every number comes from our own training run or our own integration checks.", "small")]
    story += [PageBreak()]

    # ---------------- Contents ----------------
    story += [h("Contents"), bullets([
        "1. Executive summary", "2. Problem and target user", "3. Objectives and scope",
        "4. Three-screen user journey", "5. Architecture and module map",
        "6. Reader 1 - our own trained CNN", "7. Reader 2 - Google Gemini with serial fallback",
        "8. Fusion and safety engineering", "9. Evaluation and proof",
        "10. Technology stack and repository", "11. Setup, tests and reproduction",
        "12. Deployment and rule compliance", "13. AI disclosure and credits",
        "14. Limitations and future work", "15. Three-minute demo script",
        "Appendix A - commit history", "Appendix B - judge question bank",
    ])]

    # ---------------- 1 ----------------
    story += [h("1. Executive summary")]
    story += [P("RxBondhu turns a photograph of a handwritten Bangladeshi prescription into a clear Bangla "
                "medicine schedule and spoken summary. It is deliberately a reading aid, not a doctor: it never "
                "diagnoses, prescribes, or checks drug interactions, and it never shows a final schedule before "
                "the user has reviewed every line.")]
    story += [P("The technical core is two independent AI readers looking at the same medicine crop. The first "
                "is a convolutional neural network that we trained ourselves from ImageNet-pretrained "
                "EfficientNet-B0 on 4,680 labelled handwritten medicine-word images across 78 brands, with a "
                "held-out test accuracy of 0.9590 (748 of 780 images). The second is Google Gemini Flash, called "
                "live through the Google Gen AI SDK with a serial fallback chain so one unavailable model does "
                "not break the reader.")]
    story += [P("Their answers are merged by a simple, explainable fusion rule into GREEN, YELLOW or RED badges. "
                "A verified brand-to-generic lexicon rejects invented names, catches duplicate generics such as "
                "Napa plus Ace (both Paracetamol), and all uncertain lines demand human confirmation.")]
    story += [P("The result is a three-screen Streamlit application (Photo, Reading, Schedule) running locally "
                "and publicly at https://rxbondhu.streamlit.app. The project was built from zero during the "
                "official pre-build window, with a public GitHub history, no committed secrets, and honest "
                "disclosure of every AI tool and model used.")]

    # ---------------- 2 ----------------
    story += [h("2. Problem and target user")]
    story += [P("In Bangladesh many prescriptions are still written by hand. A caregiver or patient can easily "
                "misread a brand name, a dose notation such as 1+0+1, BD, TDS or HS, or a Bangla evening-dose "
                "phrase. Two different brands can also contain the same generic drug, which a reader may not "
                "notice and which can lead to a double dose.")]
    story += [bullets([
        "Primary user: a patient or family caregiver who needs to understand the prescribed medicine schedule.",
        "Secondary user: a pharmacy or health worker who wants a quick second reading to check against the paper.",
        "Failure mode we target: a confident-looking but wrong reading being acted on without confirmation.",
        "Out of scope: diagnosis, choosing medicines, interaction checking, and replacing professional advice.",
    ])]
    story += [P("Design consequence: the app's safety is not a disclaimer added at the end. It is structural - "
                "crop first, read with two models, verify against a real-brand list, colour the disagreement, "
                "and require an explicit review action before any schedule appears.")]

    # ---------------- 3 ----------------
    story += [h("3. Objectives and scope")]
    story += [table([
        ["Priority", "Item", "Status on 22 Nov 2026"],
        ["MUST", "Own trained CNN with honest held-out accuracy", "Done - test 0.9590 (748/780)"],
        ["MUST", "Three-screen local app: Photo -> Reading -> Schedule", "Done - verified in browser and live"],
        ["MUST", "Gemini second reader plus fusion", "Done - 3-model serial fallback"],
        ["MUST", "Public GitHub repo, first commit 21 Nov, regular commits", "Done - no history rewrite"],
        ["MUST", "README with all required sections and disclosure", "Done - aligned to rulebook"],
        ["MUST", "Public live link or <=3 min demo video", "Done - live Streamlit Cloud link"],
        ["SHOULD", "Bangla audio", "Done - MMS-TTS with gTTS fallback"],
        ["SHOULD", "10-12 own handwritten prescriptions, CNN/Gemini/Combined table",
         "Pending - log template exists, rows still blank; no numbers invented"],
        ["SHOULD", "3-5 volunteer usability notes", "Pending - to collect at final"],
        ["CUT", "docTR, 20 prescriptions, 10 volunteers, extra brands, other providers",
         "Deliberately excluded to protect quality and sleep"],
    ], [58, 245, CONTENT_W - 303])]
    story += [P("Scope was cut on purpose. A smaller system that can be explained line by line scores better "
                "than a broad system the builder cannot defend.")]

    # ---------------- 4 ----------------
    story += [h("4. Three-screen user journey")]
    story += [table([
        ["Screen", "User action", "What the app does", "Safety gate"],
        ["1 - Photo", "Upload or take a prescription photo; drag a box around the medicine lines only.",
         "Stores the crop, shows a clean preview, and keeps the full photo available as context for Gemini.",
         "Cropping prevents unrelated text from being read as medicine."],
        ["2 - Reading", "Press 'Read with both AI models'.",
         "OpenCV groups handwriting into lines and word crops. Our CNN and Gemini read them independently. "
         "Results appear with GREEN / YELLOW / RED badges and a short reason line.",
         "No schedule is produced here. RED always says to confirm with a pharmacist."],
        ["3 - Schedule", "Confirm or correct each medicine name and dose; press 'Build my Bangla schedule'.",
         "Parses 1+0+1 / BD / TDS / HS and Bangla dose notes into a morning-noon-night table, warns on duplicate "
         "generics, and offers Bangla audio.",
         "The review action is mandatory - nothing reaches the schedule without it."],
    ], [64, 135, 168, CONTENT_W - 367])]
    story += [P("Navigation is a three-step indicator in the sidebar. The same sidebar reports model readiness "
                "live: 'CNN ready - test acc 0.959' and 'Gemini key: yes'.")]

    # ---------------- 5 ----------------
    story += [h("5. Architecture and module map")]
    story += [P("Flow: photo -> crop -> segmentation.py -> (recognizer.py CNN + vlm.py Gemini) -> "
                "lexicon.py -> fusion.py -> review -> dose_parser.py -> safety.py -> bangla.py / tts.py.")]
    story += [table([
        ["File", "Responsibility"],
        ["app.py", "Streamlit entrypoint; three screens, session state, sidebar status, UI event handling."],
        ["rxbondhu/image_transforms.py", "One shared 128x384 letterbox transform used in training and inference."],
        ["rxbondhu/segmentation.py", "OpenCV thresholding, contour grouping into lines and word crops."],
        ["rxbondhu/recognizer.py", "Loads our .pt checkpoint and labels, returns top-1/top-3 and confidence."],
        ["rxbondhu/vlm.py", "Gemini request, strict JSON parsing, serial model fallback, honest error text."],
        ["rxbondhu/lexicon.py", "Verified brand-to-generic list, normalisation and RapidFuzz fuzzy matching."],
        ["rxbondhu/fusion.py", "GREEN / YELLOW / RED decision and suggestion list."],
        ["rxbondhu/dose_parser.py", "Parses triplets, BD, TDS, HS and Bangla dose phrases."],
        ["rxbondhu/safety.py", "Duplicate-generic detection and RED-state warnings."],
        ["rxbondhu/bangla.py", "Builds the Bangla morning / noon / night table and spoken summary text."],
        ["rxbondhu/tts.py", "facebook/mms-tts-ben speech with gTTS fallback."],
        ["rxbondhu/ui.py", "Clean white / Bangla-green CSS, subtle 3D cards, local Three.js hero in an iframe."],
        ["rxbondhu/pipeline.py", "Orchestrates the modules for the reading and schedule screens."],
        ["training/train_cnn_kaggle.py", "Our complete Kaggle training and evaluation script."],
        ["tools/verify_model.py", "End-to-end model, fusion and Gemini smoke check."],
        ["tests/test_*.py", "29 unit tests across dose parsing, fusion, lexicon, safety, schedule and segmentation."],
    ], [150, CONTENT_W - 150])]

    # ---------------- 6 ----------------
    story += [h("6. Reader 1 - our own trained CNN")]
    story += [h2("6.1 Dataset and split")]
    story += [P("Public dataset: Doctor's Handwritten Prescription BD, Kaggle user mamun1113. The CSV labels "
                "join cropped word images by the MEDICINE_NAME column; bare image filenames were resolved against "
                "the matching training, validation and testing word folders.")]
    story += [table([
        ["Item", "Value"],
        ["Samples / classes", "4,680 word images / 78 brands"],
        ["Split", "3,120 train / 780 validation / 780 test (our own stratified split, seed 42)"],
        ["Input", "128 x 384 letterbox, identical transform in training and inference"],
        ["Base model", "EfficientNet-B0 with ImageNet weights (torchvision), fine-tuned by us"],
        ["Optimiser", "AdamW, learning rate 3e-4, cosine schedule"],
        ["Epochs / batch", "12 / 32"],
        ["Device / framework", "Kaggle GPU T4, torch 2.11.0+cu130"],
        ["Best validation accuracy", "0.9577"],
        ["Held-out test accuracy", "0.9590 (748 correct of 780)"],
    ], [145, CONTENT_W - 145])]
    story += [P("An earlier exploratory run classified dataset folder names instead of the labelled images. It "
                "was discarded and is not reported anywhere. Only the final run above is claimed.")]
    story += [h2("6.2 Artifacts and verification")]
    story += [bullets([
        "models/rx_cnn.pt - trained checkpoint (ours, committed); models/labels.json - 78 class names.",
        "models/test_report.csv - per-image true/predicted/confidence/correct rows; models/training_summary.txt - run metadata.",
        "results/kaggle_training_log.txt - the raw Kaggle log, including 'TEST ACCURACY: 0.9590 (748/780)'.",
        "tools/verify_model.py confirmed 78 classes, image size [128, 384], and the same 0.9590 metadata.",
        "The same transform module is imported by training and inference, so there is no train/serve mismatch.",
    ])]

    # ---------------- 7 ----------------
    story += [h("7. Reader 2 - Google Gemini with serial fallback")]
    story += [P("Gemini receives the crop (and the full prescription image for context) and is asked for a strict "
                "JSON array of medicine names and dose strings. The prompt forbids diagnosis, extra medicines and "
                "invented names; uncertain words must be marked with a trailing question mark.")]
    story += [h2("7.1 Serial model chain")]
    story += [table([
        ["Order", "Model", "Behaviour"],
        ["1", "gemini-2.5-flash", "Primary reader, highest-quality reading."],
        ["2", "gemini-3.5-flash-lite", "Used if the primary errors or returns an empty answer."],
        ["3", "gemini-3.1-flash-lite", "Final fallback on the same API key."],
    ], [40, 155, CONTENT_W - 195])]
    story += [P("One key serves all three models. A forced-failure test with an invalid first model confirmed "
                "that the chain silently moved to the next model and still returned Napa - 1+0+1 and Maxpro - BD. "
                "The model actually used is reported in the result. gemini-2.5-flash-lite was tested but is no "
                "longer available to new users, so it was replaced.")]
    story += [h2("7.2 Key handling")]
    story += [bullets([
        "Secrets are read from st.secrets first (Streamlit Cloud) and fall back to local .env / environment.",
        ".env and .streamlit/secrets.toml are git-ignored; .env.example and secrets.toml.example are committed.",
        "The key was pasted into chat during setup on 21 Nov and was therefore rotated on 22 Nov; the old key was deleted.",
        "No response is cached or hard-coded. If all models fail, the UI shows the real error and the CNN continues alone.",
    ])]

    # ---------------- 8 ----------------
    story += [h("8. Fusion and safety engineering")]
    story += [table([
        ["Badge", "Rule", "Meaning for the user"],
        ["GREEN", "Both readers are confident and agree (fuzzy brand match allowed).",
         "Highest-trust reading - still shown in review before any schedule is built."],
        ["YELLOW", "One reader is confident, or names agree after fuzzy correction but confidence is lower.",
         "Treat as a suggestion; choose the correct brand from the list."],
        ["RED", "Readers disagree, confidence is low, or the brand is not in the verified list.",
         "Do not trust automatically; please confirm with your pharmacist."],
    ], [58, 210, CONTENT_W - 268])]
    story += [P("Four independent safety layers surround fusion:")]
    story += [bullets([
        "Lexicon gate: only verified brand-to-generic rows are accepted; invented names such as Zzqqx are rejected (unit test).",
        "Fuzzy matching: a near miss such as Maxpo maps to Maxpro, but only if it is close to a real brand.",
        "Duplicate-generic warning: Napa and Ace both map to Paracetamol, so the schedule shows a warning instead of silently adding doses.",
        "Human-in-the-loop: the Review button is the only path to the schedule; RED lines are never auto-accepted.",
    ])]
    story += [P("Visible disclaimer on every screen: this is a reading aid, not a doctor. The app performs no "
                "diagnosis, no prescribing and no interaction checking. Images are used in the current session "
                "only; demo prescriptions are handwritten by the team and contain no real patient data.")]

    # ---------------- 9 ----------------
    story += [h("9. Evaluation and proof")]
    story += [h2("9.1 Held-out CNN accuracy (the only accuracy claim)")]
    story += [table([
        ["Metric", "Value", "Source"],
        ["Validation accuracy", "0.9577", "models/training_summary.txt"],
        ["Test accuracy", "0.9590", "748 / 780 rows in models/test_report.csv"],
    ], [125, 105, CONTENT_W - 230])]
    story += [h2("9.2 Live integration checks (not accuracy claims)")]
    story += [table([
        ["Check", "Observed result"],
        ["vlm.read(sample_ui_smoke.png) with gemini-2.5-flash", "Napa - 1+0+1; Maxpro - BD"],
        ["tools/verify_model.py after checkpoint added", "5 word crops; Napa YELLOW (cnn 0.411), Maxpro YELLOW (cnn 0.076), extra crops RED"],
        ["Public Streamlit Cloud app, 22 Nov 2026", "Sidebar: CNN ready - test acc 0.959; Gemini key: yes"],
        ["Unit tests", "29 / 29 passing (22 core, 5 pipeline, 2 segmentation)"],
    ], [210, CONTENT_W - 210])]
    story += [h2("9.3 Handwritten prescription comparison - PENDING")]
    story += [P("This table is intentionally blank. It must be filled only after 10-12 freshly handwritten "
                "volunteer prescriptions are tested with answer keys. No accuracy number has been invented.")]
    story += [table([
        ["Reader", "Correct / total", "Accuracy"],
        ["CNN only", "not measured yet", "-"],
        ["Gemini only", "not measured yet", "-"],
        ["Combined (RxBondhu, after user confirmation)", "not measured yet", "-"],
    ], [225, 120, CONTENT_W - 345])]
    story += [Paragraph("Log template: results/handwritten_test_log.csv. Keep the dataset test accuracy "
                        "(0.9590) separate from any future prescription-level accuracy.", S["note"])]

    # ---------------- 10 ----------------
    story += [h("10. Technology stack and repository")]
    story += [bullets([
        "Python 3.11; Streamlit and streamlit-cropper for the 3-screen UI.",
        "PyTorch / torchvision (CPU wheels on Cloud), OpenCV, Pillow, NumPy for vision.",
        "RapidFuzz for brand matching; pandas and matplotlib for reports; python-dotenv for local secrets.",
        "google-genai for Gemini; transformers for facebook/mms-tts-ben; gTTS as speech fallback; SciPy, uroman, tabulate as helpers.",
        "Kaggle T4 GPU for training; GitHub for public source; Streamlit Community Cloud for the free live link.",
    ])]
    story += [P("Repository structure (top level): app.py, README.md, RESOURCES.md, requirements.txt, "
                ".env.example, .gitignore, .streamlit/, rxbondhu/ (12 modules), training/ (script + notebook), "
                "models/ (checkpoint, labels, report, summary), results/ (training log + handwritten test log), "
                "tests/ (3 files), tools/verify_model.py, docs/, samples/, static/three.min.js, data/manual_brands.csv.")]

    # ---------------- 11 ----------------
    story += [h("11. Setup, tests and reproduction")]
    story += [P("Local run (Windows):"),
              C("python -m venv venv\n"
                "venv\\Scripts\\activate\n"
                "pip install -r requirements.txt\n"
                "copy .env.example .env        # paste GEMINI_API_KEY into .env only\n"
                "streamlit run app.py")]
    story += [P("Verification commands:"),
              C(".\\venv\\Scripts\\python.exe tests\\test_core.py\n"
                ".\\venv\\Scripts\\python.exe tests\\test_pipeline.py\n"
                ".\\venv\\Scripts\\python.exe tests\\test_segmentation.py\n"
                ".\\venv\\Scripts\\python.exe tools\\verify_model.py")]
    story += [P("Training reproduction on Kaggle (GPU T4, Internet On, dataset added as Input):"),
              C("!python /kaggle/working/RxBondhu/training/train_cnn_kaggle.py \\\n"
                "    --input /kaggle/input --output /kaggle/working \\\n"
                "    --epochs 12 --batch-size 32")]
    story += [P("Secrets for the live app are set in Streamlit Cloud -> Settings -> Secrets as TOML: "
                "GEMINI_API_KEY = \"...\" and RX_VLM_MODELS = \"gemini-2.5-flash, gemini-3.5-flash-lite, "
                "gemini-3.1-flash-lite\". Never place the real key in a repository file.")]

    # ---------------- 12 ----------------
    story += [h("12. Deployment and rule compliance")]
    story += [table([
        ["Rule", "Requirement", "Our position"],
        ["8", "Code only from 21 Nov; no old or copied project", "First commit 21 Nov; fresh build; reference zip never copied"],
        ["9", "Real AI only; disclose tools, models, APIs", "CNN + three Gemini models + OpenCode disclosed in README and section 13"],
        ["10", "One public repo, first commit on/after 21 Nov, regular commits, no history rewrite, .env.example",
         "github.com/SJesan/RxBondhu; 21-22 Nov history; no force-push, squash or back-date; .env.example present"],
        ["11", "Public live link from repo, or <=3 min real demo video", "https://rxbondhu.streamlit.app verified 22 Nov; video script kept as backup"],
        ["12", "Title + <=150 word description, repo link, live link, disclosure; submit >=10 min early",
         "All links public; no login so no credentials; final form to be submitted early on 24 Nov"],
        ["13", "No faked output, no rewritten history, no false information", "All numbers from our own logs; blank fields stay blank"],
        ["7", "Bring own laptop, charger, extension cord, student ID", "On-site runbook prepared for 24 Nov"],
    ], [36, 190, CONTENT_W - 226])]
    story += [P("Final-day runbook: arrive early for check-in with student ID; run the app locally with "
                "`streamlit run app.py`; demonstrate the three screens; commit at least hourly during the final; "
                "submit the form at least ten minutes before the official deadline; push the final commit before "
                "the deadline because the last commit is what is judged.")]

    # ---------------- 13 ----------------
    story += [h("13. AI disclosure and credits")]
    story += [table([
        ["Tool / asset", "Used for", "Where credited"],
        ["OpenCode (AI coding assistant, model Big Pickle)",
         "Planning, writing and debugging code, README and this report; step-by-step guidance.", "README section 4"],
        ["Google Gemini - gemini-2.5-flash, gemini-3.5-flash-lite, gemini-3.1-flash-lite",
         "Live in-app vision reader with serial fallback; no hard-coded output.", "README section 4, code vlm.py"],
        ["Doctor's Handwritten Prescription BD, Kaggle mamun1113",
         "Public training and evaluation dataset, 4,680 images / 78 brands.", "RESOURCES.md, README section 3"],
        ["EfficientNet-B0 (torchvision, ImageNet weights)",
         "Base of our own fine-tuned handwriting CNN.", "RESOURCES.md"],
        ["facebook/mms-tts-ben (CC-BY-NC-4.0) and gTTS", "Bangla speech and backup speech.", "RESOURCES.md"],
        ["OpenCV, PyTorch, RapidFuzz, Streamlit and other pip libraries",
         "Implemented under their own open-source licences, used as-is.", "RESOURCES.md, requirements.txt"],
    ], [170, 180, CONTENT_W - 350])]
    story += [P("No other AI assistant is claimed in this report. If another assistant was used for any part of "
                "the work, it must be added honestly to README section 4 before submission.")]

    # ---------------- 14 ----------------
    story += [h("14. Limitations and future work")]
    story += [bullets([
        "The verified brand lexicon currently has 18 seed brand-generic pairs; brands outside it are marked RED and need human confirmation.",
        "Handwriting styles are limited to what the public dataset and our own test samples cover; a tight crop materially improves results.",
        "Gemini needs internet and a valid key; the app degrades honestly to CNN-only when it is unavailable.",
        "Bangla speech depends on a downloaded MMS-TTS model or gTTS online; the text table always remains available.",
        "No drug-interaction, allergy, dose-range or patient-context checking is performed by design.",
        "Future: pharmacy-supervised pilot, more consented brand data, calibration of confidence thresholds, and optional medicine reminders.",
    ])]

    # ---------------- 15 ----------------
    story += [h("15. Three-minute demo script")]
    story += [table([
        ["Time", "Show", "Say"],
        ["0:00-0:20", "Problem slide", "Handwritten prescriptions can be misread; Napa and Ace are both Paracetamol. RxBondhu is a reading aid, not a doctor."],
        ["0:20-0:50", "Screen 1", "Upload the sample and crop only the medicine lines so the readers see only medicines."],
        ["0:50-1:30", "Screen 2", "Point to word crops, our own EfficientNet-B0 CNN, Gemini, and the GREEN/YELLOW/RED badges."],
        ["1:30-2:10", "Screen 3", "Confirm names and dose 1+0+1; show Bangla schedule and the duplicate-generic warning."],
        ["2:10-2:35", "Audio and proof", "Play Bangla audio, then show test accuracy 0.9590 and the evaluation file."],
        ["2:35-3:00", "Limits", "Limited brands and handwriting; every line is confirmed; no diagnosis or interaction checking."],
    ], [62, 92, CONTENT_W - 154])]
    story += [P("Full script: docs/DEMO_SCRIPT.md. Backup behaviour: no Gemini key means CNN-only, no CNN file "
                "means Gemini-only, and failed audio still leaves the Bangla table visible.")]

    # ---------------- Appendix A ----------------
    story += [PageBreak(), h("Appendix A - commit history")]
    story += [P("Public history as of 22 Nov 2026 (oldest first). No force-push, squash or back-dated commit "
                "was used; the Streamlit Cloud devcontainer commit was merged normally.")]
    commits = [
        ("fbaf282", "21 Nov", "Initial commit"),
        ("4cbe356", "21 Nov", "Fix segmentation line-box keyword in debug path"),
        ("cd9a2f1", "21 Nov", "Merge branch 'main' of GitHub repo"),
        ("52154bb", "21 Nov", "Add typed UI smoke-test sample"),
        ("566ac52", "21 Nov", "Add HF Space metadata and deployment guide"),
        ("f6740f9", "21 Nov", "Send full photo to Gemini for context"),
        ("88279ad", "21 Nov", "Add model verification tool, handwritten test log and live Gemini proof"),
        ("8b3ce75", "21 Nov", "Modern clean-white Bangla-green UI with local Three.js 3D hero"),
        ("8721bb5", "22 Nov", "Handle public Kaggle CSV layout and share letterbox transform"),
        ("18ee075", "22 Nov", "Match Kaggle CSV headers with spaces in column names"),
        ("515fa48", "22 Nov", "Add our trained CNN checkpoint and real evaluation results"),
        ("befe066", "22 Nov", "Use CPU PyTorch wheels"),
        ("97cffc3", "22 Nov", "Switch submission proof to demo video after HF Streamlit removal"),
        ("0819e19", "22 Nov", "Add Streamlit Cloud secrets support and free live-link guide"),
        ("9655743", "22 Nov", "Add verified live Streamlit URL to README"),
        ("2616a8b", "22 Nov", "Added Dev Container Folder (Streamlit Cloud)"),
        ("bf64dd9", "22 Nov", "Record verified live Streamlit deployment in evaluation"),
        ("f6f3b18", "22 Nov", "Merge Streamlit Cloud devcontainer config from remote"),
        ("d56c538", "22 Nov", "Add serial Gemini model fallback chain"),
        ("b8b664e", "22 Nov", "Align README with official rulebook submission requirements"),
    ]
    story += [table([["Commit", "Date", "Message"]] + [[a, b, c] for a, b, c in commits],
                    [62, 55, CONTENT_W - 117])]

    # ---------------- Appendix B ----------------
    story += [h("Appendix B - judge question bank")]
    story += [table([
        ["Question", "Short answer"],
        ["Why not just use Gemini?", "A general model can invent names and gives no honest confidence. We add our own CNN, a verified brand list and RED/YELLOW flags."],
        ["What data did you train on?", "Public Doctor's Handwritten Prescription BD dataset, 4,680 word images, 78 brands, credited in README."],
        ["Why EfficientNet-B0?", "Small, fast, strong transfer learning; 128x384 letterbox suits wide handwritten word crops."],
        ["How do you know it works?", "Held-out test accuracy 0.9590, plus live integration checks. Prescription-level table is left blank until really measured."],
        ["What if the AI is wrong?", "The user reviews every line; RED asks for pharmacist confirmation; no schedule appears before review."],
        ["What about brands outside the 78?", "Gemini may read them, but the lexicon marks them uncertain and the user must confirm."],
        ["Does it work offline?", "Everything except Gemini; the speech model is downloaded ahead of time, and a phone hotspot is a backup."],
        ["What did you personally do?", "Scope, safety design, dataset choice, training run, evaluation, test prescriptions, disclosure and final explanation."],
        ["What is next?", "Supervised pharmacy pilot, more consented data, calibrated thresholds and reminders."],
    ], [150, CONTENT_W - 150])]
    story += [Spacer(1, 6 * mm), HRFlowable(width="100%", color=BORDER), Spacer(1, 3 * mm),
              P("End of report. Source of truth: the public repository and the files it contains.", "small")]

    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    print("Wrote", OUT)


if __name__ == "__main__":
    build()
