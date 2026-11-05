# OnboardAI Backend

The OnboardAI backend is built with **FastAPI** and **Python**. It serves as the data layer and AI orchestration engine for the OnboardAI application, providing RESTful endpoints for the React frontend and exposing an agentic chatbot endpoint powered by **LangChain**.

## Features

- **FastAPI**: High-performance, easy-to-use asynchronous web framework.
- **SQLAlchemy & SQLite**: Relational database ORM, currently configured with a local SQLite database (`onboardai.db`) for easy local development.
- **Agentic Chatbot**: Utilizes LangChain's `AgentExecutor` to create a conversational agent capable of using tools to read from and mutate the database.
- **Department-Specific Models**: A framework (`nlp/department_models.py`) to run targeted NLP tasks and RAG (Retrieval-Augmented Generation) depending on the employee's organization or department.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) for local LLM inference (free, no API key)

The project runs entirely on free, local models. No paid API is required at any
point; `langchain-openai` has been removed in favour of `langchain-ollama`.

## Setup Instructions

### 1. Create a Virtual Environment

It's recommended to run the backend inside a virtual environment to manage dependencies cleanly.

```bash
python -m venv venv
```

Activate the virtual environment:
- **Windows**: `.\venv\Scripts\activate`
- **macOS/Linux**: `source venv/bin/activate`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup the Database

The database needs to be created and seeded with initial mock data (Organizations, Employees, Tasks, etc.). Run the seed script:

```bash
python seed.py
```
This will create `onboardai.db` in the current directory and populate it.

### 4. Set up the local LLM

Install Ollama, then pull the model the agent uses by default:

```bash
ollama pull qwen2.5:7b
```

Ollama serves on `http://localhost:11434` and starts automatically. Nothing else
is required — there is no API key and no cost.

Configuration is optional; copy `.env.example` to `.env` to change anything:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | `ollama`, `gemini`, or `groq` |
| `LLM_MODEL` | provider default | Override the model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is listening |

`gemini` and `groq` are free-tier cloud fallbacks, useful if the machine running
the demo has no GPU. They need `GOOGLE_API_KEY` / `GROQ_API_KEY` and the matching
optional package from `requirements.txt`.

On a 4GB GPU, switch to `LLM_MODEL=qwen2.5:3b` if the 7B model feels sluggish.

If the model is unreachable the app degrades gracefully: the dashboard works
normally and the chat explains that AI features are offline. Check
`GET /api/health` to see what the server thinks the LLM status is.

### 5. Run the Server

Start the FastAPI development server:

```bash
uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`. 
You can view the interactive API documentation (Swagger UI) at `http://localhost:8000/docs`.

## Project Structure

- `main.py`: Application entry point, CORS configuration, and `/api/health`.
- `database.py`: SQLAlchemy database connection setup.
- `models.py`: Database table definitions.
- `schemas.py`: Pydantic models for data validation and serialization.
- `seed.py`: Script to populate the database with initial mock data.
- `llm_provider.py`: Chooses the LLM backend from env vars. The only place any
  provider is named, so swapping Ollama for Gemini or Groq needs no code change.
- `storage.py`: Upload storage. Files are stored under a generated UUID, and the
  real file type is verified from its magic bytes rather than trusting the
  client-declared content type.
- `events.py`: Writes to the structured event stream.
- `routes/api.py`: Standard CRUD endpoints for employees and organizations.
- `routes/chat.py`: The main conversational endpoint that interfaces with the AI agent.
- `routes/documents.py`: Document upload, retrieval, and per-employee event feed.
- `agents/chatbot.py`: LangGraph tool-calling agent. Tools are bound to one
  employee id in a closure, so the model cannot read another employee's record.
- `nlp/department_models.py`: Stubs for organization and department-specific model logic (e.g., specialized document extraction).

## Document intelligence (ML)

Uploaded documents run through `ml/pipeline.py`:

`extract text -> classify type -> extract fields -> validate -> route`

- **Text extraction** (`ml/extract.py`) prefers a PDF's real text layer and falls
  back to OCR for scans. OCR is an optional dependency: without an engine
  installed the pipeline still runs and reports that it could not read the image.
- **Type classifier** (`ml/classifier.py`) is TF-IDF over combined word (1-2) and
  character (3-5) n-grams feeding a calibrated LinearSVC. Character n-grams are
  what let it survive OCR damage that destroys whole words.
