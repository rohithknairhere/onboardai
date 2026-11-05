# Final Review: How to Demonstrate OnboardAI

The demonstration has two halves. First the examiners watch the product do its job, as an
employee would see it. Then they see how well it does it, on test cases they can inspect and
even type themselves. Allow about 12 minutes.

**Team for the final review:** Kritika Sah (Team Lead), Rohith K Nair (Developer, all
application code: document verification, chatbot and app), Prisha Saini (Developer, evaluation
and tests), Pasham Srikar (Developer, risk model and data pipeline).

Who presents what: Rohith runs the live product in Part 1, Prisha presents the measured results
in Part 2, Srikar covers the risk model and data, and Kritika opens, closes and handles the HR
view.

---

## Before the review (do this 15 minutes early)

1. Start Ollama if it is not already running (it starts with Windows on this laptop).
2. Start the back end: in a terminal, go to the `backend` folder, activate the virtual environment with `venv\Scripts\activate`, then run `uvicorn main:app --port 8000`.
3. Start the front end: in a second terminal, from the project folder, run `npm run dev`.
4. Open `http://localhost:5173`, log in as **hr1 / @hr1**, click **Evaluation Lab**.
5. Click **Warm up model**. The first answer after Ollama starts can take three minutes while the
   model loads into memory. After warm-up every answer takes 20 to 45 seconds. Wait for
   "Model ready".
6. Click **Reset demo data** so every employee is back at the starting state.
7. Keep `4_Final_Evaluation.pdf` (in `docs/pdf/final_review/`) open in another window. It holds the same results, produced
   offline, in case anything fails on the day.

Do not refresh the browser during the demo: logins are not remembered across a page reload, so a
refresh sends you back to the login screen.

---

## Part 1: The product working (about 5 minutes)

### 1a. Document verification, live (Rohith)

Log in as **employee 1 / @1** (Shreya, Nimbus Labs). Her passport and bank form are still
outstanding.

| Step | Upload this file from `backend/demo_documents/final_review/` | Against | What happens |
| --- | --- | --- | --- |
| 1 | `D04_valid_passport_...pdf` | Govt ID / Passport | Approved in under a second. Open the analysis to show the type confidence, the name match and the expiry date it read. |
| 2 | `D10_cafeteria_memo_...pdf` | Direct Deposit Form | Rejected: "does not look like any onboarding document". |
| 3 | `D12_signed_salary_account_form_...pdf` | Direct Deposit Form | Approved. The rejection is replaced. |

The file names say what each file should produce so you can find the right one quickly. The
pipeline never reads the file name, only the contents. If an examiner doubts this, rename a file
and upload it again.

What to say: *"Approval needs a confident classification and every check passing. Anything
uncertain goes to a person. Wrongly approving a document is the expensive mistake, so the
system is built to avoid it."*

### 1b. The chatbot, live (Rohith)

Still as Shreya, open the assistant (bottom-right button) and send these one at a time. Each
takes 20 to 45 seconds.

| Send | What to point out |
| --- | --- |
| How many days of annual leave do I get? | Routed to the Policy Agent. Answers **24 days** and cites *Leave Policy (Nimbus Labs), Annual leave*. |
| Is there a gym membership allowance? | The handbook does not cover it, so it says so and offers HR instead of inventing an answer. |
| I need access to AWS | Routed to the IT Provisioning Agent, which offers to raise a request. |

Then log out and log in as **employee 2 / @2** (Adithya, Veltrix Corp) and ask the same leave
question. The answer is **18 days**, from Veltrix's handbook. *"Same question, different company,
different answer, and neither employee can ever see the other company's policies."*

### 1c. HR sees it (Kritika)

Log in as **hr1 / @hr1**. Open Shreya: the uploads, the automated verdicts and the activity log
are all there, and HR can overrule the model. Every overrule is recorded as a label for
retraining.

---

## Part 2: How well it works (about 7 minutes)

Stay logged in as HR and open **Evaluation Lab**. Say first: *"Every case on this page was
written by hand after training, in wording the training data never used. We are showing where
it fails as well as where it works."*

### 2a. Chatbot tab (Prisha)

1. **Try any message.** Ask an examiner to suggest a message, or type
   `I still have no laptop and my passport number is K4471902`. Show the intent probabilities,
   the chosen specialist, the sentiment score and that the passport number is removed before
   anything reaches the language model.
2. **Try any policy question.** Ask the annual leave question, then switch the employee from
   Shreya to Adithya. The top passage changes from 24 days to 18 days.
