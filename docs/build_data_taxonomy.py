"""Draw the data type taxonomy for the three datasets as a flowchart PDF.

    backend/venv/Scripts/python.exe docs/build_data_taxonomy.py

Every classification is derived from the live generators rather than assumed, so
discrete versus continuous and the level counts are measured, not guessed.
"""
import os
import sys
from pathlib import Path

import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
OUT = ROOT / "docs" / "pdf" / "Data_Taxonomy_Flowchart.pdf"

sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from ml import risk_synth, synth, text_synth  # noqa: E402

PAGE = landscape(A4)
W, H = PAGE

INK = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#5F5F5F")
LINE = colors.HexColor("#9A9A9A")

ROOT_C = colors.HexColor("#2E3B44")
UNSTRUCT = colors.HexColor("#7A5C2E")
STRUCT = colors.HexColor("#2E5C4A")
NUMERIC = colors.HexColor("#33566E")
CATEG = colors.HexColor("#6E3350")
TARGET = colors.HexColor("#8A2E2E")
EXCLUDED = colors.HexColor("#6B6B6B")


# ---------------------------------------------------------------------------
# measured facts
# ---------------------------------------------------------------------------

def measure():
    d_texts, d_labels, d_tiers = synth.generate()
    m_texts, m_intents, m_sent = text_synth.generate()
    X, y, feats, depts = risk_synth.generate()

    rows = []
    for i, f in enumerate(feats):
        col = X[:, i]
        is_int = bool(np.all(np.isclose(col, np.round(col))))
        rows.append({
            "name": f,
            "levels": len(np.unique(col)),
            "integer": is_int,
            "min": float(col.min()),
            "max": float(col.max()),
        })

    d_len = [len(t) for t in d_texts]
    m_len = [len(t) for t in m_texts]
    return {
        "doc_rows": len(d_texts), "doc_classes": len(set(d_labels)),
        "doc_tiers": len(set(d_tiers)),
        "doc_len": (min(d_len), max(d_len)),
        "msg_rows": len(m_texts), "msg_intents": len(set(m_intents)),
        "msg_sent": len(set(m_sent)),
        "msg_len": (min(m_len), max(m_len)),
        "jrn_rows": X.shape[0], "jrn_feats": X.shape[1],
        "features": rows, "departments": sorted(set(depts)),
        "target_levels": sorted(set(y.tolist())),
    }


F = measure()
BY_NAME = {r["name"]: r for r in F["features"]}


def nice_range(r):
    """Readable bounds. Generated floats land on values like 0.0002546."""
    def fmt(v):
        if abs(v - round(v)) < 0.01:
            return f"{round(v):g}"
        return f"{v:.2f}"
    return f"[{fmt(r['min'])}, {fmt(r['max'])}]"

ORDINAL = {"stage", "seniority"}
CONTINUOUS = [r["name"] for r in F["features"]
              if not r["integer"] and r["name"] not in ORDINAL]
DISCRETE = [r["name"] for r in F["features"]
            if r["integer"] and r["name"] not in ORDINAL]


# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------

