"""Split the deck into one file per presenter and attach a script to each slide.

    backend/venv/Scripts/python.exe docs/split_deck.py

Each role deck is produced by copying the full deck and removing the slides that
role does not present, which keeps images, layouts and section breaks intact.
The script for each slide is written into the speaker notes and also exported as
a single printable document.
"""
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs"))

FULL = ROOT / "docs" / "OnboardAI_MidTerm_Review.pptx"
OUT = ROOT / "docs" / "presentation"

TEAM = {
    "lead": ("Kritika Sah", "DL.AI.U4AID25031", "Team Lead"),
    "qa": ("Pasham Srikar", "DL.AI.U4AID25049", "QA"),
    "dev": ("Rohith K Nair", "DL.AI.U4AID25043", "Developer"),
    "tester": ("Prisha Saini", "DL.AI.U4AID25039", "Tester"),
}

# slide number (1 based in the full deck) -> (role key, seconds, script)
SCRIPTS = {
1: ("lead", 40, """
Good morning. Our project is OnboardAI, a system that uses machine learning to help a company
bring new employees on board.

I am Kritika Sah and I led the team. With me are Pasham Srikar who handled quality assurance,
Rohith K Nair who wrote the code, and Prisha Saini who handled testing. Each of us will
present the part we were responsible for.

One thing before we start, so the scope is clear. This review covers our work up to data
splitting. We have not trained or evaluated any models yet, so we will not be showing
accuracy or F1 figures today. That work belongs to the next phase.
"""),

2: ("lead", 20, """
This is the order we will go in. I will cover the problem, our objectives and the approach.
Pasham will take the dataset and the data quality checks. Rohith will cover the analysis and
the preprocessing. Prisha will cover the data split and the testing. Then Pasham returns for
scope and limitations, and I will close.
"""),

3: ("lead", 90, """
The problem we picked is onboarding, which is everything that happens between somebody
accepting a job and actually being productive.

A large amount of paperwork follows a new hire. Identity documents, a signed offer letter,
bank details, and depending on the role things like a safety certificate. Somebody in human
resources checks each one by hand.

At the same time the new joiner has questions that nobody has time to answer quickly. How
much leave do I get. When is my training. Who sets up my laptop.

Three groups are affected. The new hire, because a bad first fortnight shapes an opinion that
is hard to change later. The HR team, because the work is repetitive. And the company,
because replacing somebody who leaves in the first year costs an estimated six to nine months
of their salary.

The specific gap is this. Existing systems like BambooHR and Workday are checklists. They
record that a step happened. They do not read the document that was uploaded, they do not
answer the question that was asked, and they do not notice when somebody has quietly stopped
making progress. Those three things are what we are building.
"""),

4: ("lead", 60, """
We set five objectives. The first four are what this review covers.

Build the datasets and describe them properly. Preprocess the text and the numerical data
into a form a model can use, with a reason for every step. Analyse the data for
distributions, balance and quality problems before any modelling begins. Split it into
training and test sets without leakage, and then check that split rather than assume it.

The fifth objective, developing and evaluating the models themselves, is next phase work.

I want to be explicit that objectives one to four are complete and objective five has not
started. We are not presenting planned work as finished work.
"""),

5: ("lead", 75, """
Our approach follows six steps and we have completed the first four.

Data collection and generation, then data understanding and exploratory analysis, then
preprocessing, then the train and test split. Model implementation and evaluation are steps
five and six and they come next term.

The important design decision is on the left. The system has to solve three different
prediction problems and each needs a different kind of data, so we built three datasets
rather than one. Document text for verifying uploads. Message text for understanding what a
new joiner is asking. And numerical records for predicting who is falling behind.

Tools are on the right. Everything is Python with scikit-learn and NumPy. We deliberately
avoided anything that needs a GPU or a paid service, because the whole thing had to run on a
laptop.

Pasham will now take you through the datasets themselves.
"""),

6: ("qa", 90, """
Thank you. I will cover what our three datasets contain and where they came from.

The table gives the shape of each one. Four thousand nine hundred and fifty documents across
nine classes. Three thousand three hundred and sixty messages carrying two labels each,
intent and sentiment. And six thousand simulated onboarding journeys with twelve numerical
features and a yes or no outcome.

Now the part we expect to be asked about. All three are generated. We did not use a public
dataset, and there are two separate reasons.

Onboarding documents are passports and bank mandates. They are personal records. We cannot
legally collect those from anybody, and there is no public collection of Indian employment
paperwork available.

The second reason is different. The records of who struggled during onboarding do not exist
for us at all, because our system has never been deployed. There is no history to learn from.

So we wrote generators. The important point is that we tried to make them produce a hard
problem rather than a flattering one, and Rohith will show you the figures that demonstrate
that.

The limitation is stated on the slide and we will state it again. Our numbers measure how
consistent a model is with our own generator. They do not measure performance on a real
passport. Replacing this with a real corpus is the first item in our future work.
"""),

7: ("qa", 90, """
This is the data quality side, which was my responsibility.

The table on the left is what we checked and what we found. Zero missing values in all three
datasets. Document and intent classes are perfectly balanced because we generated them that
way, which means plain accuracy will be a fair measure for those two problems. The target in
the journeys dataset is moderately imbalanced at about forty three per cent.

On the right is what we learned. The strongest single indicator of somebody stalling is the
sentiment of their messages, at about minus zero point four five. That is interesting because
it links two parts of our system together. The text analysis feeds the numerical prediction.

Now the finding at the bottom, in red. Our message dataset contains two hundred exact
duplicate records. Short messages like a plain thank you get generated identically by
different random draws.

That is a real defect and we found it ourselves. Prisha will show you what we did about it,
because what happened next is the part of this project I am most pleased with.

Rohith will take the analysis from here.
"""),

8: ("dev", 75, """
Thank you. I will cover the exploratory analysis, which we did before writing any model code.

Three charts here. On the left, the nine document classes each hold exactly five hundred and
fifty samples. That is balance by construction and it matters, because it means we can quote
plain accuracy without it being misleading.

Top right, the intents are also balanced, but sentiment is not. Negative messages outnumber
positive ones. That is deliberate rather than accidental. Escalation messages are rarely
cheerful and small talk is rarely furious, so forcing them to be equal would have made the
data less realistic, not more. We handle it with balanced class weights when we train.

Bottom left is the one I would draw your attention to. Twenty two per cent of our documents
are in the severe category. Those are cropped, the header is removed, ten to twenty per cent
of the characters are scrambled, and sentences from a different document type are mixed in.

We deliberately made a fifth of our own data very difficult. The reason is on the next slide.
"""),

9: ("dev", 90, """
These two charts changed how we think about our data.

The correlation matrix on the left shows how our twelve features relate to each other. The
block in the top left corner is the finding. Stage, progress and percentage of tasks complete
correlate above zero point nine with each other, reaching zero point nine seven for the
strongest pair.

Those three are measuring almost the same thing. They are three different names for how far
along somebody is. This explained something that had been puzzling us, which is why removing
any one of them changed our results so little. Individually each looked useful. Between them
they carry one piece of information.

Also worth noting, no single feature correlates with the outcome above zero point four five.
We expected that, because our generator deliberately keeps part of the cause hidden from the
features. If any feature had shown a correlation near one, it would mean we had accidentally
leaked the answer into the inputs.

On the right, sentiment does separate the two outcomes in the direction you would expect.
People who stall write more negatively. But look at the overlap. The distributions sit on top
of each other for most of their range. So sentiment contributes to a prediction, it does not
decide one. That is a more realistic expectation than the one we started with.
"""),

10: ("dev", 90, """
This is the preprocessing, with a reason for each step rather than just a list.

The text goes through two different conversions at once. The first counts whole words and
weights them by how rare they are, so a word like the counts for nothing and a word like
passport counts for a lot. The second counts short runs of three to five letters.

That second one is the choice I would defend. When a scan is damaged, a whole word becomes
unrecognisable, so the word based method fails. But most of the short letter sequences inside
that word survive. So when one representation breaks down, the other still works. That is why
our badly damaged documents still score around ninety four per cent instead of collapsing.

The numerical data gets rescaled so every column sits on the same footing. Otherwise the
column holding a number of days would outweigh a column holding a score between minus one and
one, purely because its numbers are bigger.

Now the box at the bottom, which I think matters more than the table. Two steps that appear
in almost every preprocessing description are missing here, and I want to say why rather than
leave them out quietly.

We did not fill in missing values, because there are none. We checked every column and every
record and the count is zero. That is a consequence of generating our data rather than
collecting it, and it is one of the ways our dataset is easier than a real one.

We did not remove outliers either, although the standard rule flags a large number of them.
The features producing outliers are counts and waiting times. An employee who has been
inactive for twenty five days is exactly the case our system is supposed to catch. Deleting
that row would remove the problem we are trying to detect.
"""),

11: ("dev", 60, """
This is the before and after, with our actual numbers rather than a generic example.

The top table is the text. Four thousand nine hundred and fifty pieces of raw text become a
mathematical table of four thousand nine hundred and fifty rows by eleven thousand four
hundred and eighty two columns. We started with about forty two thousand possible features
and pruned it down to eleven and a half thousand by removing anything that appears in only
one document. A term appearing once cannot generalise, it can only memorise.

The result is over ninety nine per cent empty, which is normal and expected for text.

The bottom table is the numerical data. Every one of the twelve columns goes from its own
natural range to a mean of zero and a standard deviation of one. The reason that matters is
on the last line. Once everything is on the same scale, the model's internal weights become
directly comparable, which is what will let us say which factors actually drive a prediction.

Prisha will now take the data split and the testing.
"""),

12: ("tester", 120, """
Thank you. This slide is mine and it is the one I would most like you to look at.

The table at the top is the split. Seventy five per cent for training, twenty five per cent
held back for testing, stratified so class proportions stay the same in both halves, with a
fixed random seed so anybody can reproduce it exactly.

Why split at all. Because a model tested on data it already studied reports how well it
memorised, not how well it learned. It is the difference between an exam and a practice paper
you have already seen the answers to.

Our leakage controls are in the middle. The transformations are fitted inside a pipeline
object, which means during cross validation they are refitted on each training portion alone
and never see the held back data.

Now the red section, which is the real content of this slide.

We audited the split rather than assuming it was clean, and we found a defect. Seventy
messages appear in both halves. That is eight point three per cent of that test set. Short
messages repeat, and a random split cannot separate identical text.

My assumption was that this was inflating our scores, because the model would be tested
partly on text it had memorised. That is the textbook expectation.

So we measured it instead of assuming. We trained once, then scored the held back data in two
parts: the rows that also appear in training, and the rows that do not.

The result contradicted me. Accuracy on the leaked rows was zero point nine eight six eight.
On the clean rows it was zero point nine nine seven four. The model did worse on the rows it
had already seen.

The explanation, once we worked it out, is that the messages which get duplicated are the
short ambiguous ones like thank you. Those are the hardest to classify in the first place. So
the duplication is concentrated in the difficult cases and drags that score down rather than
lifting it.

The defect is still real and still needs fixing. But our explanation for it was wrong, and we
wrote that down rather than deleting the evidence.
"""),

13: ("tester", 90, """
This is the testing. Since no models exist yet, everything here tests the data and the code
that prepares it.

Thirty four test cases, which expand to fifty five individual checks because several run
against multiple inputs. All currently passing, and the whole suite runs in about twenty
seconds with no internet connection.

The categories are on the left. Seven cases validate the data itself. Three check the
preprocessing produced what we claim. Four check the split. Four check the document pipeline
against prepared files. Then boundary cases like a zero byte file and a file one byte over
the size limit, and exceptional cases like an HTML file renamed to look like a PDF, and an
attempt to use a file path to escape the storage folder.

Two decisions about how I wrote these are on the right.

First, no test calls the language model. Our assistant phrases its answer differently every
time, so a test comparing text would fail for reasons unrelated to the change being tested,
and the team would learn to ignore it. I test the parts that are deterministic instead.

Second, and this is the unusual one, two of my tests assert that a defect is present rather
than absent. They confirm the duplicate problem exists and set an upper limit on it. If the
problem grows, the test fails. If somebody fixes it without telling anyone, the test also
fails. A known defect with no test around it can expand without anybody noticing.

At the bottom is what I do not cover, and I would rather say it than let it be assumed. No
tests at the API level, no authentication tests because there is no authentication, and no
frontend tests.

Pasham will take the scope and the limitations.
"""),

14: ("qa", 80, """
Thank you. I will cover where this goes next and what we know is wrong with it.

On the left is what is complete. Problem definition, three datasets built and characterised,
ten figures with written observations, preprocessing with before and after evidence, the
split with its audit, and fifty five automated checks.

On the right, the next phase in order. Data preparation, then implementing the algorithms,
training, testing, evaluation, and comparison between models.

We have planned which algorithms to compare. A linear support vector classifier against
logistic regression for the documents. Logistic regression as a baseline for intent and
sentiment. And logistic regression against gradient boosting for the risk prediction, because
the relationship there may not be linear.

For evaluation we will report accuracy and macro F1 for the classification problems, and for
the risk model we will report ROC AUC together with a calibration check. That second one
matters because a probability used to rank people needs to be meaningful, not just in the
right order.

Now the limitations, in red, which is my responsibility to present honestly.

Our data is synthetic, so every figure we will produce describes consistency with our own
generators. Our message dataset has the duplication problem Prisha described. Three of our
features are redundant. And our generated documents average under four hundred characters,
which is far shorter than a real certificate, so the task we are solving is easier than the
real one.

The note at the bottom repeats what Kritika said at the start. We are presenting no accuracy
figures today because the models are next phase work.
"""),

15: ("lead", 70, """
This is who did what.

Rohith wrote the data generators, the preprocessing pipelines, the splitting implementation
and the analysis code. Prisha wrote the thirty four test cases including the boundary and
exceptional inputs, and ran the leakage measurement. Pasham owned the data quality checks,
the preprocessing verification, the documentation and the defect register. I handled the
problem definition, the objectives, the scope and coordinating the four of us.

To conclude. We have three datasets totalling about fourteen thousand examples, all built and
characterised.

Our key findings were these. Our classes are balanced by construction. Stalling correlates
most strongly with the sentiment of somebody's messages. Three of our twelve features turned
out to be measuring the same thing. And we found a genuine duplication defect in our own
data, measured its effect, and discovered our explanation for it was wrong.

Current status is that data preparation and splitting are complete and verified. Model
implementation begins next phase.

If I had to point to one thing that represents how we worked, it would be that on three
separate occasions the data told us something we did not want to hear, and each time we wrote
it down rather than looking away.
"""),

16: ("lead", 20, """
These are our references, in IEEE format. Fourteen of the fifteen in our paper are from 2017
onwards, with the most recent from 2023.

Thank you. We are happy to take questions, and each of us can answer on our own area.
"""),

17: ("lead", 25, """
These remaining slides are not part of this review. They cover work from the next phase that
we have already prototyped.

We have kept them separate deliberately, because we did not want to present next phase work
as if it were part of this assessment. If you would like to see what we have built beyond the
scope of this review, we can go through them.
"""),

18: ("lead", 60, """
We have a working application end to end. A React front end, a FastAPI back end, two role
based views for the new hire and for HR, and the whole thing is organisation aware so two
companies see only their own data.

Document upload runs through automatic verification. Policy questions are answered with a
citation to the source document. Each employee gets a risk score with an explanation of what
is driving it.

On the right, six specialist assistants, each holding only the tools for its own area. The
policy assistant physically cannot complete a task, and the onboarding assistant cannot read
the policy documents. That restriction is enforced in code rather than by asking the model
nicely.

Routing between them uses our own trained classifier rather than a language model, which is
cheaper, repeatable, and something we can measure.

We can demonstrate any of this live if you would like.
"""),

19: ("dev", 60, """
These are the models we have already trained. I want to be clear that these belong to the
final review, not this one, and we are showing them only because we were asked.

Four models. Document type, intent, sentiment, and stall risk.

How we read our own numbers matters more than the numbers themselves.

The document classifier shows zero point nine eight six overall, but the figure I would quote
is zero point nine three seven, which is what it scores on the severely damaged scans. The
clean scans score a perfect one point zero, and that tells us almost nothing.

The sentiment figure of zero point nine nine six is not a capability claim and we do not
present it as one. It is high because our generator marks sentiment with stock phrases that a
simple model separates easily. That is a property of our data, not evidence the model
understands sentiment.

And every figure here is measured on synthetic data.
"""),

20: ("tester", 75, """
This slide is the one we would most like to be judged on.

Four things.

We rejected our own perfect scores three times. The first document classifier scored one
point zero on every metric with no variation. We treated that as a broken test rather than a
result, and rebuilt the data until the hardest category read zero point nine three seven.

We tested a hypothesis about our own data and were proved wrong. That is the leakage
measurement I described earlier.

We measured whether our components actually depend on each other. Removing the sentiment
feature costs the risk model zero point zero zero seven five of its score. That is evidence
of integration rather than a claim of it.

And we keep a register of our own defects, with two automated tests that assert the known
problems still exist so they cannot quietly grow.
"""),

21: ("lead", 40, """
Finally, everything here can be demonstrated live.

On the left, the data work from this review. Four commands regenerate the dataset report, all
ten figures, the full test suite, and the test report with real results.

On the right, the system itself if you want to see it. We can upload an expired safety
certificate and watch it get rejected automatically with the expiry date quoted back. We can
ask the same leave question as two employees from different companies and get twenty four
days and eighteen days, each cited to the correct policy document.

Everything runs offline on a laptop. There is no paid service anywhere in the project.
"""),
}


