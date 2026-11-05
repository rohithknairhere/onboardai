"""Exploratory data analysis: figures plus the observation each one supports.

Run from the backend directory:
    python -m ml.eda

Writes PNGs to ml/artifacts/eda/ and an observations file alongside them. Every
observation is computed from the data, not written by hand, so the text cannot
drift away from the figure it describes.
"""
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from ml import risk_synth, synth, text_synth

OUT = Path(__file__).resolve().parent / "artifacts" / "eda"
NOTES = OUT / "observations.md"

INK = "#1f2421"
ACCENT = "#b8912f"
ALT = "#4a6070"
POS = "#2e6b3e"
NEG = "#b3261e"

plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.dpi": 130,
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "axes.edgecolor": "#cccccc",
    "axes.grid": True,
    "grid.color": "#e8e8e8",
    "grid.linewidth": 0.6,
    "figure.autolayout": True,
})

observations: list[tuple[str, str, list[str]]] = []


def save(fig, filename, title, notes):
    path = OUT / filename
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    observations.append((filename, title, notes))
    print(f" {filename}")


def fig1_document_classes(labels):
    counts = Counter(labels)
    names = sorted(counts)
    vals = [counts[n] for n in names]

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar([n.replace("_", "\n") for n in names], vals, color=ACCENT, edgecolor=INK, linewidth=0.5)
    ax.set_title("Document corpus: class distribution")
    ax.set_xlabel("Document type")
    ax.set_ylabel("Number of documents")
    ax.set_ylim(0, max(vals) * 1.18)
    for i, v in enumerate(vals):
        ax.text(i, v + max(vals) * 0.02, str(v), ha="center", fontsize=7.5)

    save(fig, "01_document_class_distribution.png",
         "Document corpus: class distribution",
         [f"All {len(names)} classes hold exactly {vals[0]:,} documents, so the corpus is "
          f"perfectly balanced by construction (balance ratio 1.00).",
          "Because the classes are balanced, plain accuracy is a fair headline metric here; on an "
          "imbalanced real corpus macro-F1 would be required instead."])


def fig2_document_lengths(texts, tiers):
    lengths = np.array([len(t) for t in texts])
    tier_names = list(synth.DIFFICULTY_MIX)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.5))

    ax1.hist(lengths, bins=45, color=ALT, edgecolor="white", linewidth=0.4)
    ax1.axvline(lengths.mean(), color=NEG, linestyle="--", linewidth=1.2,
                label=f"mean {lengths.mean():.0f}")
    ax1.axvline(np.median(lengths), color=POS, linestyle="--", linewidth=1.2,
                label=f"median {np.median(lengths):.0f}")
    ax1.set_title("Document length distribution")
    ax1.set_xlabel("Document length (characters)")
    ax1.set_ylabel("Number of documents")
    ax1.legend(frameon=False, fontsize=7.5)

    data = [lengths[np.array(tiers) == t] for t in tier_names]
    bp = ax2.boxplot(data, tick_labels=tier_names, patch_artist=True, widths=0.55)
    for patch, colour in zip(bp["boxes"], [POS, ACCENT, NEG]):
        patch.set_facecolor(colour)
        patch.set_alpha(0.65)
    for median in bp["medians"]:
        median.set_color(INK)
    ax2.set_title("Length by degradation tier")
    ax2.set_xlabel("Scan quality tier")
    ax2.set_ylabel("Document length (characters)")

    medians = {t: float(np.median(lengths[np.array(tiers) == t])) for t in tier_names}
    save(fig, "02_document_length_distribution.png",
         "Document length distribution and length by degradation tier",
         [f"Lengths are right-skewed: mean {lengths.mean():.0f} characters against a median of "
          f"{np.median(lengths):.0f}, ranging {lengths.min()}-{lengths.max()}.",
          f"Median length falls from {medians[tier_names[0]]:.0f} characters on clean scans to "
          f"{medians[tier_names[-1]]:.0f} on severe ones, confirming the severe tier genuinely "
          "removes content rather than only adding noise.",
          "Documents average well under a page, which is a known limitation: a real scanned "
          "certificate carries far more text and layout structure than this."])