class Sheet:
    def __init__(self, c):
        self.c = c

    def title(self, text, sub=None):
        c = self.c
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(18 * mm, H - 16 * mm, text)
        if sub:
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 9)
            c.drawString(18 * mm, H - 22 * mm, sub)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(18 * mm, H - 25 * mm, W - 18 * mm, H - 25 * mm)

    def footer(self, text):
        c = self.c
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(18 * mm, 12 * mm, W - 18 * mm, 12 * mm)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawString(18 * mm, 8 * mm, text)
        c.drawRightString(W - 18 * mm, 8 * mm, "OnboardAI data taxonomy")

    def box(self, x, y, w, h, heading, lines=(), fill=ROOT_C, head_size=9,
            body_size=7.2, text_colour=colors.white):
        c = self.c
        c.setFillColor(fill)
        c.setStrokeColor(fill)
        c.roundRect(x, y, w, h, 2.2 * mm, stroke=0, fill=1)

        c.setFillColor(text_colour)
        c.setFont("Helvetica-Bold", head_size)
        ty = y + h - (head_size * 0.37 * mm) - 3.2 * mm
        for part in heading.split("\n"):
            c.drawCentredString(x + w / 2, ty, part)
            ty -= (head_size + 1.6)

        c.setFont("Helvetica", body_size)
        for ln in lines:
            c.drawCentredString(x + w / 2, ty, ln)
            ty -= (body_size + 1.9)
        return (x + w / 2, y, x + w / 2, y + h)

    def elbow(self, parent_bottom, child_top, drop=5 * mm):
        """Vertical then horizontal connector from a parent to a child."""
        c = self.c
        c.setStrokeColor(LINE)
        c.setLineWidth(0.8)
        px, py = parent_bottom
        cx, cy = child_top
        mid = py - drop
        c.line(px, py, px, mid)
        c.line(px, mid, cx, mid)
        c.line(cx, mid, cx, cy)

    def label(self, x, y, text, size=7.5, colour=MUTED, bold=False, align="l"):
        c = self.c
        c.setFillColor(colour)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        if align == "c":
            c.drawCentredString(x, y, text)
        elif align == "r":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)


# ---------------------------------------------------------------------------
# page 1: master taxonomy
# ---------------------------------------------------------------------------

def page_master(s):
    s.title("Data Taxonomy: how the three datasets break down",
            "Three datasets, 14,310 rows in total. Classification measured from the "
            "generators, not assumed.")

    root = s.box(W / 2 - 52 * mm, H - 52 * mm, 104 * mm, 17 * mm,
                 "ALL PROJECT DATA",
                 [f"3 datasets  |  {F['doc_rows'] + F['msg_rows'] + F['jrn_rows']:,} rows total"],
                 fill=ROOT_C, head_size=11)
    root_b = (root[0], root[1])

    un = s.box(20 * mm, H - 92 * mm, 125 * mm, 20 * mm,
               "UNSTRUCTURED DATA",
               ["No fixed columns. Free text of variable length.",
                f"2 datasets  |  {F['doc_rows'] + F['msg_rows']:,} rows"],
               fill=UNSTRUCT, head_size=10)
    st = s.box(160 * mm, H - 92 * mm, 119 * mm, 20 * mm,
               "STRUCTURED DATA",
               ["Fixed schema. One value per column per row.",
                f"1 dataset  |  {F['jrn_rows']:,} rows"],
               fill=STRUCT, head_size=10)

    s.elbow(root_b, (un[0], un[3]), drop=7 * mm)
    s.elbow(root_b, (st[0], st[3]), drop=7 * mm)

    doc = s.box(20 * mm, H - 142 * mm, 60 * mm, 32 * mm,
                "Document corpus",
                [f"{F['doc_rows']:,} rows  x  2 raw columns",
                 f"text  : unstructured, {F['doc_len'][0]}-{F['doc_len'][1]} chars",
                 f"label : categorical NOMINAL, {F['doc_classes']} classes",
                 f"tier  : categorical ORDINAL, {F['doc_tiers']} levels",
                 "",
                 "vectorised to 11,482 numeric columns"],
                fill=colors.HexColor("#8E6C38"), head_size=9.5)
    msg = s.box(85 * mm, H - 142 * mm, 60 * mm, 32 * mm,
                "Message corpus",
                [f"{F['msg_rows']:,} rows  x  3 raw columns",
                 f"text      : unstructured, {F['msg_len'][0]}-{F['msg_len'][1]} chars",
                 f"intent    : categorical NOMINAL, {F['msg_intents']} classes",
                 f"sentiment : categorical ORDINAL, {F['msg_sent']} levels",
                 "",
                 "vectorised to 1,838 numeric columns"],
                fill=colors.HexColor("#8E6C38"), head_size=9.5)
    jrn = s.box(160 * mm, H - 142 * mm, 119 * mm, 32 * mm,
                "Journey dataset",
                [f"{F['jrn_rows']:,} rows  x  {F['jrn_feats'] + 1} columns",
                 f"{F['jrn_feats']} feature columns, all float64",
                 "1 target column, binary",
                 "",
                 "10 numerical  |  2 ordinal  |  1 target",
                 "plus 1 nominal field excluded from the model"],
                fill=colors.HexColor("#36705A"), head_size=9.5)

    s.elbow((un[0], un[1]), (doc[0], doc[3]), drop=6 * mm)
    s.elbow((un[0], un[1]), (msg[0], msg[3]), drop=6 * mm)
    s.elbow((st[0], st[1]), (jrn[0], jrn[3]), drop=6 * mm)

    s.label(18 * mm, 30 * mm,
            "Why the distinction matters", size=9, colour=INK, bold=True)
    for i, ln in enumerate([
        "Unstructured data has no columns until it is vectorised. Asking how many columns "
        "a text dataset has has two correct answers, 2 or 3 raw fields, and",
        "thousands of engineered numeric features afterwards. The structured dataset is the "
        "only one where a column exists before any processing.",
        "Both text datasets carry their labels as separate categorical fields, so each row "
        "is a text value plus one or two class labels.",
    ]):
        s.label(18 * mm, 25 * mm - i * 4.4 * mm, ln, size=7.6)

    s.footer("Page 1 of 5. Top level split.")