def role_slides(role):
    return sorted(n for n, (r, _, _) in SCRIPTS.items() if r == role)


def build_role_deck(role, slide_numbers, always_keep=(1,)):
    from pptx import Presentation

    prs = Presentation(str(FULL))
    keep = set(slide_numbers) | set(always_keep)

    xml_slides = prs.slides._sldIdLst
    rel_key = ("{http://schemas.openxmlformats.org/officeDocument/2006/"
               "relationships}id")

    for index, sld in reversed(list(enumerate(list(xml_slides), start=1))):
        if index not in keep:
            prs.part.drop_rel(sld.get(rel_key))
            xml_slides.remove(sld)

    # Attach the script for each surviving slide as speaker notes.
    remaining = sorted(keep)
    for position, original in enumerate(remaining):
        if original not in SCRIPTS:
            continue
        who, seconds, text = SCRIPTS[original]
        name, roll, title = TEAM[who]
        notes = (f"[{name}, {title}]  about {seconds} seconds\n"
                 f"(slide {original} of the full deck)\n"
                 + text.strip())
        prs.slides[position].notes_slide.notes_text_frame.text = notes

    OUT.mkdir(parents=True, exist_ok=True)
    name, roll, title = TEAM[role]
    safe = name.replace(" ", "_")
    path = OUT / f"{position_prefix(role)}_{safe}_{title.replace(' ', '')}.pptx"
    prs.save(str(path))
    return path, remaining


