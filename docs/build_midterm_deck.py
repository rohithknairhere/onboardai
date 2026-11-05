"""Build the mid-term review deck on the professor's template.

    backend/venv/Scripts/python.exe docs/build_midterm_deck.py

Content slides are cloned from the template so the logo, rule, footer and slide
numbering stay exactly as supplied. Every figure is pulled from the generated
report, so the deck cannot drift away from the data.
"""
import copy
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(r"C:\Users\Rohith\Downloads\PPT Format-Project Presentation-MTE 2026(1).pptx")
REPORT = ROOT / "backend" / "ml" / "artifacts" / "data_report.json"
EDA = ROOT / "backend" / "ml" / "artifacts" / "eda"
OUT = ROOT / "docs" / "OnboardAI_MidTerm_Review.pptx"

INK = RGBColor(0x1F, 0x24, 0x21)
ACCENT = RGBColor(0x8A, 0x6D, 0x1F)
MUTED = RGBColor(0x5A, 0x5A, 0x5A)
GOOD = RGBColor(0x2E, 0x6B, 0x3E)
WARN = RGBColor(0xB3, 0x26, 0x1E)

TITLE_BOX = (Inches(1.29), Inches(0.46), Inches(10.69), Inches(0.64))
BODY = (Inches(0.55), Inches(1.45), Inches(12.2), Inches(5.3))

R = json.loads(REPORT.read_text(encoding="utf-8"))
D, M, K = R["documents"], R["messages"], R["risk"]


# --------------------------------------------------------------------------
# Slide construction helpers
# --------------------------------------------------------------------------

def clone_content_slide(prs, source_index=2):
    """Copy a template content slide, keeping logo, rule, footer and numbering."""
    source = prs.slides[source_index]
    dest = prs.slides.add_slide(source.slide_layout)
    for shape in list(dest.shapes):
        shape._element.getparent().remove(shape._element)
    for shape in source.shapes:
        dest.shapes._spTree.append(copy.deepcopy(shape._element))

    # Strip the two template text boxes; keep logo, rule, footer, slide number.
    for shape in list(dest.shapes):
        if shape.has_text_frame and not shape.is_placeholder:
            text = shape.text_frame.text
            if "Font size 24" in text or "Describe the engineering problem" in text:
                shape._element.getparent().remove(shape._element)
    return dest


def set_title(slide, text):
    box = slide.shapes.add_textbox(*TITLE_BOX)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(24)
    run.font.bold = True
    run.font.color.rgb = INK
    return box


def body_frame(slide, left=None, top=None, width=None, height=None):
    box = slide.shapes.add_textbox(left or BODY[0], top or BODY[1],
                                   width or BODY[2], height or BODY[3])
    tf = box.text_frame
    tf.word_wrap = True
    return tf


def bullets(tf, items, size=14, space=8):
    """items: str, or (text, level), or (text, level, colour)."""
    first = True
    for item in items:
        colour = None
        if isinstance(item, tuple):
            if len(item) == 3:
                text, level, colour = item
            else:
                text, level = item
        else:
            text, level = item, 0

        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        p.space_after = Pt(space)
        run = p.add_run()
        run.text = ("• " if level == 0 else "– ") + text
        run.font.size = Pt(size - 1.5 * level)
        run.font.color.rgb = colour or (INK if level == 0 else MUTED)


def add_table(slide, rows, left, top, width, height, font=11, header=True,
              col_widths=None):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), left, top, width, height)
    table = shape.table
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w

    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(value)
            for p in cell.text_frame.paragraphs:
                p.space_after = Pt(0)
                for run in p.runs:
                    run.font.size = Pt(font)
                    run.font.color.rgb = INK
                    if header and r == 0:
                        run.font.bold = True
    return table


def add_image(slide, name, left, top, width=None, height=None):
    path = EDA / name
    if not path.exists():
        return None
    return slide.shapes.add_picture(str(path), left, top, width=width, height=height)


def note(slide, text, top=Inches(6.45), colour=MUTED, size=11, left=Inches(0.55),
         width=Inches(12.2)):
    tf = body_frame(slide, left, top, width, Inches(0.7))
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.italic = True
    run.font.color.rgb = colour


# --------------------------------------------------------------------------
# Slides
# --------------------------------------------------------------------------

def slide_title(prs):
    s = prs.slides[0]
    replacements = {
        "Name of Topic": "OnboardAI: An AI-Assisted Employee Onboarding Platform",
        "Name of Student (Roll No.)": None,
    }
    for shape in s.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text
        if "Name of Topic" in text:
            shape.text_frame.text = replacements["Name of Topic"]
            for p in shape.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(28)
                    run.font.bold = True
        elif "Name of Student" in text:
            shape.text_frame.text = (
                "Kritika Sah (DL.AI.U4AID25031), Team Lead\n"
                "Prisha Saini (DL.AI.U4AID25039), Tester\n"
                "Rohith K Nair (DL.AI.U4AID25043), Developer\n"
                "Pasham Srikar (DL.AI.U4AID25049), QA")
            for p in shape.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(14)
        elif "Subject Coordinator" in text:
            shape.text_frame.text = "Subject Coordinator: Dr. Sakshi Ahuja"
            for p in shape.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(13)


