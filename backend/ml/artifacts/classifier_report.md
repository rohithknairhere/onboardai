# Document Classifier — Evaluation Report

- Model version: `doc-clf-v1`
- Selected model: **linearsvc_calibrated**
- Train / test split: 3712 / 1238
- Test accuracy: **0.9863**
- Test macro-F1: **0.9863**
- 5-fold CV macro-F1: **0.9859 ± 0.0040**

## Model comparison

| Model | Accuracy | Macro-F1 | Train time (s) |
| --- | --- | --- | --- |
| logreg | 0.9838 | 0.9838 | 8.31 |
| linearsvc_calibrated | 0.9863 | 0.9863 | 6.65 |

## Performance by scan quality

Documents are generated at three degradation tiers. `severe` simulates a
cropped, heavily noised phone photo with cross-class text bleeding in.

| Tier | N | Accuracy | Macro-F1 |
| --- | --- | --- | --- |
| clean | 515 | 1.0000 | 1.0000 |
| degraded | 452 | 1.0000 | 1.0000 |
| severe | 271 | 0.9373 | 0.9349 |

## Per-class performance

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| background_check_consent | 0.965 | 0.993 | 0.978 | 137 |
| bank_details | 0.965 | 0.993 | 0.978 | 137 |
| education_certificate | 1.000 | 1.000 | 1.000 | 138 |
| govt_id | 0.972 | 0.993 | 0.982 | 138 |
| ip_agreement | 1.000 | 1.000 | 1.000 | 138 |
| offer_letter | 0.993 | 0.993 | 0.993 | 137 |
| other | 0.993 | 0.971 | 0.982 | 138 |
| professional_license | 1.000 | 0.964 | 0.981 | 137 |
| safety_certification | 0.993 | 0.971 | 0.982 | 138 |

## Confusion matrix

Rows are true labels, columns predicted.

| | background_check_consent | bank_details | education_certificate | govt_id | ip_agreement | offer_letter | other | professional_license | safety_certification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **background_check_consent** | 136 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| **bank_details** | 1 | 136 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **education_certificate** | 0 | 0 | 138 | 0 | 0 | 0 | 0 | 0 | 0 |
| **govt_id** | 1 | 0 | 0 | 137 | 0 | 0 | 0 | 0 | 0 |
| **ip_agreement** | 0 | 0 | 0 | 0 | 138 | 0 | 0 | 0 | 0 |
| **offer_letter** | 1 | 0 | 0 | 0 | 0 | 136 | 0 | 0 | 0 |
| **other** | 1 | 2 | 0 | 1 | 0 | 0 | 134 | 0 | 0 |
| **professional_license** | 0 | 1 | 0 | 2 | 0 | 0 | 1 | 132 | 1 |
| **safety_certification** | 1 | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 134 |
