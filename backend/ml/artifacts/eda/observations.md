# EDA Observations

Each figure in this folder with the observations it supports. Every number below is
computed from the data by `ml/eda.py`, so the commentary cannot drift away from the
figure it describes.

## Document corpus: class distribution

`01_document_class_distribution.png`

- All 9 classes hold exactly 550 documents, so the corpus is perfectly balanced by construction (balance ratio 1.00).
- Because the classes are balanced, plain accuracy is a fair headline metric here; on an imbalanced real corpus macro-F1 would be required instead.

## Document length distribution and length by degradation tier

`02_document_length_distribution.png`

- Lengths are right-skewed: mean 348 characters against a median of 342, ranging 75-727.
- Median length falls from 391 characters on clean scans to 232 on severe ones, confirming the severe tier genuinely removes content rather than only adding noise.
- Documents average well under a page, which is a known limitation: a real scanned certificate carries far more text and layout structure than this.

## Corpus composition by scan quality

`03_difficulty_tier_distribution.png`

- 22% of the corpus is the severe tier, cropped, heavily noised and with cross-class text bleeding in.
- Holding back a deliberately hard slice is what makes the per-tier accuracy breakdown meaningful; a single headline accuracy would hide where the model fails.

## Message corpus: intent and sentiment distributions

`04_message_class_distributions.png`

- Intents are balanced at 420 messages each, but sentiment is not: negative 34%, neutral 39%, positive 27%.
- The sentiment imbalance is intentional, because escalations are rarely cheerful and small talk is rarely furious. `class_weight='balanced'` is therefore used when training the sentiment classifier.

## Sentiment mix within each intent

`05_intent_sentiment_heatmap.png`

- Escalation messages are 84% negative, while small talk is 56% positive, intent and sentiment are correlated but not equivalent.
- Because they are distinct labels on the same text, two separate classifiers are trained on one corpus rather than predicting a single combined label.

## Correlation matrix: journey features and target

`06_risk_correlation_matrix.png`

- The strongest correlates of stalling are avg_sentiment (-0.45), docs_pending (+0.39), pct_tasks_complete (-0.38).
- `stage` and `progress` correlate at +0.97, so they carry overlapping information. This multicollinearity is why removing one feature in the ablation study barely moves the headline score.
- No feature correlates with the target above |0.45|, which is consistent with a generator that deliberately withholds part of the cause from the features.

## Stall rate by department

`07_stall_rate_by_department.png`

- Operations stalls most often (53%) and Design least (38%), a spread of 15 percentage points around an overall 43.3%.
- The gap reflects document-heavy, regulated onboarding in operations and legal roles.
- Department is deliberately **not** a model feature: predicting higher risk because of someone's department invites disparate impact. It shapes the simulation only.

## Message sentiment by onboarding outcome

`08_sentiment_vs_outcome.png`

- Median sentiment is +0.45 for hires who complete and -0.64 for those who stall.
- The distributions overlap heavily, so sentiment alone cannot separate the outcomes, which matches its modest ablation contribution of 0.0075 AUC rather than contradicting it.
- This is the plot that justifies feeding an NLP output into the risk model at all.

## Distribution of every journey feature

`09_risk_feature_distributions.png`

- 12 features, all numeric, with no missing values.
- Strongly right-skewed features: days_since_last_activity, docs_pending, docs_rejected, doc_resubmissions, chat_messages. These are counts and waiting times whose long tail is the signal of interest, so the outliers were kept rather than trimmed.
- The differing units and ranges are why StandardScaler is applied before logistic regression.

## Progress against inactivity, by outcome

`10_progress_vs_inactivity_scatter.png`

- Stalled hires average 4.1 days of inactivity against 1.8 for those who complete.
- Stalled cases cluster in the upper-left, low progress combined with long silence, which is precisely the region the risk model needs to flag.
- The classes are not linearly separable on these two axes alone, confirming that a multi-feature model is warranted.