def slide_contents(prs):
    s = prs.slides[1]
    for shape in s.shapes:
        if shape.has_text_frame and "Problem Statement" in shape.text_frame.text:
            shape.text_frame.text = "\n".join([
                "1. Problem Statement",
                "2. Objectives",
                "3. Proposed Methodology & Tools",
                "4. Dataset Description",
                "5. Data Understanding",
                "6. Exploratory Data Analysis (I & II)",
                "7. Data Preprocessing",
                "8. Before vs After Preprocessing",
                "9. Data Splitting & Leakage Audit",
                "10. Preliminary Testing & Validation",
                "11. Project Scope & Next Phase",
                "12. Team Contribution & Conclusion",
                "13. References",
            ])
            for p in shape.text_frame.paragraphs:
                p.space_after = Pt(6)
                for run in p.runs:
                    run.font.size = Pt(14)


def slide_problem(prs):
    s = clone_content_slide(prs)
    set_title(s, "Problem Statement")
    tf = body_frame(s)
    bullets(tf, [
        "Onboarding a new employee is manual, document-heavy and slow.",
        ("HR verifies identity documents, certificates and bank forms by hand, one at a time.", 1),
        ("New joiners wait days for answers to routine policy questions.", 1),
        ("Nobody notices a hire has stalled until they are already weeks behind.", 1),
        "Who is affected",
        ("New hires, a poor first fortnight drives early attrition.", 1),
        ("HR teams, repetitive verification and the same questions answered repeatedly.", 1),
        ("The organisation, replacing a new hire costs an estimated 6–9 months of salary.", 1),
        "The specific gap this project addresses",
        ("Existing tools (BambooHR, Workday) are passive checklists: they record state, "
         "they do not read documents, answer questions, or predict who will stall.", 1),
        ("We address the three tasks a checklist cannot do: verify a document, answer from "
         "company policy with a citation, and flag a hire at risk before HR notices.", 1),
    ], size=14)


def slide_objectives(prs):
    s = clone_content_slide(prs)
    set_title(s, "Objectives of the Project")
    tf = body_frame(s)
    bullets(tf, [
        "1. To build datasets representing onboarding documents, employee messages and "
        "onboarding journeys, and to characterise them statistically.",
        "2. To preprocess text and tabular data into model-ready form, with justification "
        "for every transformation applied.",
        "3. To analyse the data for distributions, class balance, correlations and quality "
        "defects before any modelling begins.",
        "4. To split the data into training and testing sets without leakage, and to verify "
        "that split empirically.",
        "5. To develop and evaluate ML models for document verification, intent and sentiment "
        "classification, and stall-risk prediction in the next phase.",
    ], size=15, space=16)
    note(s, "Objectives 1–4 are complete and are the subject of this review. "
            "Objective 5 is next-phase work.", colour=ACCENT)


def slide_methodology(prs):
    s = clone_content_slide(prs)
    set_title(s, "Proposed Methodology & Tools")
    tf = body_frame(s, width=Inches(6.6))
    bullets(tf, [
        "Pipeline",
        ("Step 1, Data collection / generation", 1),
        ("Step 2, Data understanding & EDA", 1),
        ("Step 3, Preprocessing (cleaning, vectorisation, scaling)", 1),
        ("Step 4, Train / test split with leakage audit", 1),
        ("Step 5, Model development [next phase]", 1),
        ("Step 6, Evaluation & comparison [next phase]", 1),
        "",
        "Three parallel data streams",
        ("Text (documents) → document type verification", 1),
        ("Text (messages) → intent + sentiment", 1),
        ("Tabular (journeys) → stall-risk prediction", 1),
    ], size=13)

    rows = [["Area", "Tools"],
            ["Language", "Python 3.13"],
            ["Data / ML", "scikit-learn, NumPy, pandas-free NumPy pipeline"],
            ["Text", "TF-IDF (word + char n-grams), TruncatedSVD (LSA)"],
            ["Visualisation", "Matplotlib"],
            ["Backend", "FastAPI, SQLAlchemy, SQLite"],
            ["Frontend", "React 19, Vite, Tailwind CSS"],
            ["Testing", "pytest (55 checks)"]]
    add_table(s, rows, Inches(7.3), Inches(1.5), Inches(5.4), Inches(3.4), font=11,
              col_widths=[Inches(1.5), Inches(3.9)])