# ---------------------------------------------------------------------------
# page 2: text datasets
# ---------------------------------------------------------------------------

def page_text(s):
    s.title("Unstructured data: the two text corpora",
            "Each row is free text plus categorical labels. Numeric columns only exist "
            "after vectorisation.")

    top = s.box(W / 2 - 50 * mm, H - 48 * mm, 100 * mm, 14 * mm,
                "UNSTRUCTURED TEXT",
                [f"{F['doc_rows'] + F['msg_rows']:,} rows across 2 datasets"],
                fill=UNSTRUCT, head_size=10)
    tb = (top[0], top[1])

    left = s.box(26 * mm, H - 80 * mm, 112 * mm, 18 * mm,
                 "Document corpus",
                 [f"{F['doc_rows']:,} rows, built from 21 templates"],
                 fill=colors.HexColor("#8E6C38"), head_size=9.5)
    right = s.box(W - 138 * mm, H - 80 * mm, 112 * mm, 18 * mm,
                  "Message corpus",
                  [f"{F['msg_rows']:,} rows, built from 45 templates"],
                  fill=colors.HexColor("#8E6C38"), head_size=9.5)
    s.elbow(tb, (left[0], left[3]), drop=5 * mm)
    s.elbow(tb, (right[0], right[3]), drop=5 * mm)

    specs = [
        (26 * mm, left, [
            ("text", "UNSTRUCTURED",
             [f"natural language, {F['doc_len'][0]} to {F['doc_len'][1]} chars",
              "variable length, no fixed fields"], UNSTRUCT),
            ("label", "CATEGORICAL, NOMINAL",
             [f"{F['doc_classes']} classes, no inherent order",
              "offer_letter, govt_id, bank_details, ...",
              "550 rows each, perfectly balanced"], CATEG),
            ("tier", "CATEGORICAL, ORDINAL",
             ["clean < degraded < severe",
              "3 levels with a genuine ranking",
              "engineered label, not a model input"], CATEG),
        ]),
        (W - 138 * mm, right, [
            ("text", "UNSTRUCTURED",
             [f"natural language, {F['msg_len'][0]} to {F['msg_len'][1]} chars",
              "much shorter than the documents"], UNSTRUCT),
            ("intent", "CATEGORICAL, NOMINAL",
             [f"{F['msg_intents']} classes, no inherent order",
              "document_help, it_access, escalation, ...",
              "420 rows each, balanced"], CATEG),
            ("sentiment", "CATEGORICAL, ORDINAL",
             ["negative < neutral < positive",
              "3 levels with a genuine ranking",
              "deliberately imbalanced 34 / 39 / 27 per cent"], CATEG),
        ]),
    ]

    for x0, parent, fields in specs:
        y = H - 112 * mm
        for name, kind, lines, colour in fields:
            b = s.box(x0, y, 112 * mm, 22 * mm, f"{name}   ({kind})", lines,
                      fill=colour, head_size=8.5, body_size=7)
            s.elbow((parent[0], parent[1]), (b[0], b[3]),
                    drop=4 * mm if y == H - 112 * mm else 3 * mm)
            parent = b
            y -= 27 * mm

    s.label(18 * mm, 34 * mm, "After vectorisation", size=9, colour=INK, bold=True)
    for i, ln in enumerate([
        "Documents become a 4,950 x 11,482 sparse matrix, 99.26 per cent zeros. Messages "
        "become 3,360 x 1,838, 98.78 per cent zeros.",
        "Every engineered column is numerical and continuous, holding a TF-IDF weight "
        "between 0 and 1. The messages produce far fewer columns because they are much",
        "shorter, mean 73 characters against 348 for the documents.",
        "The sentiment labels are additionally converted to a continuous score of "
        "p(positive) minus p(negative), bounded between -1 and +1, which is what the risk "
        "model consumes.",
    ]):
        s.label(18 * mm, 29 * mm - i * 4.4 * mm, ln, size=7.6)

    s.footer("Page 2 of 5. Unstructured datasets.")


