"""Run the suite and write a test report with expected vs actual results.

    python -m tests.make_test_report

Produces ml/artifacts/test_report.md. The "actual" column comes from a real run,
so the report cannot claim a pass that did not happen.
"""
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
OUT = BACKEND / "ml" / "artifacts" / "test_report.md"

SUITES = {
    "test_data_quality": ("Data quality and validation",
                          "Is the data present, complete, balanced and correctly typed?"),
    "test_preprocessing_and_split": ("Preprocessing and split integrity",
                                     "Did the transformations do what is claimed, and is the split honest?"),
    "test_pipeline_and_safety": ("Document pipeline, safety and boundaries",
                                 "Does the pipeline honour its contract, and does it refuse bad input?"),
    "test_nlp_retrieval_agents": ("NLP, retrieval and agent boundaries",
                                  "Are classifications, access control and capability limits correct?"),
}

# Case id -> (input, expected result, category)
CASES = {
    "tc01": ("Generated document corpus", "4,950 documents, 9 classes, parallel arrays aligned", "Validation"),
    "tc02": ("All three datasets", "Zero empty strings, zero NaN in features or target", "Validation"),
    "tc03": ("Document labels", "Every class within 1% of the mean count", "Validation"),
    "tc04": ("Document texts", "Zero exact duplicates", "Validation"),
    "tc05": ("Message texts", "Duplicates present but under 10% (known defect)", "Known defect"),
    "tc06": ("Risk feature matrix", "Float dtype, all finite, 12 columns, no constant column", "Validation"),
    "tc07": ("Risk target", "Values in {0,1}, positive rate between 20% and 80%", "Validation"),
    "tc08": ("Each bounded feature", "Values inside their declared domain", "Boundary"),
    "tc09": ("Document texts through the vectoriser", "Sparse matrix, one row per document, >95% sparse", "Preprocessing"),
    "tc10": ("Document texts, min_df 1 vs 2", "Pruning reduces the feature count", "Preprocessing"),
    "tc11": ("Risk features through StandardScaler", "Every column mean ~0, sd ~1", "Preprocessing"),
    "tc12": ("Documents split 75/25 stratified", "Class proportions preserved within 1% in both folds", "Split"),
    "tc13": ("Document train/test folds", "Zero records present in both folds", "Split"),
    "tc14": ("Message train/test folds", "Overlap present but under 15% (known defect)", "Known defect"),
    "tc15": ("Risk split run twice with seed 42", "Identical folds both times", "Reproducibility"),
    "tc16": ("Each of 7 demo PDFs + its requirement", "The verdict named in the filename", "Functional"),
    "tc17": ("Expired safety certificate", "Rejected, reason names the expiry date", "Functional"),
    "tc18": ("Passport line holding issue and expiry together", "Each date gets its correct role", "Regression"),
    "tc19": ("Document titled 'CERTIFICATE OF ...'", "Identifier taken from the field, not the title", "Regression"),
    "tc20": ("Zero-byte upload", "Rejected, no crash", "Boundary"),
    "tc21": ("HTML content declared as application/pdf", "Rejected on magic bytes", "Exceptional"),
    "tc22": ("File one byte over the 10MB cap", "Rejected and no partial file left on disk", "Boundary"),
    "tc23": ("Employee ids with traversal or illegal characters", "Rejected", "Exceptional"),
    "tc24": ("Crafted relative path '../../../windows/win.ini'", "Refused, cannot escape the store", "Exceptional"),
    "tc25": ("PDF with no extractable text", "Never auto-approved; routed to a human", "Validation"),
    "tc26": ("One demo PDF, warmed", "End-to-end analysis under 5 seconds", "Performance"),
    "tc27": ("One representative message per intent", "Routed to the correct specialist", "Functional"),
    "tc28": ("'any update?'", "Low confidence, not routed to a specialist", "Boundary"),
    "tc29": ("One message per sentiment class", "The matching sentiment label", "Functional"),
    "tc30": ("Message containing six identifier types", "Every value stripped before leaving", "Security"),
    "tc31": ("Same question from two organisations", "Different, organisation-correct policies", "Access control"),
    "tc32": ("Security question from permitted and non-permitted departments", "Restricted document hidden from Sales", "Access control"),
    "tc33": ("Each specialist's tool registry", "Capabilities disjoint and enforced by construction", "Architecture"),
    "tc34": ("50 classifications and 50 retrievals", "Mean under 150ms per call", "Performance"),
}