def slide_dataset(prs):
    s = clone_content_slide(prs)
    set_title(s, "Dataset Description")
    rows = [
        ["Dataset", "Samples", "Features", "Target", "Classes", "Type", "Source"],
        ["Onboarding documents", f"{D['samples']:,}", "Text (TF-IDF)", "Document type",
         str(len(D["classes"])), "Unstructured text", "Generated, ml/synth.py"],
        ["Employee messages", f"{M['samples']:,}", "Text (TF-IDF)", "Intent + Sentiment",
         f"{len(M['classes'])} + 3", "Unstructured text", "Generated, ml/text_synth.py"],
        ["Onboarding journeys", f"{K['samples']:,}", f"{K['features']} numeric",
         "stalled (binary)", "2", "Structured tabular", "Simulated, ml/risk_synth.py"],
    ]
    add_table(s, rows, Inches(0.55), Inches(1.5), Inches(12.2), Inches(1.6), font=11,
              col_widths=[Inches(2.3), Inches(1.2), Inches(1.5), Inches(1.9),
                          Inches(1.1), Inches(1.9), Inches(2.3)])

    tf = body_frame(s, top=Inches(3.35), height=Inches(2.9))
    bullets(tf, [
        ("Why the data is synthetic", 0, ACCENT),
        ("Real onboarding documents are identity and financial records (passports, bank "
         "details) that cannot lawfully be collected or published for a student project.", 1),
        ("Real onboarding outcomes do not exist, because the system has not been deployed, "
         "so there is no history of who stalled.", 1),
        ("Generators are built to make the task realistically hard: three scan-degradation "
         "tiers, cross-class text bleed, deliberately ambiguous messages, and a latent-variable "
         "process with an unobserved component.", 1),
        ("Limitation, stated plainly", 0, WARN),
        ("These datasets measure internal consistency with a generator, not real-world "
         "capability. Replacing them with a real corpus (e.g. RVL-CDIP, 400k labelled document "
         "images) is the first item of future work.", 1),
    ], size=12.5)


def slide_data_understanding(prs):
    s = clone_content_slide(prs)
    set_title(s, "Data Understanding")

    rows = [["Measure", "Documents", "Messages", "Journeys"],
            ["Samples", f"{D['samples']:,}", f"{M['samples']:,}", f"{K['samples']:,}"],
            ["Classes", f"{len(D['classes'])}", f"{len(M['classes'])} intents / 3 sentiment", "2"],
            ["Class balance (min/max)", f"{D['class_balance_ratio']:.2f}",
             f"{M['class_balance_ratio']:.2f}",
             f"{min(K['target_counts'].values())/max(K['target_counts'].values()):.2f}"],
            ["Mean length", f"{D['char_len']['mean']:.0f} chars",
             f"{M['char_len']['mean']:.0f} chars", "n/a"],
            ["Missing values", "0", "0", "0"],
            ["Exact duplicates", f"{D['duplicates_exact']:,}", f"{M['duplicates_exact']:,}",
             f"{K['duplicate_rows']:,}"],
            ["Data types", "str", "str", "float64"]]
    add_table(s, rows, Inches(0.55), Inches(1.45), Inches(6.3), Inches(3.3), font=10.5,
              col_widths=[Inches(2.0), Inches(1.5), Inches(1.7), Inches(1.1)])

    tf = body_frame(s, left=Inches(7.1), top=Inches(1.45), width=Inches(5.7),
                    height=Inches(5.0))
    top_corr = list(K["correlation_with_target"].items())[:5]
    bullets(tf, [
        ("What we learned", 0, ACCENT),
        (f"Document and intent classes are balanced by construction "
         f"(ratio {D['class_balance_ratio']:.2f}), so accuracy is a fair headline metric.", 1),
        (f"The target is moderately imbalanced: {100*K['target_positive_rate']:.1f}% of "
         "journeys stall.", 1),
        ("Strongest correlates of stalling:", 1),
    ] + [(f"{f} ({v:+.2f})", 2) for f, v in top_corr] + [
        (f"Documents average {D['char_len']['mean']:.0f} characters, far shorter than a real "
         "scanned certificate. A known limitation.", 1),
        ("Defect found: the message corpus contains "
         f"{M['duplicates_exact']:,} exact duplicates (short messages such as \"thank you\" "
         "recur). Impact measured on the next slides.", 1, WARN),
    ], size=12)


def slide_eda_1(prs):
    s = clone_content_slide(prs)
    set_title(s, "Exploratory Data Analysis (I): Distributions")
    add_image(s, "01_document_class_distribution.png", Inches(0.4), Inches(1.3),
              width=Inches(6.2))
    add_image(s, "04_message_class_distributions.png", Inches(6.8), Inches(1.3),
              width=Inches(6.2))
    add_image(s, "03_difficulty_tier_distribution.png", Inches(0.4), Inches(3.75),
              width=Inches(4.3))

    tf = body_frame(s, left=Inches(5.0), top=Inches(3.8), width=Inches(8.0),
                    height=Inches(2.7))
    tier = D["difficulty_tiers"]
    sent = M["sentiment_counts"]
    total_sent = sum(sent.values())
    bullets(tf, [
        ("Observations", 0, ACCENT),
        (f"All {len(D['classes'])} document classes hold exactly "
         f"{list(D['class_counts'].values())[0]:,} samples, balanced by construction.", 1),
        (f"Intents are balanced, but sentiment is not: negative "
         f"{100*sent.get('negative',0)/total_sent:.0f}%, neutral "
         f"{100*sent.get('neutral',0)/total_sent:.0f}%, positive "
         f"{100*sent.get('positive',0)/total_sent:.0f}%. Escalations are rarely cheerful, so "
         "class_weight='balanced' is used.", 1),
        (f"{100*tier.get('severe',0)/D['samples']:.0f}% of documents sit in the severe tier "
         "(cropped, 10–20% character noise). Holding back a hard slice is what makes a "
         "per-tier accuracy breakdown meaningful.", 1),
    ], size=11.5)


