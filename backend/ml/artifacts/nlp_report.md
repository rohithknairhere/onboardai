# NLP Models — Evaluation Report

Model version: `nlp-v1`

## Intent classification

- Accuracy: **0.9369**
- Macro-F1: **0.9368**
- 5-fold CV macro-F1: **0.9331 ± 0.0037**

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| document_help | 0.968 | 0.867 | 0.915 | 105 |
| escalation | 0.910 | 0.962 | 0.935 | 105 |
| it_access | 0.936 | 0.971 | 0.953 | 105 |
| kt_schedule | 0.941 | 0.914 | 0.928 | 105 |
| payroll_benefits | 0.894 | 0.962 | 0.927 | 105 |
| policy_question | 0.969 | 0.886 | 0.925 | 105 |
| smalltalk | 1.000 | 1.000 | 1.000 | 105 |
| status_check | 0.891 | 0.933 | 0.912 | 105 |

Confusion matrix (rows true, columns predicted):

| | document_help | escalation | it_access | kt_schedule | payroll_benefits | policy_question | smalltalk | status_check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **document_help** | 91 | 1 | 2 | 2 | 5 | 0 | 0 | 4 |
| **escalation** | 0 | 101 | 0 | 1 | 2 | 0 | 0 | 1 |
| **it_access** | 0 | 2 | 102 | 0 | 0 | 0 | 0 | 1 |
| **kt_schedule** | 1 | 2 | 2 | 96 | 1 | 1 | 0 | 2 |
| **payroll_benefits** | 0 | 1 | 1 | 0 | 101 | 1 | 0 | 1 |
| **policy_question** | 1 | 4 | 0 | 2 | 2 | 93 | 0 | 3 |
| **smalltalk** | 0 | 0 | 0 | 0 | 0 | 0 | 105 | 0 |
| **status_check** | 1 | 0 | 2 | 1 | 2 | 1 | 0 | 98 |

## Sentiment classification

- Accuracy: **0.9964**
- Macro-F1: **0.9964**
- 5-fold CV macro-F1: **0.9962 ± 0.0027**

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| negative | 1.000 | 0.996 | 0.998 | 282 |
| neutral | 0.997 | 0.994 | 0.995 | 330 |
| positive | 0.991 | 1.000 | 0.996 | 228 |

Confusion matrix (rows true, columns predicted):

| | negative | neutral | positive |
| --- | --- | --- | --- |
| **negative** | 281 | 1 | 0 |
| **neutral** | 0 | 328 | 2 |
| **positive** | 0 | 0 | 228 |

