# Onboarding Stall-Risk Model — Evaluation Report

- Model version: `risk-v1`
- Selected model: **logistic_regression**
- Train / test: 4500 / 1500
- Base stall rate: 43.3%
- 5-fold CV ROC-AUC: **0.8070 ± 0.0019**

## Model comparison

| Model | ROC-AUC | PR-AUC | Brier | Accuracy |
| --- | --- | --- | --- | --- |
| hist_gradient_boosting | 0.7773 | 0.7377 | 0.1941 | 0.7047 |
| logistic_regression | 0.7948 | 0.7612 | 0.1815 | 0.7253 |

## Ablations

Each row retrains the model with one feature removed. A negative delta
means the feature was carrying real signal.

| Removed feature | ROC-AUC | Δ |
| --- | --- | --- |
| avg_sentiment | 0.7873 | -0.0075 |
| days_since_last_activity | 0.7897 | -0.0052 |
| docs_rejected | 0.7943 | -0.0005 |

## Permutation importance

| Feature | Importance | Std |
| --- | --- | --- |
| avg_sentiment | 0.0356 | 0.0047 |
| kt_completed_pct | 0.0215 | 0.0027 |
| pct_tasks_complete | 0.0210 | 0.0035 |
| days_since_start | 0.0188 | 0.0027 |
| days_since_last_activity | 0.0092 | 0.0020 |
| progress | 0.0090 | 0.0020 |
| docs_pending | 0.0059 | 0.0028 |
| seniority | 0.0030 | 0.0009 |
| docs_rejected | 0.0029 | 0.0021 |
| stage | 0.0021 | 0.0010 |
| chat_messages | 0.0011 | 0.0008 |
| doc_resubmissions | 0.0010 | 0.0021 |

## Calibration

Predicted probability versus observed stall rate on held-out data.

| Predicted bucket | N | Mean predicted | Observed |
| --- | --- | --- | --- |
| 0.0-0.2 | 410 | 0.124 | 0.139 |
| 0.2-0.4 | 376 | 0.295 | 0.316 |
| 0.4-0.6 | 275 | 0.501 | 0.513 |
| 0.6-0.8 | 247 | 0.695 | 0.664 |
| 0.8-1.0 | 192 | 0.883 | 0.880 |