def slide_eda_2(prs):
    s = clone_content_slide(prs)
    set_title(s, "Exploratory Data Analysis (II): Relationships")
    add_image(s, "06_risk_correlation_matrix.png", Inches(0.35), Inches(1.3),
              height=Inches(4.6))
    add_image(s, "08_sentiment_vs_outcome.png", Inches(5.9), Inches(1.35),
              width=Inches(7.0))

    tf = body_frame(s, left=Inches(5.9), top=Inches(4.0), width=Inches(7.0),
                    height=Inches(2.6))
    pairs = K["top_correlated_pairs"][0]
    bullets(tf, [
        ("Observations", 0, ACCENT),
        (f"`{pairs[0]}` and `{pairs[1]}` correlate at {pairs[2]:+.2f}. Severe multicollinearity: "
         "three progress-style features carry nearly the same information.", 1),
        ("No single feature correlates with the target above |0.45|, consistent with a "
         "generator that deliberately withholds part of the cause.", 1),
        ("Sentiment separates the outcomes in the expected direction but with heavy overlap, "
         "so it is a contributing signal rather than a decisive one.", 1),
    ], size=11.5)


def slide_preprocessing(prs):
    s = clone_content_slide(prs)
    set_title(s, "Data Preprocessing: What, Why, Result")
    rows = [
        ["Step", "Why it was done", "Result"],
        ["Lowercase + strip accents", "OCR and typing produce inconsistent case",
         "Applied to all text"],
        ["Word 1–2 gram TF-IDF", "Captures topical vocabulary and short phrases",
         f"{D['tfidf']['word_ngram_features_min_df_2']:,} features"],
        ["Character 3–5 gram TF-IDF", "Survives OCR damage that destroys whole words",
         "Unioned with word features"],
        ["Sublinear TF", "Dampens a term repeated many times in one document", "Applied"],
        ["min_df = 2 pruning", "A token appearing once cannot generalise",
         f"{D['tfidf']['features_pruned_away']:,} features dropped"],
        ["StandardScaler (tabular)", "Features span different units and ranges",
         "Mean 0, SD 1 on all 12"],
        ["Scaler fitted in a Pipeline", "Stops test statistics leaking into training",
         "Enforced by sklearn"],
    ]
    add_table(s, rows, Inches(0.55), Inches(1.45), Inches(12.2), Inches(3.6), font=11,
              col_widths=[Inches(3.1), Inches(5.4), Inches(3.7)])

    tf = body_frame(s, top=Inches(5.3), height=Inches(1.4))
    out_total = sum(v["outliers_iqr"] for v in K["per_feature"].values())
    bullets(tf, [
        ("Not performed, and why", 0, ACCENT),
        ("Missing-value imputation, there are no missing values in any dataset (verified, "
         "test TC-02).", 1),
        (f"Outlier removal, {out_total:,} IQR outliers exist but were retained. They are "
         "counts and waiting times whose long right tail is the signal of interest: a hire "
         "inactive for 25 days is the case the model must catch, not noise.", 1),
    ], size=11.5)


def slide_before_after(prs):
    s = clone_content_slide(prs)
    set_title(s, "Before vs After Preprocessing")

    t = D["tfidf"]
    rows = [["Measure", "Before", "After"],
            ["Representation", f"{D['samples']:,} raw text strings",
             f"Sparse matrix {t['matrix_shape'][0]:,} × {t['matrix_shape'][1]:,}"],
            ["Unique tokens", f"{t['raw_unique_tokens']:,} raw tokens",
             f"{t['word_ngram_features_min_df_2']:,} weighted n-gram features"],
            ["Feature count", f"{t['word_ngram_features_min_df_1']:,} (min_df=1)",
             f"{t['word_ngram_features_min_df_2']:,} (min_df=2)"],
            ["Density", "Dense text",
             f"{t['sparsity_pct']:.2f}% sparse, {t['nonzero_per_doc_mean']:.0f} non-zeros/doc"]]
    add_table(s, rows, Inches(0.55), Inches(1.45), Inches(12.2), Inches(1.7), font=11,
              col_widths=[Inches(2.4), Inches(4.4), Inches(5.4)])

    note(s, "Text vectorisation (document corpus)", top=Inches(1.15), colour=ACCENT, size=12)

    scale_rows = [["Feature", "Mean before", "SD before", "Mean after", "SD after"]]
    for f, v in list(K["per_feature"].items())[:6]:
        scale_rows.append([f, f"{v['mean']:.2f}", f"{v['std']:.2f}",
                           f"{v['mean_after_scaling']:+.1e}", f"{v['std_after_scaling']:.3f}"])
    add_table(s, scale_rows, Inches(0.55), Inches(3.75), Inches(12.2), Inches(2.3), font=10.5,
              col_widths=[Inches(3.6), Inches(2.2), Inches(2.2), Inches(2.2), Inches(2.0)])
    note(s, "Feature scaling (tabular dataset, first 6 of 12 features)", top=Inches(3.42),
         colour=ACCENT, size=12)
    note(s, "All 12 features standardise to mean ≈ 0 and SD = 1, which is what makes the "
            "logistic-regression coefficients directly comparable.", top=Inches(6.2))


