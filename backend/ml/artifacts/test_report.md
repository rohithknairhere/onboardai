# Test Report

Generated 2026-10-07 by `python -m tests.make_test_report`.
The actual-result column comes from a real run of the suite.

**34 test cases, 55 executed checks, 55 passed.**
`============================= 55 passed in 19.50s =============================`

Run the suite yourself with:

```
python -m pytest tests -q
```

## Scope and approach

No language model is called anywhere in this suite. Agent behaviour is asserted
through tool registries and classifier outputs, both deterministic, because a test
whose result depends on generation temperature cannot act as a regression gate.
Uploads are written to a temporary directory, so no test touches the development
database or the real document store.

Two cases (TC-05, TC-14) assert the *presence* of known defects rather than their
absence. They document measured problems and fail if those problems grow worse.

## Test cases

| ID | Category | Input | Expected | Actual |
| --- | --- | --- | --- | --- |
| TC-01 | Validation | Generated document corpus | 4,950 documents, 9 classes, parallel arrays aligned | PASS |
| TC-02 | Validation | All three datasets | Zero empty strings, zero NaN in features or target | PASS |
| TC-03 | Validation | Document labels | Every class within 1% of the mean count | PASS |
| TC-04 | Validation | Document texts | Zero exact duplicates | PASS |
| TC-05 | Known defect | Message texts | Duplicates present but under 10% (known defect) | PASS |
| TC-06 | Validation | Risk feature matrix | Float dtype, all finite, 12 columns, no constant column | PASS |
| TC-07 | Validation | Risk target | Values in {0,1}, positive rate between 20% and 80% | PASS |
| TC-08 | Boundary | Each bounded feature | Values inside their declared domain | PASS (6 runs) |
| TC-09 | Preprocessing | Document texts through the vectoriser | Sparse matrix, one row per document, >95% sparse | PASS |
| TC-10 | Preprocessing | Document texts, min_df 1 vs 2 | Pruning reduces the feature count | PASS |
| TC-11 | Preprocessing | Risk features through StandardScaler | Every column mean ~0, sd ~1 | PASS |
| TC-12 | Split | Documents split 75/25 stratified | Class proportions preserved within 1% in both folds | PASS |
| TC-13 | Split | Document train/test folds | Zero records present in both folds | PASS |
| TC-14 | Known defect | Message train/test folds | Overlap present but under 15% (known defect) | PASS |
| TC-15 | Reproducibility | Risk split run twice with seed 42 | Identical folds both times | PASS |
| TC-16 | Functional | Each of 7 demo PDFs + its requirement | The verdict named in the filename | PASS (7 runs) |
| TC-17 | Functional | Expired safety certificate | Rejected, reason names the expiry date | PASS |
| TC-18 | Regression | Passport line holding issue and expiry together | Each date gets its correct role | PASS |
| TC-19 | Regression | Document titled 'CERTIFICATE OF ...' | Identifier taken from the field, not the title | PASS |
| TC-20 | Boundary | Zero-byte upload | Rejected, no crash | PASS |
| TC-21 | Exceptional | HTML content declared as application/pdf | Rejected on magic bytes | PASS |
| TC-22 | Boundary | File one byte over the 10MB cap | Rejected and no partial file left on disk | PASS |
| TC-23 | Exceptional | Employee ids with traversal or illegal characters | Rejected | PASS (5 runs) |
| TC-24 | Exceptional | Crafted relative path '../../../windows/win.ini' | Refused, cannot escape the store | PASS |
| TC-25 | Validation | PDF with no extractable text | Never auto-approved; routed to a human | PASS |
| TC-26 | Performance | One demo PDF, warmed | End-to-end analysis under 5 seconds | PASS |
| TC-27 | Functional | One representative message per intent | Routed to the correct specialist | PASS (5 runs) |
| TC-28 | Boundary | 'any update?' | Low confidence, not routed to a specialist | PASS |
| TC-29 | Functional | One message per sentiment class | The matching sentiment label | PASS (3 runs) |
| TC-30 | Security | Message containing six identifier types | Every value stripped before leaving | PASS |
| TC-31 | Access control | Same question from two organisations | Different, organisation-correct policies | PASS |
| TC-32 | Access control | Security question from permitted and non-permitted departments | Restricted document hidden from Sales | PASS |
| TC-33 | Architecture | Each specialist's tool registry | Capabilities disjoint and enforced by construction | PASS |
| TC-34 | Performance | 50 classifications and 50 retrievals | Mean under 150ms per call | PASS |

## Coverage by category

| Category | Cases |
| --- | --- |
| Validation | 7 |
| Boundary | 4 |
| Functional | 4 |
| Preprocessing | 3 |
| Exceptional | 3 |
| Known defect | 2 |
| Split | 2 |
| Regression | 2 |
| Performance | 2 |
| Access control | 2 |
| Reproducibility | 1 |
| Security | 1 |
| Architecture | 1 |

## What is not covered

Stated plainly so the gaps are not mistaken for passes:

- **No API-level tests.** Endpoints are exercised manually, not by the suite.
- **No authentication tests**, because there is no authentication to test.
- **No frontend tests.** No vitest or Playwright coverage exists.
- **No agent-response quality tests.** Tool boundaries are asserted; whether an
  answer is *good* is not, and would need an LLM-as-judge rubric reported as a
  trend rather than a gate.
- **No model accuracy gate in CI.** Metric thresholds are not enforced on each run.