def run():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-v", "--tb=no",
         "-p", "no:cacheprovider"],
        cwd=BACKEND, capture_output=True, text=True)
    return proc.stdout + proc.stderr


def parse(output):
    results = defaultdict(list)
    for line in output.splitlines():
        # Parametrised ids can contain spaces, so match lazily up to the status
        # rather than assuming the id is a single whitespace-free token.
        m = re.match(r"tests[/\\](\w+)\.py::(test_\w+).*?\s(PASSED|FAILED|SKIPPED|ERROR)\b", line)
        if m:
            suite, test, status = m.groups()
            cid = re.match(r"test_(tc\d+)", test)
            if cid:
                results[cid.group(1)].append((suite, status))
    summary = ""
    for line in output.splitlines():
        if re.search(r"\d+ (passed|failed)", line):
            summary = line.strip()
    return results, summary


def main():
    print("Running the suite...")
    output = run()
    results, summary = parse(output)

    total = sum(len(v) for v in results.values())
    passed = sum(1 for v in results.values() for _, s in v if s == "PASSED")

    L = ["# Test Report", "",
         f"Generated {date.today().isoformat()} by `python -m tests.make_test_report`.",
         "The actual-result column comes from a real run of the suite.", "",
         f"**{len(results)} test cases, {total} executed checks, {passed} passed.**",
         f"`{summary}`", "",
         "Run the suite yourself with:", "", "```", "python -m pytest tests -q", "```", "",
         "## Scope and approach", "",
         "No language model is called anywhere in this suite. Agent behaviour is asserted",
         "through tool registries and classifier outputs, both deterministic, because a test",
         "whose result depends on generation temperature cannot act as a regression gate.",
         "Uploads are written to a temporary directory, so no test touches the development",
         "database or the real document store.", "",
         "Two cases (TC-05, TC-14) assert the *presence* of known defects rather than their",
         "absence. They document measured problems and fail if those problems grow worse.", "",
         "## Test cases", "",
         "| ID | Category | Input | Expected | Actual |",
         "| --- | --- | --- | --- | --- |"]

    for cid in sorted(CASES):
        inp, expected, category = CASES[cid]
        runs = results.get(cid, [])
        if not runs:
            actual = "not run"
        else:
            statuses = {s for _, s in runs}
            n = len(runs)
            if statuses == {"PASSED"}:
                actual = f"PASS ({n} run{'s' if n > 1 else ''})" if n > 1 else "PASS"
            elif "FAILED" in statuses:
                actual = f"**FAIL** ({sum(1 for _, s in runs if s == 'FAILED')}/{n})"
            else:
                actual = ", ".join(sorted(statuses)).title()
        L.append(f"| {cid.upper().replace('TC', 'TC-')} | {category} | {inp} | {expected} | {actual} |")

    counts = defaultdict(int)
    for _, _, category in CASES.values():
        counts[category] += 1
    L += ["", "## Coverage by category", "", "| Category | Cases |", "| --- | --- |"]
    for category, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        L.append(f"| {category} | {n} |")

    L += ["", "## What is not covered", "",
          "Stated plainly so the gaps are not mistaken for passes:", "",
          "- **No API-level tests.** Endpoints are exercised manually, not by the suite.",
          "- **No authentication tests**, because there is no authentication to test.",
          "- **No frontend tests.** No vitest or Playwright coverage exists.",
          "- **No agent-response quality tests.** Tool boundaries are asserted; whether an",
          "  answer is *good* is not, and would need an LLM-as-judge rubric reported as a",
          "  trend rather than a gate.",
          "- **No model accuracy gate in CI.** Metric thresholds are not enforced on each run.", ""]

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Saved {OUT}")
    print(f"{len(results)} cases, {total} checks, {passed} passed")


if __name__ == "__main__":
    main()