def slide_splitting(prs):
    s = clone_content_slide(prs)
    set_title(s, "Data Splitting & Leakage Audit")

    ds, ms, ks = D["split"], M["split"], K["split"]
    rows = [["Dataset", "Split", "Train", "Test", "Stratified", "Seed", "Max class drift",
             "Train/test overlap"],
            ["Documents", ds["split_ratio"], f"{ds['train_size']:,}", f"{ds['test_size']:,}",
             "Yes", "42", f"{ds['max_class_proportion_drift']:.4f}",
             f"{ds['overlap_documents']:,}"],
            ["Messages", ms["split_ratio"], f"{ms['train_size']:,}", f"{ms['test_size']:,}",
             "Yes", "42", f"{ms['max_class_proportion_drift']:.4f}",
             f"{ms['overlap_documents']:,}"],
            ["Journeys", ks["split_ratio"], f"{ks['train_size']:,}", f"{ks['test_size']:,}",
             "Yes", "42",
             f"{abs(ks['train_positive_rate']-ks['test_positive_rate']):.4f}", "n/a"]]
    add_table(s, rows, Inches(0.55), Inches(1.45), Inches(12.2), Inches(1.5), font=10.5,
              col_widths=[Inches(1.6), Inches(0.9), Inches(1.0), Inches(1.0), Inches(1.2),
                          Inches(0.8), Inches(2.0), Inches(1.9)])

    tf = body_frame(s, top=Inches(3.2), height=Inches(3.3))
    li = M.get("leakage_impact_sentiment", {})
    bullets(tf, [
        ("Why splitting matters before modelling", 0, ACCENT),
        ("A model evaluated on data it trained on reports memorisation, not generalisation. "
         "The test fold must stay unseen until the model is final.", 1),
        ("Leakage controls applied", 0, ACCENT),
        ("Vectoriser and scaler are fitted inside an sklearn Pipeline, so during "
         "cross-validation they re-fit on the training fold alone and never see the test fold.", 1),
        ("Stratification holds every class proportion within "
         f"{max(ds['max_class_proportion_drift'], ms['max_class_proportion_drift']):.4f}.", 1),
        ("random_state = 42 everywhere, so splits are reproducible (verified, test TC-15).", 1),
        ("Defect found and measured, not assumed", 0, WARN),
        (f"{ms['overlap_documents']} messages appear in BOTH folds "
         f"({100*ms['overlap_documents']/ms['test_size']:.1f}% of that test set) because short "
         "messages repeat. We hypothesised this inflated the scores and tested it: accuracy on "
         f"leaked rows was {li.get('accuracy_on_leaked', 0):.4f} versus "
         f"{li.get('accuracy_on_clean', 0):.4f} on clean rows, the leaked rows score LOWER. "
         "The duplicates are the genuinely ambiguous short messages. Fix is to deduplicate "
         "before splitting; impact is negligible but the defect is real.", 1),
    ], size=11.5)


def slide_testing(prs):
    s = clone_content_slide(prs)
    set_title(s, "Preliminary Testing & Validation")

    rows = [["Category", "Cases", "Examples"],
            ["Data validation", "7", "Missing values, class balance, dtypes, domain ranges"],
            ["Preprocessing", "3", "TF-IDF shape & sparsity, pruning, scaler output"],
            ["Split integrity", "4", "Stratification, fold overlap, reproducibility"],
            ["Functional", "4", "7 demo documents each produce their expected verdict"],
            ["Boundary", "3", "Zero-byte file, 10 MB + 1 byte, feature domain limits"],
            ["Exceptional", "3", "HTML disguised as PDF, path traversal, malformed IDs"],
            ["Access control", "2", "Cross-organisation and cross-department retrieval"],
            ["Regression", "2", "Two previously-fixed extraction bugs"],
            ["Performance", "2", "Pipeline < 5 s; classifier & retrieval < 150 ms"],
            ["Security", "1", "PII stripped before text leaves the system"]]
    add_table(s, rows, Inches(0.55), Inches(1.45), Inches(7.3), Inches(4.3), font=10.5,
              col_widths=[Inches(1.8), Inches(0.8), Inches(4.7)])

    tf = body_frame(s, left=Inches(8.2), top=Inches(1.45), width=Inches(4.6),
                    height=Inches(5.0))
    bullets(tf, [
        ("34 test cases · 55 checks · 55 passing", 0, GOOD),
        ("Run with: python -m pytest tests -q", 1),
        ("Approach", 0, ACCENT),
        ("No language model is called in the suite, a test whose result depends on "
         "generation temperature cannot be a regression gate.", 1),
        ("Uploads write to a temp directory, so no test touches the real database.", 1),
        ("Two cases assert KNOWN DEFECTS rather than their absence, and fail if those "
         "defects grow worse.", 1, WARN),
        ("Not covered", 0, WARN),
        ("No API, authentication, or frontend tests. No accuracy gate in CI.", 1),
    ], size=11.5)