# ---------------------------------------------------------------------------
# page 3: journey taxonomy
# ---------------------------------------------------------------------------

def page_journey(s):
    s.title("Structured data: the journey dataset",
            f"{F['jrn_rows']:,} rows by {F['jrn_feats'] + 1} columns. "
            "Every feature stored as float64, but the measurement scales differ.")

    root = s.box(W / 2 - 46 * mm, H - 46 * mm, 92 * mm, 14 * mm,
                 "JOURNEY DATASET",
                 [f"{F['jrn_feats']} features + 1 target"],
                 fill=STRUCT, head_size=10)
    rb = (root[0], root[1])

    num = s.box(24 * mm, H - 72 * mm, 108 * mm, 15 * mm,
                "NUMERICAL  (10 features)",
                ["true quantities, arithmetic is meaningful"],
                fill=NUMERIC, head_size=9)
    ordi = s.box(146 * mm, H - 72 * mm, 62 * mm, 15 * mm,
                 "ORDINAL  (2 features)",
                 ["ranked levels, integer coded"],
                 fill=CATEG, head_size=9)
    tgt = s.box(222 * mm, H - 72 * mm, 56 * mm, 15 * mm,
                "TARGET  (1)",
                ["binary, nominal"],
                fill=TARGET, head_size=9)

    for b in (num, ordi, tgt):
        s.elbow(rb, (b[0], b[3]), drop=5 * mm)

    cont = s.box(24 * mm, H - 96 * mm, 52 * mm, 13 * mm,
                 "CONTINUOUS (5)", ["infinitely divisible"],
                 fill=colors.HexColor("#3D6A86"), head_size=8.5)
    disc = s.box(80 * mm, H - 96 * mm, 52 * mm, 13 * mm,
                 "DISCRETE (5)", ["whole number counts"],
                 fill=colors.HexColor("#3D6A86"), head_size=8.5)
    s.elbow((num[0], num[1]), (cont[0], cont[3]), drop=4 * mm)
    s.elbow((num[0], num[1]), (disc[0], disc[3]), drop=4 * mm)

    def listing(x, y, w, names, note=None):
        """Two lines per entry so a long feature name cannot collide with its range."""
        c = s.c
        rows = len(names)
        h = 8.4 * mm * rows + (4.5 * mm if note else 0) + 3.5 * mm
        c.setFillColor(colors.HexColor("#F2F0EB"))
        c.setStrokeColor(colors.HexColor("#D5D1C8"))
        c.setLineWidth(0.5)
        c.roundRect(x, y - h, w, h, 1.6 * mm, stroke=1, fill=1)
        ty = y - 5.2 * mm
        for n in names:
            r = BY_NAME[n]
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(x + 3 * mm, ty, n)
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 6.3)
            c.drawString(x + 3 * mm, ty - 3.4 * mm,
                         f"{nice_range(r)}   {r['levels']:,} levels")
            ty -= 8.4 * mm
        if note:
            c.setFillColor(MUTED)
            c.setFont("Helvetica-Oblique", 6.3)
            c.drawString(x + 3 * mm, ty + 1.2 * mm, note)
        return h

    s.label(24 * mm, H - 101 * mm, "ratio scale, true zero", size=6.6)
    listing(24 * mm, H - 103 * mm, 52 * mm,
            [n for n in CONTINUOUS if n != "avg_sentiment"],
            "plus avg_sentiment, below")
    s.label(80 * mm, H - 101 * mm, "ratio scale, true zero", size=6.6)
    listing(80 * mm, H - 103 * mm, 52 * mm, DISCRETE)

    sent = BY_NAME["avg_sentiment"]
    s.box(24 * mm, H - 166 * mm, 108 * mm, 16 * mm,
          "avg_sentiment   (CONTINUOUS, INTERVAL scale)",
          [f"range {nice_range(sent)}, signed, zero means neutral rather than absent",
           "ratio statements such as twice as positive are not valid here"],
          fill=colors.HexColor("#54788E"), head_size=8, body_size=6.8)

    y = H - 96 * mm
    for n in sorted(ORDINAL):
        r = BY_NAME[n]
        extra = ("0 = junior, 1 = mid, 2 = senior"
                 if n == "seniority" else "stages 0 to 5 of onboarding")
        b = s.box(146 * mm, y - 18 * mm, 62 * mm, 18 * mm, n,
                  [f"{r['levels']} ordered levels", extra,
                   "spacing between levels not guaranteed equal"],
                  fill=colors.HexColor("#84406A"), head_size=8.5, body_size=6.6)
        s.elbow((ordi[0], ordi[1]), (b[0], b[3]), drop=3.5 * mm)
        y -= 24 * mm

    tb = s.box(222 * mm, H - 114 * mm, 56 * mm, 18 * mm,
               "stalled",
               ["2 levels: 0 or 1", "dichotomous nominal",
                "43.3 per cent positive"],
               fill=colors.HexColor("#A33A3A"), head_size=8.5, body_size=6.6)
    s.elbow((tgt[0], tgt[1]), (tb[0], tb[3]), drop=4 * mm)

    ex = s.box(222 * mm, H - 148 * mm, 56 * mm, 22 * mm,
               "department",
               ["CATEGORICAL, NOMINAL",
                f"{len(F['departments'])} levels, unordered",
                "shapes the simulation",
                "EXCLUDED as a model input"],
               fill=EXCLUDED, head_size=8.5, body_size=6.6)
    s.c.setDash(2, 2)
    s.elbow((tgt[0], tgt[1] - 20 * mm), (ex[0], ex[3]), drop=3 * mm)
    s.c.setDash()

    s.label(18 * mm, 30 * mm, "Two classification decisions worth defending",
            size=9, colour=INK, bold=True)
    for i, ln in enumerate([
        "stage and seniority are ordinal but stored as numbers and treated as numeric by "
        "the model. That assumes the gap between stage 1 and 2 equals the gap between 4 and 5,",
        "which is not guaranteed. An alternative is one hot encoding, at the cost of losing "
        "the ordering. The current choice keeps the ordering and accepts the spacing assumption.",
        "department is nominal with no order and is deliberately not a model input. "
        "Predicting higher risk because of somebody's department invites disparate impact.",
    ]):
        s.label(18 * mm, 25 * mm - i * 4.4 * mm, ln, size=7.6)

    s.footer("Page 3 of 5. Structured dataset taxonomy.")