- **Field extraction** (`ml/fields.py`) pulls dates, names, and identifiers.
  Dates are assigned a role by the *nearest preceding label*, because identity
  documents routinely put issue and expiry on a single line.
- **Validation** (`ml/validate.py`) checks type match, expiry, name match, and
  signature presence, each with a severity.
- **Routing** (`ml/pipeline.py`) auto-approves only on a confident
  classification with clean checks; a blocking failure auto-rejects, and
  everything else goes to a human. Approving wrongly costs far more than asking.

Retrain and re-evaluate:

```bash
python -m ml.train_classifier
```

Held-out results (`ml/artifacts/classifier_report.md`), 9 classes, 4950 documents:

| Scan quality | Accuracy |
| --- | --- |
| clean | 1.000 |
| degraded | 1.000 |
| severe | 0.937 |

Overall accuracy 0.986, macro-F1 0.986, 5-fold CV macro-F1 0.986 ± 0.004.

The corpus is generated by `ml/synth.py` at three degradation tiers, because a
clean template corpus is trivially separable and yields a meaningless 100%. The
`severe` tier crops the document, strips its header, injects 10-20% character
noise, and bleeds in text from other document types.

Generate demo PDFs for testing or a live demonstration:

```bash
python -m ml.make_demo_docs
```

### The improvement loop

`document_uploads.verdict` records what the model concluded;
`hr_decision` records what a human concluded. `GET /api/ml/agreement` reports how
often they match, and the disagreements are the labelled examples the next model
is trained on. HR can override an auto-approval precisely so that this signal
keeps being collected.

## NLP layer

`ml/nlp_models.py` runs two classifiers over every employee message, both
TF-IDF (word + character n-grams) into logistic regression:

- **Intent** (8 classes) decides which specialist agent handles the message.
  Below a confidence floor of 0.45 nothing is routed, because a bare "any
  update?" genuinely does not say what the person wants.
- **Sentiment** (3 classes) produces `p(positive) - p(negative)`, a continuous
  score. That score is written to the event stream and becomes the
  `avg_sentiment` feature of the risk model — this is the concrete link
  between the NLP and ML layers.

`ml/pii.py` strips emails, phone numbers, Aadhaar, PAN, IFSC, passport and
account numbers before any text reaches a model provider. Values are replaced
with typed placeholders and never stored, so they cannot leak into logs or the
event stream. Presidio would add ML-based NER on top; this is the
dependency-free floor.

Messages classified as escalation, or scoring below -0.60 sentiment, raise a
`chat.escalated` event for HR regardless of topic.

Retrain: `python -m ml.train_nlp` (report in `ml/artifacts/nlp_report.md`).

| Model | Accuracy | 5-fold CV macro-F1 |
| --- | --- | --- |
| Intent (8 classes) | 0.937 | 0.933 ± 0.004 |
| Sentiment (3 classes) | 0.996 | 0.996 ± 0.003 |

The intent corpus deliberately contains blended messages spanning two intents
and vague chasers whose label is genuinely unrecoverable from the text, which
is where most of the 6% error sits. **Sentiment's 0.996 is a ceiling effect of
template generation, not a real-world claim** — it should be validated against
a hand-labelled sample of real messages before anyone trusts that number.

## Retrieval (RAG)

`ml/rag.py` answers policy questions from the corpus in `backend/knowledge/`.

- **Hybrid scoring**: TF-IDF catches exact policy wording ("lockout-tagout"),
  and an LSA projection of the same matrix catches paraphrase. Asking "can I
  take time off before my probation ends" scores 0.34 lexically but 0.85
  semantically against the *Leave during probation* section — the semantic half
  is doing the work.
- **LSA rather than neural embeddings** so the system runs offline with no model
  download. The backend is swappable without changing callers.
- **Access control**: a chunk is visible only if its organisation matches and,
  where the document restricts one, its department. Nimbus and Veltrix
  employees asking the identical leave question get 24 and 18 days
  respectively, and Sales cannot retrieve the Engineering security policy.
- **Mandatory citation**: the agent must cite document and section, and is
  instructed to refuse rather than answer policy from general knowledge.

Seed the corpus with `python -m ml.knowledge_seed`.

### Documentation gaps

When retrieval finds nothing, or only weakly-matching passages, the question is
recorded as a `knowledge.gap` event and surfaced at `GET /api/knowledge/gaps`.
An assistant that cannot answer is normally a failure; here it is turned into a
work list of pages the handbook is missing. The corpus is intentionally
incomplete (parental leave, notice period and relocation are absent) so this is
demonstrable.