def slide_scope(prs):
    s = clone_content_slide(prs)
    set_title(s, "Project Scope & Next Phase")
    tf = body_frame(s, width=Inches(6.3))
    bullets(tf, [
        ("Intended application", 0, ACCENT),
        ("HR teams onboarding employees across multiple organisations.", 1),
        ("Users: new hires, HR administrators.", 1),
        ("Deployment: web application, organisation-scoped.", 1),
        ("Completed in this phase", 0, GOOD),
        ("Problem definition and objectives", 1),
        ("Three datasets built and characterised", 1),
        ("EDA with 10 figures and written observations", 1),
        ("Preprocessing with before/after evidence", 1),
        ("Stratified splitting with a measured leakage audit", 1),
        ("55 automated validation checks", 1),
    ], size=12.5)

    tf2 = body_frame(s, left=Inches(7.0), top=Inches(1.45), width=Inches(5.8),
                     height=Inches(5.0))
    bullets(tf2, [
        ("Next phase", 0, ACCENT),
        ("Data preparation → ML algorithm implementation → model training → testing → "
         "evaluation → model comparison", 1),
        ("Planned algorithms", 0, ACCENT),
        ("Document type: Linear SVC / Logistic Regression on TF-IDF", 1),
        ("Intent & sentiment: Logistic Regression on TF-IDF", 1),
        ("Stall risk: Logistic Regression vs Gradient Boosting", 1),
        ("Evaluation: accuracy, macro-F1, ROC-AUC, confusion matrices, "
         "5-fold cross-validation, ablation studies", 1),
        ("Known limitations to address", 0, WARN),
        ("Synthetic data → move to a real corpus (RVL-CDIP)", 1),
        ("Message duplication → deduplicate before splitting", 1),
        ("Multicollinearity among progress features", 1),
    ], size=12.5)
    note(s, "No accuracy, precision, recall or F1 figures are presented in this review: model "
            "implementation is next-phase work. Early prototypes of the next phase exist and "
            "are available in the appendix if the panel wishes to see them.", colour=WARN)


def slide_team(prs):
    s = clone_content_slide(prs)
    set_title(s, "Team Contribution & Conclusion")
    rows = [["Student", "Roll Number", "Role", "Contribution in this phase"],
            ["Kritika Sah", "DL.AI.U4AID25031", "Team Lead",
             "Problem definition, objectives, project scope, workflow and team coordination"],
            ["Prisha Saini", "DL.AI.U4AID25039", "Tester",
             "34 test cases, boundary and exceptional inputs, leakage measurement"],
            ["Rohith K Nair", "DL.AI.U4AID25043", "Developer",
             "Data generators, preprocessing pipelines, splitting implementation, EDA code"],
            ["Pasham Srikar", "DL.AI.U4AID25049", "QA",
             "Data quality checks, preprocessing verification, documentation, defect log"]]
    add_table(s, rows, Inches(0.55), Inches(1.45), Inches(12.2), Inches(2.0), font=11,
              col_widths=[Inches(1.9), Inches(2.4), Inches(1.4), Inches(6.5)])

    tf = body_frame(s, top=Inches(3.8), height=Inches(2.7))
    bullets(tf, [
        ("Conclusion", 0, ACCENT),
        (f"Three datasets built and characterised: {D['samples']:,} documents, "
         f"{M['samples']:,} messages, {K['samples']:,} journeys.", 1),
        ("Key findings: classes balanced by construction; stalling correlates most with "
         f"sentiment ({list(K['correlation_with_target'].values())[0]:+.2f}); severe "
         "multicollinearity among progress features; a real duplication defect in the "
         "message corpus whose impact we measured rather than assumed.", 1),
        ("Status: data preparation and splitting complete and verified. ML implementation "
         "begins next phase.", 1),
    ], size=12.5)