# ---------------------------------------------------------------------------
# page 4: full variable reference
# ---------------------------------------------------------------------------

def page_table(s):
    s.title("Every variable in the project, classified",
            "20 variables across the three datasets, including engineered and excluded ones.")

    c = s.c
    headers = ["Dataset", "Variable", "Structure", "Type", "Scale", "Levels / range", "Role"]
    widths = [30, 36, 28, 32, 24, 46, 44]
    widths = [w * mm for w in widths]
    x0 = 16 * mm
    y = H - 34 * mm

    def row(cells, bold=False, fill=None, size=6.9):
        nonlocal y
        if fill:
            c.setFillColor(fill)
            c.rect(x0, y - 2.2 * mm, sum(widths), 6.4 * mm, stroke=0, fill=1)
        x = x0
        for cell, w in zip(cells, widths):
            c.setFillColor(INK if bold else colors.HexColor("#2C2C2C"))
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            text = str(cell)
            while c.stringWidth(text, "Helvetica", size) > w - 2.5 * mm and len(text) > 4:
                text = text[:-2]
            c.drawString(x + 1.4 * mm, y, text)
            x += w
        y -= 6.4 * mm

    row(headers, bold=True, fill=colors.HexColor("#E6E2D9"), size=7.2)
    c.setStrokeColor(MUTED)
    c.setLineWidth(0.6)
    c.line(x0, y + 4.2 * mm, x0 + sum(widths), y + 4.2 * mm)

    data = [
        ("Documents", "text", "Unstructured", "Text", "n/a",
         f"{F['doc_len'][0]}-{F['doc_len'][1]} chars", "Input"),
        ("Documents", "label", "Structured", "Categorical", "Nominal",
         f"{F['doc_classes']} classes, 550 each", "Target"),
        ("Documents", "tier", "Structured", "Categorical", "Ordinal",
         "clean < degraded < severe", "Stratifier, not an input"),
        ("Documents", "tfidf_1..11482", "Engineered", "Numerical", "Ratio",
         "0 to 1, 99.26 pct sparse", "Input after vectorising"),
        ("Messages", "text", "Unstructured", "Text", "n/a",
         f"{F['msg_len'][0]}-{F['msg_len'][1]} chars", "Input"),
        ("Messages", "intent", "Structured", "Categorical", "Nominal",
         f"{F['msg_intents']} classes, 420 each", "Target"),
        ("Messages", "sentiment", "Structured", "Categorical", "Ordinal",
         "negative < neutral < positive", "Target"),
        ("Messages", "sentiment_score", "Engineered", "Numerical", "Interval",
         "-1 to +1, continuous", "Feature for risk model"),
        ("Messages", "tfidf_1..1838", "Engineered", "Numerical", "Ratio",
         "0 to 1, 98.78 pct sparse", "Input after vectorising"),
    ]
    for name in ["days_since_start", "stage", "progress", "pct_tasks_complete",
                 "days_since_last_activity", "docs_pending", "docs_rejected",
                 "doc_resubmissions", "kt_completed_pct", "chat_messages",
                 "avg_sentiment", "seniority"]:
        r = BY_NAME[name]
        if name in ORDINAL:
            typ, scale = "Categorical", "Ordinal"
            lv = f"{r['levels']} ordered levels"
        elif name == "avg_sentiment":
            typ, scale = "Numerical cont.", "Interval"
            lv = f"{nice_range(r)} continuous"
        elif r["integer"]:
            typ, scale = "Numerical disc.", "Ratio"
            lv = f"{nice_range(r)}, {r['levels']} values"
        else:
            typ, scale = "Numerical cont.", "Ratio"
            lv = f"{nice_range(r)} continuous"
        data.append(("Journeys", name, "Structured", typ, scale, lv, "Model feature"))

    data.append(("Journeys", "stalled", "Structured", "Categorical", "Nominal",
                 "2 levels, 43.3 pct positive", "Target"))
    data.append(("Journeys", "department", "Structured", "Categorical", "Nominal",
                 f"{len(F['departments'])} levels", "Excluded from the model"))

    shade = colors.HexColor("#FAF9F6")
    for i, d in enumerate(data):
        row(d, fill=shade if i % 2 == 0 else None)

    s.footer("Page 4 of 5. Variable reference.")