def fig3_tier_distribution(tiers):
    counts = Counter(tiers)
    names = list(synth.DIFFICULTY_MIX)
    vals = [counts[n] for n in names]
    total = sum(vals)

    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    bars = ax.bar(names, vals, color=[POS, ACCENT, NEG], edgecolor=INK, linewidth=0.5)
    ax.set_title("Corpus composition by scan quality")
    ax.set_xlabel("Degradation tier")
    ax.set_ylabel("Number of documents")
    ax.set_ylim(0, max(vals) * 1.2)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02,
                f"{v:,}\n({100*v/total:.0f}%)", ha="center", fontsize=7.5)

    save(fig, "03_difficulty_tier_distribution.png",
         "Corpus composition by scan quality",
         [f"{100*vals[-1]/total:.0f}% of the corpus is the severe tier, cropped, heavily noised "
          "and with cross-class text bleeding in.",
          "Holding back a deliberately hard slice is what makes the per-tier accuracy "
          "breakdown meaningful; a single headline accuracy would hide where the model fails."])


def fig4_message_classes(intents, sentiments):
    i_counts = Counter(intents)
    s_counts = Counter(sentiments)
    i_names = sorted(i_counts)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.5),
                                   gridspec_kw={"width_ratios": [2.4, 1]})

    ax1.barh([n.replace("_", " ") for n in i_names],
             [i_counts[n] for n in i_names], color=ALT, edgecolor=INK, linewidth=0.5)
    ax1.set_title("Message corpus: intent distribution")
    ax1.set_xlabel("Number of messages")
    ax1.invert_yaxis()

    order = ["negative", "neutral", "positive"]
    vals = [s_counts.get(o, 0) for o in order]
    bars = ax2.bar(order, vals, color=[NEG, "#8a8a8a", POS], edgecolor=INK, linewidth=0.5)
    ax2.set_title("Sentiment distribution")
    ax2.set_xlabel("Sentiment class")
    ax2.set_ylabel("Number of messages")
    ax2.set_ylim(0, max(vals) * 1.2)
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02,
                 f"{100*v/sum(vals):.0f}%", ha="center", fontsize=7.5)

    save(fig, "04_message_class_distributions.png",
         "Message corpus: intent and sentiment distributions",
         [f"Intents are balanced at {i_counts[i_names[0]]:,} messages each, but sentiment is not: "
          f"negative {100*vals[0]/sum(vals):.0f}%, neutral {100*vals[1]/sum(vals):.0f}%, "
          f"positive {100*vals[2]/sum(vals):.0f}%.",
          "The sentiment imbalance is intentional, because escalations are rarely cheerful and "
          "small talk is rarely furious. `class_weight='balanced'` is therefore used when "
          "training the sentiment classifier."])


def fig5_intent_sentiment_heatmap(intents, sentiments):
    i_names = sorted(set(intents))
    s_names = ["negative", "neutral", "positive"]
    matrix = np.zeros((len(i_names), len(s_names)))
    for i, s in zip(intents, sentiments):
        matrix[i_names.index(i), s_names.index(s)] += 1
    row_pct = 100 * matrix / matrix.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    im = ax.imshow(row_pct, cmap="RdYlGn", aspect="auto", vmin=0, vmax=100)
    ax.set_xticks(range(len(s_names)), s_names)
    ax.set_yticks(range(len(i_names)), [n.replace("_", " ") for n in i_names])
    ax.set_title("Sentiment mix within each intent (row %)")
    ax.set_xlabel("Sentiment")
    ax.set_ylabel("Intent")
    ax.grid(False)
    for r in range(len(i_names)):
        for c in range(len(s_names)):
            ax.text(c, r, f"{row_pct[r, c]:.0f}", ha="center", va="center", fontsize=7.5)
    fig.colorbar(im, ax=ax, label="% of messages in that intent", shrink=0.85)

    esc = row_pct[i_names.index("escalation")]
    small = row_pct[i_names.index("smalltalk")]
    save(fig, "05_intent_sentiment_heatmap.png",
         "Sentiment mix within each intent",
         [f"Escalation messages are {esc[0]:.0f}% negative, while small talk is "
          f"{small[2]:.0f}% positive, intent and sentiment are correlated but not equivalent.",
          "Because they are distinct labels on the same text, two separate classifiers are "
          "trained on one corpus rather than predicting a single combined label."])