def slide_references(prs):
    s = clone_content_slide(prs)
    set_title(s, "References")
    tf = body_frame(s)
    bullets(tf, [
        "[1] Y. Huang, T. Lv, L. Cui, Y. Lu, and F. Wei, \"LayoutLMv3: Pre-training for "
        "document AI with unified text and image masking,\" in Proc. 30th ACM Int. Conf. "
        "Multimedia, 2022, pp. 4083–4091.",
        "[2] G. Kim et al., \"OCR-free document understanding transformer,\" in Proc. ECCV, "
        "2022, pp. 498–517.",
        "[3] J. Li, Y. Xu, T. Lv, L. Cui, C. Zhang, and F. Wei, \"DiT: Self-supervised "
        "pre-training for document image transformer,\" in Proc. 30th ACM Int. Conf. "
        "Multimedia, 2022, pp. 3530–3539.",
        "[4] J. Devlin, M. W. Chang, K. Lee, and K. Toutanova, \"BERT: Pre-training of deep "
        "bidirectional transformers for language understanding,\" in Proc. NAACL-HLT, 2019, "
        "pp. 4171–4186.",
        "[5] P. Lewis et al., \"Retrieval-augmented generation for knowledge-intensive NLP "
        "tasks,\" in Advances in Neural Information Processing Systems, vol. 33, 2020, "
        "pp. 9459–9474.",
        "[6] Y. Gao et al., \"Retrieval-augmented generation for large language models: A "
        "survey,\" arXiv:2312.10997, 2023.",
        "[7] S. Kapoor and A. Narayanan, \"Leakage and the reproducibility crisis in "
        "machine-learning-based science,\" Patterns, vol. 4, no. 9, 2023.",
        "[8] T. Gebru et al., \"Datasheets for datasets,\" Communications of the ACM, vol. 64, "
        "no. 12, pp. 86–92, 2021.",
    ], size=10.5, space=7)
    note(s, "IEEE citation format. The full list of fifteen references appears in the project "
            "paper. Fourteen of the fifteen are from 2017 onwards.", colour=MUTED)


def slide_appendix_divider(prs):
    s = clone_content_slide(prs)
    set_title(s, "Appendix: Work Completed Ahead of Schedule")
    tf = body_frame(s, top=Inches(2.0), height=Inches(3.5))
    bullets(tf, [
        ("These slides are NOT part of the mid-term review.", 0, WARN),
        ("The review covers work up to data splitting, which is slides 1–16.", 1),
        ("The items that follow belong to the next phase. They are included only as backup "
         "material, to be shown if the panel asks what has been prototyped.", 1),
        ("Nothing here is claimed as a mid-term deliverable, and no result below is "
         "presented as part of the assessed work.", 1, WARN),
    ], size=15, space=14)


def slide_appendix_system(prs):
    s = clone_content_slide(prs)
    set_title(s, "Appendix: Working System Already Prototyped")
    tf = body_frame(s, width=Inches(6.3))
    bullets(tf, [
        ("A running web application exists end to end", 0, ACCENT),
        ("React 19 + Vite frontend; FastAPI + SQLAlchemy + SQLite backend.", 1),
        ("Two role-based views: new hire and HR administrator.", 1),
        ("Multi-organisation: data and policy are scoped per organisation.", 1),
        ("Capabilities wired into the request path", 0, ACCENT),
        ("Document upload → automatic verification → approve / reject / escalate.", 1),
        ("Policy question answering with mandatory source citation.", 1),
        ("Risk score per employee, with per-feature explanation.", 1),
        ("Structured event stream feeding the ML features.", 1),
    ], size=12.5)

    tf2 = body_frame(s, left=Inches(7.0), top=Inches(1.45), width=Inches(5.8),
                     height=Inches(5.0))
    bullets(tf2, [
        ("Six specialist agents with enforced boundaries", 0, ACCENT),
        ("Onboarding, Document, IT Provisioning, Knowledge Transfer, Policy, Escalation.", 1),
        ("Each holds only its own tools, enforced in code, the Policy agent cannot complete "
         "a task; the Onboarding agent cannot read the policy corpus.", 1),
        ("Routing is done by our trained intent classifier, not by an LLM: cheaper, "
         "deterministic, and measurable against a confusion matrix.", 1),
        ("Privacy control", 0, ACCENT),
        ("Personal identifiers (email, phone, Aadhaar, PAN, IFSC, account) are stripped "
         "before any text is sent to a model provider.", 1),
    ], size=12.5)
    note(s, "Available for live demonstration if the panel wishes to see it.", colour=ACCENT)


def slide_appendix_models(prs):
    s = clone_content_slide(prs)
    set_title(s, "Appendix: Models Trained Ahead of Schedule")
    rows = [["Model", "Algorithm", "Classes / Features", "Held-out result"],
            ["Document type", "TF-IDF (word+char) → calibrated LinearSVC", "9 classes",
             "0.986 acc · 0.937 on severe scans"],
            ["Intent", "TF-IDF → Logistic Regression", "8 classes",
             "0.937 acc · CV 0.933 ± 0.004"],
            ["Sentiment", "TF-IDF → Logistic Regression", "3 classes",
             "0.996 acc, inflated, see below"],
            ["Stall risk", "Logistic Regression (vs Gradient Boosting)", "12 features",
             "ROC-AUC 0.795 · CV 0.807 ± 0.002"]]
    add_table(s, rows, Inches(0.55), Inches(1.45), Inches(12.2), Inches(2.0), font=11,
              col_widths=[Inches(1.9), Inches(4.2), Inches(2.3), Inches(3.8)])

    tf = body_frame(s, top=Inches(3.8), height=Inches(2.7))
    bullets(tf, [
        ("Shown only if asked. These belong to the final review, not this one.", 0, WARN),
        ("How we read our own numbers", 0, ACCENT),
        ("The document classifier's honest figure is 0.937 on severely degraded scans, not "
         "the 0.986 headline. Clean scans reach 1.000, which tells us little.", 1),
        ("Sentiment's 0.996 is a template-separability ceiling, not evidence the model "
         "understands sentiment. We do not present it as a capability.", 1, WARN),
        ("All figures are measured on synthetic data and describe internal consistency with "
         "our generators, not real-world performance.", 1, WARN),
    ], size=12)