## Multi-agent layer

`agents/specialists.py` defines six specialists, each a separate agent with its
own system prompt and its own tool subset. Capability boundaries are enforced by
construction — a specialist is only ever handed the tools in its registry entry
— rather than by instructing one agent to pretend it lacks them.

| Specialist | Tools | Handles |
| --- | --- | --- |
| Onboarding Agent | `get_my_status`, `list_my_tasks`, `complete_task` | stage, progress, tasks; default |
| Document Agent | `list_my_documents`, `list_my_tasks` | required documents, rejections |
| IT Provisioning Agent | `raise_it_request`, `list_my_tasks` | accounts, access, hardware |
| Knowledge Transfer Agent | `list_kt_sessions` | KT sessions and contacts |
| Policy Agent | `search_company_policy` | policy, pay, benefits |
| Escalation Agent | `escalate_to_hr`, `get_my_status` | complaints, human handover |

**Routing is done by the trained intent classifier, not by an LLM.** That is one
model call cheaper, deterministic and therefore testable, and its accuracy is
measurable against a confusion matrix. Below the 0.45 confidence floor nothing
is routed and the Onboarding agent answers, because a vague message genuinely
does not identify a specialist.

**Transfer.** Every specialist holds `transfer_to_specialist`. A message that
reaches the wrong one is passed on exactly once (`MAX_TRANSFERS = 1`), which
covers the classifier's residual ~6% error without risking a loop. The API
reports `routed_to` (classifier's choice) and `transferred_from` separately from
`agent` (who actually answered).

Conversation threads are keyed `{emp_id}:{specialist}`, because replaying one
specialist's tool calls into an agent that does not hold those tools is not
safe. The trade-off is that context is not shared across a transfer.

**Known limitation:** transfer reliability depends on instruction-following. On
local `qwen2.5:7b` the first prompt revision was ignored — the Document agent
tried to answer a policy question itself — and the rule had to be made
considerably more directive. Smaller models may still occasionally answer out of
remit.

## Stall-risk model

`ml/risk_model.py` scores each employee's probability of stalling and explains
it. Features come from the live database and the event stream.

Retrain: `python -m ml.train_risk` (report in `ml/artifacts/risk_report.md`).

- Selected model: logistic regression over **12 features**, **ROC-AUC 0.795**,
  5-fold CV 0.807 ± 0.002
- Explanations are exact per-feature contributions to the log-odds. For a
  standardised linear model these *are* the SHAP values, so no sampling is
  needed and the explanation is deterministic.

Ablations (retraining with one feature removed):

| Removed feature | Δ ROC-AUC |
| --- | --- |
| `avg_sentiment` | -0.0075 |
| `days_since_last_activity` | -0.0052 |
| `docs_rejected` | -0.0005 |

### Removed features

`response_latency_hours` and `is_remote` were dropped from the feature set.
Neither is recoverable from the data model — there is no remote-working field,
and employee reply timings are not recorded — so at serving time both arrived as
hardcoded constants while the model had been trained on varying values. Two
coefficients were being applied to information the model never received.

Both are still simulated in `risk_synth.py` and still influence the outcome;
they are simply no longer offered as inputs. Real causes the system cannot
measure belong in the unobserved component, not in the feature vector. The
reported ROC-AUC now corresponds to what the model actually receives in
production.

`avg_sentiment` is produced by the NLP layer, so its ablation is the measured
evidence that the pillars are load-bearing rather than decorative.
`docs_rejected` barely moves aggregate AUC because rejections are rare, yet it
is a strong *individual* driver for the employees who have one — an aggregate
metric and a per-case explanation answer different questions.

`ml/risk_synth.py` generates training data as a latent-variable process
(engagement, friction, support) with a genuinely unobserved component, so no
feature set can predict the outcome perfectly. A score near 1.0 here would mean
the generator had leaked the answer.

## Data model notes

Two tables exist for auditing, and they are not redundant:

- `audit_logs` holds prose written for humans, and is what the HR timeline renders.
- `events` holds structured, machine-readable records. This is the feature source
  for the risk model, the agent's memory, and offline evaluation. Any action that
  skips it is invisible to the ML layer.

`document_uploads` deliberately keeps `verdict` (what the model predicted) apart
from `hr_decision` (what a human concluded). The disagreement between those two
columns is the training signal used to improve the document classifier.