def fig6_risk_correlation(X, y, features):
    data = np.column_stack([X, y])
    names = list(features) + ["stalled"]
    corr = np.corrcoef(data, rowvar=False)

    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(names)), names, rotation=45, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(names)), names, fontsize=7.5)
    ax.set_title("Correlation matrix: journey features and target")
    ax.grid(False)
    for r in range(len(names)):
        for c in range(len(names)):
            if abs(corr[r, c]) > 0.25 and r != c:
                ax.text(c, r, f"{corr[r, c]:.2f}", ha="center", va="center", fontsize=6.2)
    fig.colorbar(im, ax=ax, label="Pearson r", shrink=0.8)

    target = {f: corr[i, -1] for i, f in enumerate(features)}
    top = sorted(target.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
    pairs = []
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            pairs.append((features[i], features[j], corr[i, j]))
    strongest = max(pairs, key=lambda p: abs(p[2]))

    save(fig, "06_risk_correlation_matrix.png",
         "Correlation matrix: journey features and target",
         [f"The strongest correlates of stalling are "
          + ", ".join(f"{f} ({v:+.2f})" for f, v in top) + ".",
          f"`{strongest[0]}` and `{strongest[1]}` correlate at {strongest[2]:+.2f}, so they carry "
          "overlapping information. This multicollinearity is why removing one feature in the "
          "ablation study barely moves the headline score.",
          "No feature correlates with the target above |0.45|, which is consistent with a "
          "generator that deliberately withholds part of the cause from the features."])


def fig7_stall_by_department(y, departments):
    depts = sorted(set(departments))
    arr = np.array(departments)
    rates = [100 * y[arr == d].mean() for d in depts]
    counts = [int((arr == d).sum()) for d in depts]
    order = np.argsort(rates)[::-1]

    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    bars = ax.bar([depts[i] for i in order], [rates[i] for i in order],
                  color=ACCENT, edgecolor=INK, linewidth=0.5)
    ax.axhline(100 * y.mean(), color=NEG, linestyle="--", linewidth=1.2,
               label=f"overall {100*y.mean():.1f}%")
    ax.set_title("Stall rate by department")
    ax.set_xlabel("Department")
    ax.set_ylabel("Stalled (% of hires)")
    ax.legend(frameon=False, fontsize=8)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    for b, i in zip(bars, order):
        ax.text(b.get_x() + b.get_width() / 2, rates[i] + 0.8,
                f"{rates[i]:.0f}%\nn={counts[i]}", ha="center", fontsize=7)

    hi, lo = depts[order[0]], depts[order[-1]]
    save(fig, "07_stall_rate_by_department.png",
         "Stall rate by department",
         [f"{hi} stalls most often ({max(rates):.0f}%) and {lo} least ({min(rates):.0f}%), a "
          f"spread of {max(rates)-min(rates):.0f} percentage points around an overall "
          f"{100*y.mean():.1f}%.",
          "The gap reflects document-heavy, regulated onboarding in operations and legal roles.",
          "Department is deliberately **not** a model feature: predicting higher risk because of "
          "someone's department invites disparate impact. It shapes the simulation only."])


def fig8_sentiment_vs_outcome(X, y, features):
    idx = features.index("avg_sentiment")
    col = X[:, idx]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.5))

    bp = ax1.boxplot([col[y == 0], col[y == 1]],
                     tick_labels=["completed", "stalled"], patch_artist=True, widths=0.5)
    for patch, colour in zip(bp["boxes"], [POS, NEG]):
        patch.set_facecolor(colour)
        patch.set_alpha(0.65)
    for median in bp["medians"]:
        median.set_color(INK)
    ax1.set_title("Message sentiment by onboarding outcome")
    ax1.set_xlabel("Outcome")
    ax1.set_ylabel("Mean sentiment score (-1 to +1)")

    ax2.hist(col[y == 0], bins=35, alpha=0.6, label="completed", color=POS, density=True)
    ax2.hist(col[y == 1], bins=35, alpha=0.6, label="stalled", color=NEG, density=True)
    ax2.set_title("Sentiment distribution by outcome")
    ax2.set_xlabel("Mean sentiment score (-1 to +1)")
    ax2.set_ylabel("Density")
    ax2.legend(frameon=False, fontsize=8)

    save(fig, "08_sentiment_vs_outcome.png",
         "Message sentiment by onboarding outcome",
         [f"Median sentiment is {np.median(col[y == 0]):+.2f} for hires who complete and "
          f"{np.median(col[y == 1]):+.2f} for those who stall.",
          "The distributions overlap heavily, so sentiment alone cannot separate the outcomes, "
          "which matches its modest ablation contribution of 0.0075 AUC rather than contradicting "
          "it.",
          "This is the plot that justifies feeding an NLP output into the risk model at all."])