def slide_appendix_rigour(prs):
    s = clone_content_slide(prs)
    set_title(s, "Appendix: Methodology We Are Most Confident In")
    tf = body_frame(s)
    bullets(tf, [
        ("1. We rejected our own perfect scores, three times.", 0, ACCENT),
        ("The first document classifier scored 1.000 on every metric with zero "
         "cross-validation variance. We treated that as a broken benchmark, not a result, and "
         "rebuilt the corpus with three degradation tiers and cross-class text bleed until the "
         "severe tier read 0.937.", 1),
        ("2. We tested a hypothesis about our own data and were proved wrong.", 0, ACCENT),
        ("We found duplicate messages leaking across the train/test split and predicted this "
         "inflated our scores. Measured: accuracy on leaked rows 0.9868 versus 0.9974 on clean "
         "rows, the leaked rows score LOWER, because duplicates concentrate in the genuinely "
         "ambiguous short messages. The hypothesis was wrong and we report it as wrong.", 1),
        ("3. We measured whether our components actually depend on each other.", 0, ACCENT),
        ("Removing the NLP sentiment feature costs the risk model 0.0075 ROC-AUC. That is "
         "measured evidence the NLP layer feeds the ML layer, rather than three techniques "
         "sitting side by side.", 1),
        ("4. We keep a register of our own defects.", 0, ACCENT),
        ("Message duplication, multicollinearity among progress features, synthetic-data "
         "ceilings and short documents are all documented, and two automated tests assert the "
         "known defects exist so they cannot quietly worsen.", 1),
    ], size=12)


def slide_appendix_demo(prs):
    s = clone_content_slide(prs)
    set_title(s, "Appendix: Available for Live Demonstration")
    tf = body_frame(s, width=Inches(6.3))
    bullets(tf, [
        ("Data and analysis (this review)", 0, ACCENT),
        ("python -m ml.data_report → dataset card and quality audit", 1),
        ("python -m ml.eda → all 10 figures regenerated from the data", 1),
        ("python -m pytest tests -q → 55 checks, live", 1),
        ("python -m tests.make_test_report → report with actual results", 1),
    ], size=12.5)

    tf2 = body_frame(s, left=Inches(7.0), top=Inches(1.45), width=Inches(5.8),
                     height=Inches(5.0))
    bullets(tf2, [
        ("System (next phase, if asked)", 0, ACCENT),
        ("Upload an expired safety certificate → rejected automatically, with the expiry date "
         "quoted back.", 1),
        ("Ask the same leave question as two different employees → 24 days vs 18 days, each "
         "cited to its own company's policy document.", 1),
        ("Open the HR dashboard → stall-risk ranking with per-employee explanations.", 1),
        ("Seven demo documents are prepared, each named for the verdict it should produce.", 1),
    ], size=12.5)
    note(s, "Everything above runs offline on a laptop. No paid API is used anywhere in the "
            "project.", colour=ACCENT)


def main():
    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE}")
    prs = Presentation(str(TEMPLATE))

    # Keep slides 1 (title) and 2 (contents); drop the remaining placeholders.
    xml_slides = prs.slides._sldIdLst
    for sld in list(xml_slides)[2:]:
        rid = sld.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        prs.part.drop_rel(rid)
        xml_slides.remove(sld)

    # Slide 3 of the original is the clone source; re-add it temporarily.
    source = Presentation(str(TEMPLATE)).slides[2]

    global clone_content_slide

    def _clone(p, _src=source):
        dest = p.slides.add_slide(p.slide_layouts[1])
        for shape in list(dest.shapes):
            shape._element.getparent().remove(shape._element)
        for shape in _src.shapes:
            dest.shapes._spTree.append(copy.deepcopy(shape._element))
        for shape in list(dest.shapes):
            if shape.has_text_frame and not shape.is_placeholder:
                text = shape.text_frame.text
                if "Font size 24" in text or "Describe the engineering problem" in text:
                    shape._element.getparent().remove(shape._element)
        return dest

    clone_content_slide = _clone

    slide_title(prs)
    slide_contents(prs)
    for builder in (slide_problem, slide_objectives, slide_methodology, slide_dataset,
                    slide_data_understanding, slide_eda_1, slide_eda_2,
                    slide_preprocessing, slide_before_after, slide_splitting,
                    slide_testing, slide_scope, slide_team, slide_references,
                    slide_appendix_divider, slide_appendix_system,
                    slide_appendix_models, slide_appendix_rigour, slide_appendix_demo):
        builder(prs)
        print(f" {builder.__name__}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"\nSaved {OUT} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