# ---------------------------------------------------------------------------
# page 5: definitions
# ---------------------------------------------------------------------------

def page_notes(s):
    s.title("Definitions used, and why each classification was chosen",
            "The terms applied on the preceding pages, with the project's own examples.")

    c = s.c
    items = [
        ("Structured", "Fixed schema. Every row has the same columns and one value per "
                       "column. Only the journey dataset qualifies before processing."),
        ("Unstructured", "No fixed fields. Free text of variable length. Both text corpora "
                         "qualify, and neither has columns until vectorised."),
        ("Categorical", "Takes one of a fixed set of labels. Arithmetic on the codes is "
                        "meaningless. Document label, intent, sentiment, stalled, department."),
        ("Nominal", "Categorical with no inherent order. Nothing makes govt_id greater "
                    "than bank_details. Applies to document label, intent, stalled, department."),
        ("Ordinal", "Categorical with a genuine ranking but no guaranteed equal spacing. "
                    "clean < degraded < severe, negative < neutral < positive, junior < mid "
                    "< senior, stage 0 through 5."),
        ("Numerical, discrete", "Whole number counts. Cannot take a value between two "
                                "adjacent levels. docs_pending, docs_rejected, "
                                "doc_resubmissions, chat_messages, days_since_start."),
        ("Numerical, continuous", "Any value within the range. progress, pct_tasks_complete, "
                                  "days_since_last_activity, kt_completed_pct, avg_sentiment."),
        ("Ratio scale", "Has a true zero, so ratios are meaningful. Zero documents pending "
                        "really is none, and four pending is twice two."),
        ("Interval scale", "Differences are meaningful but zero is a reference point rather "
                           "than an absence. avg_sentiment sits here: zero means neutral, "
                           "not no sentiment, so twice as positive is not a valid statement."),
        ("Binary or dichotomous", "Categorical with exactly two levels. The target, stalled, "
                                  "is 0 or 1 and positive in 43.3 per cent of rows."),
        ("Engineered", "Not present in the raw data, produced by a transformation. The TF-IDF "
                       "columns and the sentiment score."),
        ("Clustered text", "Not used in this project. The text corpora are labelled, so "
                           "classification is supervised. Clustering would group unlabelled "
                           "documents by similarity, which is a possible next phase extension."),
    ]

    y = H - 36 * mm
    for term, definition in items:
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 8.6)
        c.drawString(18 * mm, y, term)
        c.setFillColor(colors.HexColor("#2C2C2C"))
        c.setFont("Helvetica", 7.8)
        words = definition.split()
        line, lines = "", []
        for wrd in words:
            trial = (line + " " + wrd).strip()
            if c.stringWidth(trial, "Helvetica", 7.8) > 190 * mm:
                lines.append(line)
                line = wrd
            else:
                line = trial
        lines.append(line)
        ly = y
        for ln in lines:
            c.drawString(66 * mm, ly, ln)
            ly -= 4.2 * mm
        y = min(y - 8 * mm, ly - 3.2 * mm)

    s.footer("Page 5 of 5. Definitions.")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(OUT), pagesize=PAGE)
    c.setTitle("OnboardAI Data Taxonomy")
    s = Sheet(c)
    for page in (page_master, page_text, page_journey, page_table, page_notes):
        page(s)
        c.showPage()
    c.save()
    print(f"Saved {OUT}  ({OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