def position_prefix(role):
    return {"lead": "1", "qa": "2", "dev": "3", "tester": "4"}[role]


def build_script_markdown():
    lines = ["# Presentation Scripts", "",
             "One script per slide, grouped by presenter. Times are a guide rather than a",
             "target. The full run is about seventeen minutes for the sixteen assessed slides.",
             "", "The same text is in the speaker notes of each role deck.", ""]

    total = sum(s for n, (_, s, _) in SCRIPTS.items() if n <= 16)
    lines += [f"Assessed slides 1 to 16: about {total // 60} minutes {total % 60} seconds.",
              "Appendix slides 17 to 21 are only presented if asked.", "", "---", ""]

    order = ["lead", "qa", "dev", "tester"]
    for role in order:
        name, roll, title = TEAM[role]
        slides = role_slides(role)
        seconds = sum(SCRIPTS[n][1] for n in slides)
        lines += [f"# {name} ({title})", "",
                  f"Roll number {roll}. Slides: "
                  + ", ".join(str(n) for n in slides)
                  + f". About {seconds // 60} minutes {seconds % 60} seconds in total.", ""]
        for n in slides:
            who, secs, text = SCRIPTS[n]
            lines += [f"## Slide {n}  ({secs} seconds)", ""]
            for para in text.strip().split("\n\n"):
                lines += [" ".join(para.split()), ""]
        lines += ["---", ""]

    return "\n".join(lines)


def main():
    if not FULL.exists():
        raise SystemExit("Full deck missing. Run docs/build_midterm_deck.py first.")

    OUT.mkdir(parents=True, exist_ok=True)

    print("Role decks:")
    for role in ("lead", "qa", "dev", "tester"):
        slides = role_slides(role)
        path, kept = build_role_deck(role, slides)
        name, _, title = TEAM[role]
        print(f"  {name:16s} {title:10s} slides {kept}  ->  {path.name}")

    md_path = ROOT / "docs" / "PRESENTATION_SCRIPTS.md"
    md_path.write_text(build_script_markdown(), encoding="utf-8")

    import md_to_pdf
    pdf = ROOT / "docs" / "pdf" / "Presentation_Scripts.pdf"
    md_to_pdf.convert(md_path, pdf, "OnboardAI Presentation Scripts")
    print(f"\nScripts: {md_path.name} and {pdf.name}")


if __name__ == "__main__":
    main()