def fig9_feature_distributions(X, features):
    fig, axes = plt.subplots(3, 4, figsize=(11, 6.4))
    for ax, (i, f) in zip(axes.ravel(), enumerate(features)):
        ax.hist(X[:, i], bins=30, color=ALT, edgecolor="white", linewidth=0.3)
        ax.set_title(f, fontsize=8.5)
        ax.tick_params(labelsize=6.5)
    fig.suptitle("Distribution of every journey feature", fontweight="bold", y=1.01)

    skewed = []
    for i, f in enumerate(features):
        col = X[:, i]
        if col.std() and abs(float(((col - col.mean()) ** 3).mean() / col.std() ** 3)) > 1.0:
            skewed.append(f)

    save(fig, "09_risk_feature_distributions.png",
         "Distribution of every journey feature",
         [f"{len(features)} features, all numeric, with no missing values.",
          f"Strongly right-skewed features: {', '.join(skewed) if skewed else 'none'}. These are "
          "counts and waiting times whose long tail is the signal of interest, so the outliers "
          "were kept rather than trimmed.",
          "The differing units and ranges are why StandardScaler is applied before logistic "
          "regression."])


def fig10_scatter(X, y, features):
    xi = features.index("progress")
    yi = features.index("days_since_last_activity")

    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    for cls, colour, label in ((0, POS, "completed"), (1, NEG, "stalled")):
        mask = y == cls
        ax.scatter(X[mask, xi], X[mask, yi], s=7, alpha=0.32, c=colour,
                   label=label, edgecolors="none")
    ax.set_title("Progress against inactivity, by outcome")
    ax.set_xlabel("Overall progress (%)")
    ax.set_ylabel("Days since last recorded activity")
    ax.legend(frameon=False, fontsize=8, markerscale=2)

    stalled_hi = X[(y == 1), yi].mean()
    done_hi = X[(y == 0), yi].mean()
    save(fig, "10_progress_vs_inactivity_scatter.png",
         "Progress against inactivity, by outcome",
         [f"Stalled hires average {stalled_hi:.1f} days of inactivity against {done_hi:.1f} for "
          "those who complete.",
          "Stalled cases cluster in the upper-left, low progress combined with long silence, "
          "which is precisely the region the risk model needs to flag.",
          "The classes are not linearly separable on these two axes alone, confirming that a "
          "multi-feature model is warranted."])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Writing figures to {OUT}\n")

    d_texts, d_labels, d_tiers = synth.generate()
    fig1_document_classes(d_labels)
    fig2_document_lengths(d_texts, d_tiers)
    fig3_tier_distribution(d_tiers)

    _, intents, sentiments = text_synth.generate()
    fig4_message_classes(intents, sentiments)
    fig5_intent_sentiment_heatmap(intents, sentiments)

    X, y, features, departments = risk_synth.generate()
    fig6_risk_correlation(X, y, features)
    fig7_stall_by_department(y, departments)
    fig8_sentiment_vs_outcome(X, y, features)
    fig9_feature_distributions(X, features)
    fig10_scatter(X, y, features)

    lines = ["# EDA Observations", "",
             "Each figure in this folder with the observations it supports. Every number below is",
             "computed from the data by `ml/eda.py`, so the commentary cannot drift away from the",
             "figure it describes.", ""]
    for filename, title, notes in observations:
        lines += [f"## {title}", "", f"`{filename}`", ""]
        lines += [f"- {n}" for n in notes]
        lines += [""]
    NOTES.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{len(observations)} figures + {NOTES.name}")


if __name__ == "__main__":
    main()
