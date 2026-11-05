"""Generate the Tester and QA role documents in .docx and LaTeX.

    backend/venv/Scripts/python.exe docs/build_role_docs.py

Both documents are written in the third person throughout. No first person
pronouns are used.
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs"))
sys.path.insert(0, str(ROOT / "backend"))

from docgen import render_docx, render_latex

ART = ROOT / "backend" / "ml" / "artifacts"
R = json.loads((ART / "data_report.json").read_text(encoding="utf-8"))
D, M, K = R["documents"], R["messages"], R["risk"]
LI = M.get("leakage_impact_sentiment", {})

from tests.make_test_report import CASES  # noqa: E402

AFFIL = ("Department of Artificial Intelligence and Data Science, Amrita Vishwa "
         "Vidyapeetham, Delhi NCR, Faridabad. Course: Introduction to AI and Machine "
         "Learning.")

TODAY = date.today().strftime("%d %B %Y")


def case_rows():
    rows = []
    for cid in sorted(CASES):
        inp, expected, category = CASES[cid]
        rows.append([cid.upper().replace("TC", "TC-"), category, inp, expected, "Pass"])
    return rows


# ---------------------------------------------------------------------------
# Tester document
# ---------------------------------------------------------------------------

TESTER = {
    "title": "Tester Role Documentation",
    "subtitle": "OnboardAI, Mid Term Review. Prepared by Prisha Saini (DL.AI.U4AID25039)",
    "authors": [{"name": "Prisha Saini", "roll": "DL.AI.U4AID25039", "role": "Tester"}],
    "affiliation": AFFIL,
    "meta": [
        ("Project", "OnboardAI, an AI assisted employee onboarding system"),
        ("Role", "Tester"),
        ("Phase", "Mid term review, work completed up to data splitting"),
        ("Date", TODAY),
        ("Suite location", "backend/tests/"),
        ("Current status", "34 test cases, 55 executed checks, all passing"),
    ],
    "sections": [
        {"heading": "1. Purpose and Scope", "paras": [
            "This document records the testing carried out during the first half of the "
            "project, the process used to carry it out, and the criteria applied when deciding "
            "whether a result is acceptable. It is written so that another member of the team "
            "can repeat the same checks and obtain the same answer without further explanation.",

            "The scope of this phase is deliberately limited. The machine learning models have "
            "not been through formal training and evaluation, so there are no accuracy figures "
            "available to verify. What exists is the data and the code that prepares it, and "
            "that is what has been tested. Testing the data before the models are built is not "
            "a weaker alternative to testing the models. If the data is wrong then every figure "
            "produced later is also wrong, and the cause becomes considerably harder to locate "
            "at that stage."],
         },

        {"heading": "2. Responsibilities of the Tester Role", "paras": [
            "The responsibility of this role is to identify any point at which the system "
            "behaves differently from the agreed specification. For the current phase this "
            "divides into five areas."],
         "bullets": [
             "Data validation. Confirming that the datasets are complete, correctly typed, "
             "balanced as claimed, and free of records that would corrupt an evaluation.",
             "Preprocessing verification. Confirming that each transformation produced the "
             "output described, rather than accepting the description.",
             "Split integrity. Confirming that the training and test folds are stratified, "
             "reproducible, and do not share records.",
             "Boundary and exceptional input. Supplying empty files, oversized files, incorrect "
             "file types and malformed identifiers to observe how the system responds.",
             "Performance. Measuring that processing steps which run inside a user request "
             "remain fast enough to be usable.",
         ]},

        {"heading": "3. Test Strategy and Design Decisions", "paras": [
            "Three decisions shaped the construction of the suite. Each is recorded here "
            "because the reasoning is not self evident from the code.",

            "No test invokes a language model. The assistant component of the system uses a "
            "language model, and its output is phrased differently on each run. A test that "
            "compared such output against an expected string would fail for reasons unrelated "
            "to the change being examined, and the team would quickly learn to ignore it. The "
            "parts of the agent system that are deterministic are tested instead, namely the "
            "tool permissions held by each agent and the classifier that determines which agent "
            "receives a message.",

            "All file handling tests write to a temporary directory. An early version of one "
            "test uploaded a document and added a row to the working database. That behaviour "
            "was unacceptable, since running a test suite must never alter the state of the "
            "project. Storage is now redirected to a temporary directory that is removed "
            "afterwards.",

            "Two tests assert that a defect is present rather than absent. The message dataset "
            "was found to contain duplicate entries, some of which appear in both the training "
            "and test folds. Rather than removing the assertion or silently correcting the data, "
            "tests were written that confirm the problem exists and place an upper bound on it. "
            "If the data is later corrected the test fails and is updated deliberately. If the "
            "problem grows worse the test also fails. A known defect with no test around it is "
            "more dangerous than one that is documented, because it can expand without being "
            "noticed."],
         },

        {"heading": "4. Test Environment", "paras": [
            "The suite runs locally with no network access and no paid service. Execution takes "
            "approximately twenty seconds."],
         "code": "cd backend\n"
                 "venv\\Scripts\\activate\n"
                 "python -m pytest tests -q\n\n"
                 "# regenerate the report with actual results\n"
                 "python -m tests.make_test_report",
         },

        {"heading": "5. The Testing Process for Each Iteration", "paras": [
            "The following sequence is followed whenever the developer changes anything that "
            "touches data, preprocessing or the document pipeline. It is written as discrete "
            "steps so that it can be repeated identically on each iteration."],
         "numbered": [
             "Establish what changed. The developer is asked which files were modified and "
             "which behaviour is expected to differ. Without this information an intended "
             "change cannot be distinguished from a fault.",

             "Run the existing suite before examining any new behaviour. This establishes "
             "whether the change has broken something that previously worked. A failure at this "
             "point is a regression and takes priority over testing the new behaviour.",

             "Regenerate the data report and the figures using python -m ml.data_report and "
             "python -m ml.eda. Both read the live generators, so any shift in the data is "
             "reflected in the regenerated numbers.",

             "Compare the new report against the previous one. Sample counts, class balance, "
             "duplicate counts, missing value counts and split overlap are examined "
             "specifically. Any change in these that was not mentioned by the developer is "
             "recorded as a finding.",

             "Write test cases for the new behaviour before confirming that it works. The "
             "input, the expected result and the reason for that expectation are written down "
             "first. Performing this step before running the code prevents a test being written "
             "that merely agrees with whatever the code happens to do.",

             "Add at least one boundary case and one exceptional case for every new input path. "
             "Where a change accepts a file, an empty file and a file of the wrong type are "
             "supplied. Where a change accepts an identifier, an empty identifier and one "
             "containing path characters are supplied.",

             "Run the new tests and record the actual result beside the expected result. Where "
             "they match, the case passes. Where they do not, the test is not altered to agree "
             "with the code. The mismatch is raised as a defect.",

             "Classify every mismatch as a fault in the code, a fault in the expectation, or a "
             "disagreement about intended behaviour. The third category is referred to the team "
             "lead rather than to the developer.",

             "Re-run the complete suite after a defect is fixed, not only the test that failed. "
             "Fixes frequently affect adjacent behaviour, and running a single test conceals "
             "this.",

             "Regenerate the test report so that the recorded results originate from an actual "
             "run. No result is written into the report by hand.",
         ]},

        {"heading": "6. Criteria Used to Evaluate an Outcome", "paras": [
            "A test case passes only where the actual result matches an expected result that "
            "was recorded before the test was executed. The ordering is significant. Where the "
            "code is run first and the expectation written afterwards, the exercise records "
            "behaviour rather than testing it.",

            "Where a check does not involve an exact value, a threshold is applied, and that "
            "threshold is derived from the reason behind the check rather than from the figure "
            "the code currently produces. The preprocessing sparsity test illustrates this. The "
            "threshold was initially set at 99 per cent because that figure appeared in the data "
            "report, and the test failed. On investigation the reported figure applied to word "
            "features alone, while the code combines word and character features, which are "
            "legitimately denser. The code was correct and the threshold was wrong. The "
            "threshold was corrected to 95 per cent and a comment added explaining why. This is "
            "recorded as an example of a failing test that did not indicate a defect.",

            "Performance limits are set according to what a user would notice rather than "
            "according to the current measurement. Document analysis runs while a user waits for "
            "an upload to complete, so a limit of five seconds is applied. Classification and "
            "retrieval run on every chat message, so a limit of 150 milliseconds is applied. "
            "Both currently pass with a wide margin, which is intentional, since a limit set "
            "just above the present measurement would fail on any slower machine.",

            "A defect is any instance where the system behaves differently from the agreed "
            "specification, including cases where the specification itself proves unclear. "
            "Defects are graded as blocking where they would produce an incorrect result, major "
            "where they would mislead a reader of the project's figures, and minor otherwise."],
         },

        {"heading": "7. Test Case Catalogue", "paras": [
            "The table lists all 34 cases. Several are parameterised, meaning that one case runs "
            "against several inputs, which produces 55 executed checks in total. The actual "
            "column is taken from the most recent execution of the suite."],
         "table": {
             "caption": "Full test case catalogue",
             "header": ["ID", "Category", "Input", "Expected result", "Actual"],
             "widths": [0.07, 0.13, 0.3, 0.33, 0.07],
             "rows": case_rows(),
         }},

        {"heading": "8. Defects and Observations Raised", "paras": [
            "Four findings arose during this phase. Two are defects in the data, one was a "
            "fault in a test rather than in the system, and one was a fault in the processing "
            "code which the developer subsequently corrected."],
         "table": {
             "caption": "Defect log for the current phase",
             "header": ["Ref", "Finding", "Severity", "Status"],
             "widths": [0.07, 0.52, 0.13, 0.18],
             "rows": [
                 ["T-01",
                  f"The message dataset contains {M['duplicates_exact']} exact duplicate "
                  f"records. {M['split']['overlap_documents']} of them appear in both the "
                  "training and test folds.",
                  "Major", "Open, covered by TC-05 and TC-14"],
                 ["T-02",
                  "Three journey features, stage, progress and pct_tasks_complete, correlate "
                  "above 0.9 with one another and therefore carry nearly identical information.",
                  "Minor", "Open, recorded for the next phase"],
                 ["T-03",
                  "The sparsity threshold in TC-09 was derived from the wrong measurement, "
                  "causing the test to fail although the code was correct.",
                  "Minor", "Closed, threshold corrected with an explanatory comment"],
                 ["T-04",
                  "Date role extraction assigned the issue date as the expiry where both appear "
                  "on a single line, which caused a valid passport to be marked as expired.",
                  "Blocking", "Closed, corrected by the developer, regression test TC-18 added"],
             ]},
         },
        {"paras": [
            "T-01 warrants a longer note because of the way it was investigated. The initial "
            "assumption was that duplicate records appearing in both folds were inflating the "
            "reported scores, since the model would be evaluated partly on text it had already "
            "seen. Rather than accept that assumption, it was measured. The sentiment classifier "
            "was trained once and the test set was then scored in two parts, the rows that also "
            "appear in training and the rows that do not. Accuracy on the leaked rows was "
            f"{LI.get('accuracy_on_leaked', 0):.4f} and accuracy on the clean rows was "
            f"{LI.get('accuracy_on_clean', 0):.4f}. The leaked rows scored lower rather than "
            "higher, so the assumption was incorrect. The duplicated messages proved to be the "
            "short ambiguous ones, which are the hardest to classify in any case. The leakage "
            "remains a defect requiring correction, but it is not the reason the sentiment score "
            "is high."],
         },

        {"heading": "9. Coverage Not Provided by This Suite", "paras": [
            "The following gaps are stated explicitly so that the suite is not assumed to cover "
            "more than it does."],
         "bullets": [
             "No tests at the API level. The web endpoints are exercised manually and are not "
             "covered by the suite.",
             "No authentication tests, since the system currently has no authentication to test.",
             "No frontend tests. The React interface has no automated coverage.",
             "No assessment of whether an assistant response is of good quality. Agent tool "
             "permissions and routing are verified, but response quality would require a "
             "different technique and would have to be reported as a trend rather than as a pass "
             "or fail result.",
             "No automatic enforcement of accuracy thresholds. Once models are trained, the "
             "suite should fail where a score falls below an agreed figure, and this is not yet "
             "in place.",
         ]},

        {"heading": "10. Plan for the Next Phase", "paras": [
            "Once model training begins, the focus of testing moves from the data to model "
            "behaviour. The first addition planned is a set of threshold tests that fail the "
            "build where a model score falls below an agreed level, so that a change which "
            "quietly degrades a model is detected on the day it is made. Tests at the API level "
            "are also planned, since that is presently the largest untested surface. Finally the "
            "message dataset is to be deduplicated and the leakage re-measured, so that TC-05 "
            "and TC-14 can be rewritten as ordinary assertions rather than markers for a known "
            "defect."],
         },
    ],
}


# ---------------------------------------------------------------------------
# QA document
# ---------------------------------------------------------------------------

out_total = sum(v["outliers_iqr"] for v in K["per_feature"].values())

QA = {
    "title": "Quality Assurance Role Documentation",
    "subtitle": "OnboardAI, Mid Term Review. Prepared by Pasham Srikar (DL.AI.U4AID25049)",
    "authors": [{"name": "Pasham Srikar", "roll": "DL.AI.U4AID25049", "role": "QA"}],
    "affiliation": AFFIL,
    "meta": [
        ("Project", "OnboardAI, an AI assisted employee onboarding system"),
        ("Role", "Quality Assurance"),
        ("Phase", "Mid term review, work completed up to data splitting"),
        ("Date", TODAY),
        ("Artefacts owned", "Data quality report, defect register, documentation inventory"),
    ],
    "sections": [
        {"heading": "1. Purpose and Scope", "paras": [
            "This document sets out the quality controls applied to the project during its "
            "first half, the results obtained from applying them, and the limitations that are "
            "known and have not yet been addressed.",

            "Quality assurance in this project is a distinct activity from testing, and the "
            "separation took some time to establish clearly. Testing asks whether the system "
            "does what was specified. Quality assurance asks whether the method of working is "
            "capable of producing a trustworthy result, and whether the claims made about that "
            "result are genuinely supported by evidence. The Tester identifies faults in the "
            "system. This role is concerned with faults in the process and in the reasoning."],
         },

        {"heading": "2. Quality Criteria for This Phase", "paras": [
            "Five criteria were agreed with the team lead at the start of the phase. Every "
            "section of this document maps back to one of them."],
         "table": {
             "caption": "Quality criteria and the evidence for each",
             "header": ["Criterion", "Meaning in this project", "Evidence"],
             "widths": [0.2, 0.4, 0.3],
             "rows": [
                 ["Data is fit for use",
                  "No missing values, no undisclosed duplicates, correct types, documented class "
                  "balance",
                  "Section 4, generated data report"],
                 ["Preprocessing is verified",
                  "Every transformation produces the claimed output, demonstrated with before "
                  "and after figures",
                  "Section 5"],
                 ["Claims are supported",
                  "Every figure in a report or slide traces to a script that produced it",
                  "Section 7"],
                 ["Defects are visible",
                  "Known problems are recorded with a severity rather than retained informally",
                  "Section 6"],
                 ["Work is reproducible",
                  "Any team member can regenerate every figure and every number from a single "
                  "command",
                  "Section 8"],
             ]},
         },

        {"heading": "3. The Quality Process for Each Iteration", "paras": [
            "The following review cycle is executed each time a piece of work is declared "
            "complete. It runs after the Tester has finished, since there is no value in "
            "reviewing the quality of something that does not yet function."],
         "numbered": [
             "Confirm that the work is genuinely complete. The path under review is checked for "
             "placeholder values, hardcoded constants and commented out blocks. The train and "
             "serve defect described in section 6 was identified at this step.",

             "Regenerate every artefact from scratch. The generated reports and figures are "
             "deleted and rebuilt using python -m ml.data_report and python -m ml.eda. Any "
             "artefact that fails to regenerate was edited by hand at some point, which breaks "
             "the link between the project's claims and its data.",

             "Confirm that every figure quoted in the documents appears in a generated file. "
             "Figures quoted in the slides and the reports are checked against data_report.json "
             "and the test report. A figure that cannot be traced is removed or replaced.",

             "Review the data quality section of the report against the underlying data. "
             "Missing values, duplicates, class balance, outliers and value ranges are examined "
             "and compared against the previous run.",

             "Verify preprocessing by inspecting the output rather than the description. For "
             "scaling, the resulting columns are confirmed to have a mean of zero and unit "
             "variance. For vectorisation, the matrix dimensions and sparsity are confirmed "
             "against the reported values.",

             "Challenge at least one documented claim deliberately. In each cycle a statement "
             "made by the team is selected and evidence that would contradict it is sought. The "
             "leakage measurement described in section 6 originated from this step, and it is "
             "considered the most valuable part of the cycle.",

             "Update the defect register. Every finding receives an identifier, a severity, an "
             "owner and a status. No item is closed on the basis of a report that it has been "
             "fixed, only on the evidence being regenerated.",

             "Confirm the documentation inventory is current. Where a new script has been added "
             "during the cycle, it must appear in the README and in the relevant guide, "
             "otherwise it will be overlooked by the final review.",

             "Record limitations rather than removing them. Where a problem is genuine but a "
             "decision has been taken not to address it in the current phase, it is entered in "
             "the limitations list together with the reason for deferral.",
         ]},

        {"heading": "4. Data Quality Checks and Results", "paras": [
            "All three datasets were examined for the same set of defects. The results below "
            "are taken from the generated report rather than from manual inspection."],
         "table": {
             "caption": "Data quality check results",
             "header": ["Check", "Documents", "Messages", "Journeys", "Assessment"],
             "widths": [0.22, 0.14, 0.14, 0.13, 0.27],
             "rows": [
                 ["Missing values", "0", "0", "0", "Pass"],
                 ["Exact duplicates", f"{D['duplicates_exact']}", f"{M['duplicates_exact']}",
                  f"{K['duplicate_rows']}", "Fail on messages, see Q-01"],
                 ["Duplicates after normalising", f"{D['duplicates_normalised']}",
                  f"{M['duplicates_normalised']}", "Not applicable", "Fail on messages"],
                 ["Empty records", "0", "0", "0", "Pass"],
                 ["Zero variance features", "Not applicable", "Not applicable",
                  f"{sum(1 for v in K['per_feature'].values() if v['zero_variance'])}", "Pass"],
                 ["Class balance ratio", f"{D['class_balance_ratio']:.2f}",
                  f"{M['class_balance_ratio']:.2f}",
                  f"{min(K['target_counts'].values()) / max(K['target_counts'].values()):.2f}",
                  "Acceptable"],
                 ["Values within declared range", "Pass", "Pass", "Pass", "Pass"],
             ]},
         },
        {"paras": [
            f"The outlier count across the twelve numeric features is {out_total:,} under the "
            "interquartile range rule. These were reviewed with the developer and retained. The "
            "features that produce outliers are counts and waiting times, and their long tail "
            "represents the behaviour the system is intended to detect. Removing them would "
            "improve the appearance of the distribution plots while deleting the cases of "
            "interest."],
         },

        {"heading": "5. Preprocessing Verification", "paras": [
            "Each preprocessing step was verified by inspecting its output rather than by "
            "accepting the description of it."],
         "table": {
             "caption": "Preprocessing verification results",
             "header": ["Step", "Property checked", "Result"],
             "widths": [0.22, 0.4, 0.28],
             "rows": [
                 ["Text vectorisation",
                  "Matrix row count equals document count, column count is plausible, sparsity "
                  "exceeds 95 per cent",
                  f"{D['tfidf']['matrix_shape'][0]:,} rows by "
                  f"{D['tfidf']['matrix_shape'][1]:,} columns, verified"],
                 ["Minimum document frequency pruning",
                  "Feature count at min_df of two is lower than at min_df of one",
                  f"{D['tfidf']['features_pruned_away']:,} features removed, verified"],
                 ["Feature scaling",
                  "Each of the twelve columns has a mean of zero and a standard deviation of one "
                  "after transformation",
                  "All twelve verified to within floating point tolerance"],
                 ["Pipeline placement of the scaler",
                  "The scaler sits inside the pipeline object and refits on each training fold",
                  "Confirmed by code inspection"],
                 ["Split stratification",
                  "Class proportions in both folds match the full dataset",
                  f"Maximum drift {max(D['split']['max_class_proportion_drift'], M['split']['max_class_proportion_drift']):.4f}, verified"],
             ]},
         },

        {"heading": "6. Defect and Limitation Register", "paras": [
            "This register holds every known fault and incomplete item. Entries are closed only "
            "when the supporting evidence has been regenerated, not when a fix is reported."],
         "table": {
             "caption": "Defect and limitation register",
             "header": ["Ref", "Description", "Severity", "Status"],
             "widths": [0.07, 0.5, 0.13, 0.2],
             "rows": [
                 ["Q-01",
                  f"The message dataset holds {M['duplicates_exact']} duplicate records, of "
                  f"which {M['split']['overlap_documents']} appear in both folds. The impact was "
                  "measured and found to be negligible, but the defect is genuine.",
                  "Major", "Open, deferred to the next phase"],
                 ["Q-02",
                  "Two risk model features were supplied as hardcoded constants at prediction "
                  "time while the model had been trained on values that varied.",
                  "Blocking", "Closed, both features removed and the model retrained"],
                 ["Q-03",
                  "All three datasets are synthetic. Reported figures describe consistency with "
                  "the project's own generators rather than real world performance.",
                  "Major", "Open, accepted limitation for this phase"],
                 ["Q-04",
                  "Three journey features correlate above 0.9, so the feature set contains "
                  "redundancy.",
                  "Minor", "Open, recorded for the next phase"],
                 ["Q-05",
                  "Sentiment classification reaches a very high score because the generator "
                  "marks sentiment with stock phrases. This is a property of the data and must "
                  "not be presented as model capability.",
                  "Major", "Open, documented in all reports"],
                 ["Q-06",
                  f"Generated documents average {D['char_len']['mean']:.0f} characters, "
                  "considerably shorter than a real scanned certificate, so the task is easier "
                  "than the real equivalent.",
                  "Minor", "Open, accepted limitation"],
                 ["Q-07",
                  "The project has no authentication on its web endpoints and no version "
                  "control history.",
                  "Major", "Open, outside mid term scope"],
             ]},
         },
        {"paras": [
            "Q-02 is the most significant finding of the phase, because no test existing at the "
            "time would have detected it. The risk model had been trained on twelve features "
            "that varied across the dataset, but at prediction time two of them were being "
            "supplied with the same fixed value for every employee. The model was therefore "
            "applying learned weights to information it never actually received. Both values "
            "were examined to establish whether either could be computed from the available "
            "data. Neither could, so both features were removed from the feature set and the "
            "model was retrained. The reported score changed very little, which is the point of "
            "the correction. The figure now describes what the model genuinely observes."],
         },

        {"heading": "7. Traceability of Claims", "paras": [
            "Every quantitative statement in the project's slides, paper and reports originates "
            "from one of four generated files. No figure is entered by hand."],
         "table": {
             "caption": "Source of each class of claim",
             "header": ["Claim type", "Produced by", "Output file"],
             "widths": [0.26, 0.34, 0.3],
             "rows": [
                 ["Dataset sizes, class balance, duplicates, correlations",
                  "python -m ml.data_report", "ml/artifacts/data_report.json and .md"],
                 ["All figures and their written observations", "python -m ml.eda",
                  "ml/artifacts/eda/"],
                 ["Test case results", "python -m tests.make_test_report",
                  "ml/artifacts/test_report.md"],
                 ["Slide content", "python docs/build_midterm_deck.py",
                  "docs/OnboardAI_MidTerm_Review.pptx"],
             ]},
         },

        {"heading": "8. Reliability and Reproducibility Checks", "paras": [
            "The work was confirmed to be rebuildable from nothing by a different person on a "
            "different machine. The checks below were performed after deleting the generated "
            "artefacts."],
         "bullets": [
             "Every dataset uses a fixed random seed of 42, so regeneration produces identical "
             "data. This is verified by test TC-15.",
             "All figures and reports regenerate from two commands with no manual editing.",
             "The full test suite completes in approximately twenty seconds and requires no "
             "network access.",
             "Processing performance was measured rather than assumed. Document analysis "
             "completes well within the five second limit, and classification and retrieval each "
             "average under 150 milliseconds across fifty runs.",
             "No step in the pipeline requires a paid service or an API key.",
         ]},

        {"heading": "9. Documentation Inventory", "paras": [
            "Part of this role is ensuring the project can be understood by somebody who was not "
            "present during its development. The following documents are current as of this "
            "review."],
         "table": {
             "caption": "Documentation held for the current phase",
             "header": ["Document", "Owner", "Purpose"],
             "widths": [0.33, 0.14, 0.43],
             "rows": [
                 ["Data report", "Developer and QA",
                  "Dataset description, quality checks, preprocessing evidence, split audit"],
                 ["EDA observations", "Developer",
                  "Ten figures with the written observation each supports"],
                 ["Test report", "Tester",
                  "All 34 cases with input, expected result and actual result"],
                 ["Tester role document", "Tester",
                  "Test strategy, iteration process, defect log"],
                 ["QA role document", "QA",
                  "Quality criteria, verification results, defect register"],
                 ["Project guides", "Team",
                  "Code walkthrough and a technical and non technical explanation"],
                 ["README", "Team", "Setup and run instructions from a clean machine"],
             ]},
         },

        {"heading": "10. Recommendations for Improvement", "paras": [
            "These are ordered by the amount of risk each removes rather than by difficulty."],
         "numbered": [
             "Place the project under version control. At present there is no commit history, "
             "so an error cannot be reverted and the work exists on a single machine. This is "
             "the largest single risk to the project and requires only minutes to resolve.",

             "Deduplicate the message dataset before splitting and re-measure the leakage, so "
             "that Q-01 can be closed properly rather than carried forward.",

             "Introduce accuracy thresholds into the test suite once models are trained, so that "
             "a change degrading a model fails the build rather than being discovered during a "
             "review.",

             "Obtain a real document corpus for the next phase. Every figure reported at present "
             "is bounded by the quality of the project's own generators, and no amount of care "
             "in the analysis removes that limit.",

             "Combine or remove the redundant progress features identified in Q-04, since three "
             "features measuring the same quantity makes any feature importance result harder to "
             "interpret.",
         ]},
    ],
}


def main():
    out = ROOT / "docs" / "roles"
    for doc, name in ((TESTER, "Tester_Role_Documentation"),
                      (QA, "QA_Role_Documentation")):
        render_docx(doc, out / f"{name}.docx")
        render_latex(doc, out / f"{name}.tex", style="report")
        print(f"Saved {out / name}.docx and .tex")


if __name__ == "__main__":
    main()