3. **Layer 1, routing: Run 48 messages.** Show the two accuracy figures side by side:
   93.7% on the synthetic test set, about 73% on hand-written messages. This is the honest
   headline. Tick **Show misses only** and talk through two or three of them.
4. **Layer 2, policy search: Run 16 questions.** The right passage is ranked first for most
   questions and is in the top 3 for almost all of them. Both "not in the handbook" questions
   correctly find nothing, and no question ever returns the other company's handbook.
5. **Layer 3, full answers.** The last full run is already shown: the right fact in 11 of 12
   answerable questions, the handbook section cited in 9 of 12, and a correct decline in 3 of 4
   questions the handbook cannot answer. Open P02 (Veltrix, 18 days, cited) and P11 (handed on
   from the Onboarding Agent to the Policy Agent, right answer but no citation, so marked as a
   fail). To prove it is live, click **Run** on P01 (about 30 seconds).

### 2b. Document verification tab (Prisha)

1. **Verify 16 documents.** All 16 get the verdict an HR officer would give, and the key number
   is **0 bad documents approved**. The matrix shows expected against given verdicts.
2. Expand three cases:
   - **D03, blank signature line.** This used to be read as signed. We found it with this
     benchmark and fixed it.
   - **D09, expiring in 10 days.** Valid today, but HR is warned. The date is worked out from
     today, so this is true whenever the test runs.
   - **D15, damaged scan.** Letters swapped for digits and words broken apart, still classified
     correctly because the model also reads groups of 3 to 5 characters, not just whole words.
3. **Try any document.** Ask an examiner to pick any file from `final_review/`, or any PDF on the
   laptop, and choose what it is supposed to be.

### 2c. The risk model (Srikar)

Srikar also answers questions about the data every model learned from: three generated
datasets (4,950 documents, 3,360 messages, 6,000 journeys), the 75/25 stratified split and the
leakage audit. The numbers are in `docs/REVISION_NOTES.md`.

On the HR dashboard show the **Predicted stall risk** list; each employee's main risk driver is
named under the score. Then log out and log in as **hr2 / @hr2** (Veltrix Corp; hr1 only sees
Nimbus Labs) and open Adithya, who is blocked by an expired safety certificate. His detail page
lists the features that drive his risk score.

Also point out **Documentation gaps** on the dashboard: every policy question the handbook could
not answer during the chatbot demo appears here, so HR knows which page to write next. Model quality is in
`backend/ml/artifacts/risk_report.md` (ROC-AUC 0.81 under 5-fold cross-validation).

---

## Questions to expect

**Why is the routing accuracy lower on your own test set?**
The classifier was trained on generated messages built from templates. Real people phrase things
differently. We wrote the hand-written set specifically to measure that gap rather than report
only the flattering number. The next step is training on real or more varied messages.

**What happens when a message is routed to the wrong agent?**
Each specialist only holds the tools for its own job, and every one of them can hand the
conversation to the right specialist once. Low-confidence messages are not forced into a
specialist at all; the general Onboarding Agent takes them.

**How do you stop the chatbot inventing policy?**
The Policy Agent must search before answering and cite the section. If the best match scores
below 0.42, the search tool tells the agent there is no documented answer, and the question is
logged as a gap in the handbook for HR to fill. These gaps show on the HR dashboard.

**Could the model approve a forged document?**
It checks type, name, expiry and signature. It cannot detect a skilled forgery, which is why
HR can overrule any verdict and every overrule is logged. The system's job is to clear the
obvious cases so that people spend their time on the hard ones.

**Did you tune the system on this test set?**
We fixed five defects the benchmark exposed: blank signature lines, photos without OCR, the
"certifies that" name pattern, plural words in policy search, and agents that received a
transfer trying to transfer again instead of answering. We did not retrain any model
on these cases and the results show the remaining failures as they are. The same people wrote
the cases and the fixes, so a fully independent test set written by someone outside the team
would be the stronger check.

**Why a local model?**
No API key, no cost, no usage limit, and employee messages never leave the machine. The code
can switch to Gemini or Groq by changing one setting in `backend/.env`.

---

## If something goes wrong

| Problem | Fix |
| --- | --- |
| Chat says AI features are offline | Ollama is not running. Start it, then press **Warm up model** again. |
| First chat reply takes minutes | The model was not warmed up. Wait once; later replies are fast. |
| Browser shows the login page mid-demo | The page was refreshed. Log in again, nothing is lost. |
| Uploads show old results | Press **Reset demo data** in the Evaluation Lab. |
| Anything else | Open `4_Final_Evaluation.pdf`: same cases, same results, produced offline. |
