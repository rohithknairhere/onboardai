"""Generate the IEEE paper in .docx and LaTeX.

    backend/venv/Scripts/python.exe docs/build_paper.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs"))

from docgen import render_docx, render_latex

R = json.loads((ROOT / "backend" / "ml" / "artifacts" / "data_report.json")
               .read_text(encoding="utf-8"))
D, M, K = R["documents"], R["messages"], R["risk"]
LI = M.get("leakage_impact_sentiment", {})

AUTHORS = [
    {"name": "Kritika Sah", "roll": "DL.AI.U4AID25031", "role": "Team Lead"},
    {"name": "Prisha Saini", "roll": "DL.AI.U4AID25039", "role": "Tester"},
    {"name": "Rohith K Nair", "roll": "DL.AI.U4AID25043", "role": "Developer"},
    {"name": "Pasham Srikar", "roll": "DL.AI.U4AID25049", "role": "QA"},
]

top_corr = list(K["correlation_with_target"].items())[:4]
pair = K["top_correlated_pairs"][0]
tier = D["difficulty_tiers"]

PAPER = {
    "title": "OnboardAI: Data Preparation and Analysis for an AI Assisted "
             "Employee Onboarding System",
    "authors": AUTHORS,
    "dept": "Department of Artificial Intelligence and Data Science",
    "org": "Amrita Vishwa Vidyapeetham, Delhi NCR, Faridabad",
    "affiliation": "Department of Artificial Intelligence and Data Science, "
                   "Amrita Vishwa Vidyapeetham, Delhi NCR, Faridabad. "
                   "Course: Introduction to AI and Machine Learning. "
                   "Subject Coordinator: Dr. Sakshi Ahuja",
    "sections": [
        {"heading": "Introduction", "paras": [
            "Hiring a new employee creates a large amount of administrative work that nobody "
            "enjoys doing. Identity documents have to be checked, certificates have to be "
            "confirmed as valid and in date, bank details have to be recorded, accounts have "
            "to be created, and training sessions have to be booked. In most organisations a "
            "person in the human resources team does all of this by hand, one new joiner at a "
            "time.",

            "The cost of this is not only staff time. A new joiner who is waiting for answers "
            "forms an early opinion of the company, and that opinion is difficult to change "
            "later. Industry estimates place the cost of replacing an employee who leaves "
            "within the first year at several months of their salary, so a poor first few weeks "
            "is an expensive problem rather than a minor inconvenience.",

            "Existing human resource management systems such as BambooHR and Workday handle "
            "this as a checklist. They record whether a step is complete, but they do not read "
            "the document that was uploaded, they do not answer the question the new joiner "
            "actually asked, and they do not notice when somebody has quietly stopped making "
            "progress. Those three gaps are what our project addresses.",

            "This paper describes the work we completed in the first half of the project. "
            "Following the scope set for the mid term review, we cover the problem definition, "
            "the construction and analysis of our datasets, the preprocessing we applied, the "
            "train and test split, and the validation work carried out so far. Machine learning "
            "model implementation, training and performance evaluation belong to the next phase "
            "and are deliberately not reported here.",

            "Our contributions at this stage are the following. We built three datasets covering "
            "the three different prediction problems the system needs to solve. We characterised "
            "each dataset statistically and visually before writing any model code. We applied "
            "and justified a preprocessing pipeline for both text and tabular data. We split the "
            "data in a way that avoids leakage and then audited that split rather than assuming "
            "it was correct. Finally, we wrote an automated validation suite of 34 test cases "
            "that runs against the data and the processing code."],
         },

        {"heading": "Related Work", "paras": [
            "Four groups of existing work are relevant, because the project touches document "
            "understanding, text classification, retrieval and tabular prediction.",

            "Document understanding has moved decisively towards multimodal pre-training since "
            "2020. LayoutLM [4] was the first widely used model to learn text and layout "
            "jointly, and LayoutLMv3 [1] extended this with unified text and image masking. DiT "
            "[3] applies self-supervised pre-training directly to document images, and Donut [2] "
            "removes the OCR stage entirely by reading the image end to end. All four report "
            "strong results on document classification benchmarks, and all four require GPU "
            "pre-training on large labelled corpora, which was not available for this project.",

            "Text classification is dominated by transformer encoders. BERT [5] established the "
            "pre-train and fine-tune pattern, and Sentence-BERT [6] adapted it to produce "
            "sentence embeddings suitable for semantic similarity. These would be the natural "
            "upgrade path for the intent and sentiment components.",

            "Retrieval augmented generation [7] grounds a language model in retrieved passages "
            "rather than relying on parametric memory. The recent survey by Gao et al. [8] "
            "identifies corpus quality and retrieval precision as the dominant factors in "
            "practical systems, which matches what was observed here.",

            "Reproducibility work is directly relevant to the split audit reported in section "
            "VII. Kapoor and Narayanan [9] surveyed machine learning based science across "
            "seventeen fields and found data leakage to be a recurring and frequently unnoticed "
            "cause of over optimistic results. Their taxonomy was used to decide what to check "
            "for in this project."],
         "table": {
             "caption": "Existing systems and methods reviewed",
             "header": ["System or paper", "Method used", "Limitation for this problem"],
             "widths": [0.26, 0.3, 0.34],
             "rows": [
                 ["BambooHR, Workday and similar HRMS platforms",
                  "Rule based workflow and status tracking",
                  "Record that a step happened but never inspect the uploaded document or "
                  "predict a problem"],
                 ["Huang et al. [1], LayoutLMv3",
                  "Multimodal pre-training over text, layout and image",
                  "Needs GPU pre-training and a large labelled corpus"],
                 ["Kim et al. [2], Donut",
                  "OCR free encoder decoder read directly from the image",
                  "No intermediate text to inspect, so a rejection cannot be explained to the "
                  "employee"],
                 ["Li et al. [3], DiT",
                  "Self-supervised pre-training on document images",
                  "Same compute and corpus constraints"],
                 ["Devlin et al. [5], BERT",
                  "Transformer pre-training for text classification",
                  "Heavier than required for nine short document classes at this stage"],
                 ["Lewis et al. [7] and Gao et al. [8]",
                  "Retrieve passages and condition generation on them",
                  "Assumes a curated corpus already exists, which is rarely true in a small "
                  "company"],
                 ["Kapoor and Narayanan [9]",
                  "Audit of leakage across machine learning based science",
                  "Diagnoses the problem and motivates the audit, but provides no tooling"],
             ]},
         },
        {"paras": [
            "The gap identified is that no single system reads the onboarding document, answers "
            "the policy question from the company's own records, and predicts who is falling "
            "behind. Each of these has been studied separately. This project treats them as one "
            "problem with three data streams.",

            "The approach taken here is deliberately lighter than the document AI literature. "
            "Classical term weighting with a latent semantic projection was chosen over a "
            "pre-trained transformer because the entire system had to run offline on a laptop "
            "with no model download, which is a constraint the cited work does not face."],
         },

        {"heading": "Proposed Methodology", "paras": [
            "The system has to solve three different prediction problems, and each one needs a "
            "different kind of data. We therefore built three datasets rather than one.",

            "The first stream is document text. When a new joiner uploads a file, the system "
            "needs to decide what kind of document it is, pull out the dates and identifiers, "
            "and decide whether it satisfies the requirement. The second stream is message text. "
            "When a new joiner asks a question, the system needs to work out what they want and "
            "how they feel about it. The third stream is tabular. For each new joiner the system "
            "tracks progress indicators over time and uses them to estimate the chance that the "
            "onboarding will stall.",

            "The analytical stack is scikit-learn [15] over NumPy [14], chosen because the whole "
            "pipeline had to run offline on a laptop with no GPU and no model download.",

            "Our working method for this phase followed six steps, of which the first four are "
            "complete."],
         "numbered": [
             "Data collection and generation for all three streams.",
             "Data understanding, including distributions, class balance and quality checks.",
             "Preprocessing, covering text vectorisation and feature scaling.",
             "Splitting into training and test sets, followed by a leakage audit.",
             "Machine learning model implementation and training, which is next phase work.",
             "Evaluation and model comparison, which is also next phase work.",
         ]},

        {"heading": "Dataset Description", "paras": [
            "Table II summarises the three datasets. All three were produced by generators we "
            "wrote ourselves, for reasons explained below."],
         "table": {
             "caption": "Table II. Summary of the three datasets",
             "header": ["Dataset", "Samples", "Features", "Target", "Classes", "Data type"],
             "widths": [0.2, 0.11, 0.17, 0.17, 0.09, 0.16],
             "rows": [
                 ["Onboarding documents", f"{D['samples']:,}", "Text, vectorised",
                  "Document type", str(len(D["classes"])), "Unstructured text"],
                 ["Employee messages", f"{M['samples']:,}", "Text, vectorised",
                  "Intent and sentiment", f"{len(M['classes'])} and 3", "Unstructured text"],
                 ["Onboarding journeys", f"{K['samples']:,}", f"{K['features']} numeric",
                  "Stalled, binary", "2", "Structured tabular"],
             ]},
         },
        {"heading": "Why the data is synthetic", "level": 2, "paras": [
            "We considered using a public dataset and decided against it for the document and "
            "journey streams, for two separate reasons.",

            "Onboarding documents are passports, bank mandates and professional certificates. "
            "These are personal records containing identity and financial information. We could "
            "not lawfully collect real examples from classmates or from a company, and no "
            "suitable corpus of Indian onboarding paperwork is publicly available. Onboarding "
            "outcomes are a different problem. Our system has not been deployed anywhere, so "
            "there is no history of who completed onboarding and who stalled. The label simply "
            "does not exist yet.",

            "Because of this we wrote generators, and we tried to make them produce a hard "
            "problem rather than a flattering one. Nikolenko [13] surveys synthetic data in "
            "machine learning and notes that its value depends almost entirely on whether the "
            "generator reproduces the difficulty of the real task rather than only its surface "
            "form, which is the standard we tried to work to. The document generator applies "
            "three levels "
            "of degradation to simulate scan quality, producing "
            f"{tier.get('clean', 0):,} clean documents, {tier.get('degraded', 0):,} degraded "
            f"ones and {tier.get('severe', 0):,} severely damaged ones. The severe tier crops "
            "the page, removes the header, injects character level noise of between ten and "
            "twenty per cent, and bleeds in sentences belonging to other document types. The "
            "message generator includes deliberately uninformative messages such as a bare "
            "request for an update, where the correct label genuinely cannot be recovered from "
            "the text. The journey generator models three hidden traits, which we called "
            "engagement, friction and support, and derives the observable features as noisy "
            "measurements of those traits. It also includes a component in the outcome that no "
            "feature observes, so a perfect prediction is impossible by design.",

            "We state the limitation plainly. Any figure we report measures how consistent a "
            "model is with our generator, not how well it would perform on real paperwork. "
            "Replacing the document corpus with a real one is the first item in our future work.",

            "Section IV follows the structure recommended by Gebru et al. [12] for dataset "
            "documentation, covering composition, collection process and intended use, so that "
            "a reader can judge whether the data supports the claims made from it."],
         },

        {"heading": "Data Preprocessing", "paras": [
            "Text and tabular data needed different treatment, so we describe them separately. "
            "Table III lists each step with the reason for it and the result."],
         "table": {
             "caption": "Table III. Preprocessing steps applied",
             "header": ["Step", "Reason", "Result"],
             "widths": [0.25, 0.37, 0.28],
             "rows": [
                 ["Lowercasing and accent stripping",
                  "Scanned and typed text is inconsistent in case",
                  "Applied to all text data"],
                 ["Word level TF-IDF, one and two grams",
                  "Captures the vocabulary and short phrases that identify a document type",
                  f"{D['tfidf']['word_ngram_features_min_df_2']:,} features"],
                 ["Character level TF-IDF, three to five grams",
                  "Survives scan damage that destroys whole words",
                  "Combined with the word features"],
                 ["Sublinear term frequency",
                  "Stops a word repeated many times in one document from dominating",
                  "Applied"],
                 ["Minimum document frequency of two",
                  "A term that appears once cannot generalise to new documents",
                  f"{D['tfidf']['features_pruned_away']:,} features removed"],
                 ["Standard scaling of numeric features",
                  "The twelve features use different units and ranges",
                  "All features reduced to mean zero and unit variance"],
                 ["Scaler fitted inside a pipeline",
                  "Prevents statistics from the test fold reaching the training step",
                  "Enforced by the library"],
             ]},
         },
        {"paras": [
            "Two steps that appear in most preprocessing descriptions were not performed, and "
            "we think it is more useful to say why than to leave them out silently.",

            "We did not impute missing values because there are none. We checked every column "
            "of the tabular data and every record of both text corpora, and the count is zero in "
            "all three datasets. This is a consequence of generating the data rather than "
            "collecting it, and it is one of the ways our datasets are easier than real ones.",

            "We did not remove outliers either, although the interquartile range rule identifies "
            f"{sum(v['outliers_iqr'] for v in K['per_feature'].values()):,} of them. The features "
            "that produce outliers are counts and waiting times, and their long right tail is "
            "exactly the signal we care about. An employee who has been inactive for twenty five "
            "days is the case the system is supposed to catch, so discarding that row would "
            "remove the problem we are trying to detect.",

            "Table IV shows the effect of vectorisation on the document corpus."],
         "table": {
             "caption": "Table IV. Document corpus before and after vectorisation",
             "header": ["Measure", "Before", "After"],
             "widths": [0.22, 0.3, 0.38],
             "rows": [
                 ["Representation", f"{D['samples']:,} raw text strings",
                  f"Sparse matrix of {D['tfidf']['matrix_shape'][0]:,} by "
                  f"{D['tfidf']['matrix_shape'][1]:,}"],
                 ["Vocabulary", f"{D['tfidf']['raw_unique_tokens']:,} unique tokens",
                  f"{D['tfidf']['word_ngram_features_min_df_2']:,} weighted n-gram features"],
                 ["Feature count before pruning",
                  f"{D['tfidf']['word_ngram_features_min_df_1']:,}",
                  f"{D['tfidf']['word_ngram_features_min_df_2']:,} after pruning"],
                 ["Density", "Dense text",
                  f"{D['tfidf']['sparsity_pct']:.2f} per cent sparse, about "
                  f"{D['tfidf']['nonzero_per_doc_mean']:.0f} non zero values per document"],
             ]},
         },

        {"heading": "Exploratory Data Analysis", "paras": [
            "We produced ten figures before writing any model code. Four of the findings changed "
            "how we think about the data, and those are the ones we report here.",

            "The document and intent classes are balanced by construction. Every document class "
            f"holds exactly {list(D['class_counts'].values())[0]:,} samples and every intent "
            f"holds {list(M['class_counts'].values())[0]:,}. This means plain accuracy is a fair "
            "headline measure for those two problems. Sentiment is not balanced, because "
            "escalation messages are rarely cheerful and small talk is rarely angry, so we use a "
            "balanced class weight when that classifier is trained.",

            "The correlation matrix of the journey features produced the most useful finding. "
            f"The features {pair[0]} and {pair[1]} correlate at {pair[2]:.2f}, and three "
            "progress related features are mutually correlated above 0.9. They are measuring "
            "almost the same thing. This matters because it explains why removing any single one "
            "of them has very little effect on an overall score, even though each is individually "
            "informative.",

            "No single feature correlates with the target above " +
            f"{abs(top_corr[0][1]):.2f}. The strongest are " +
            ", ".join(f"{f} at {v:+.2f}" for f, v in top_corr[:3]) +
            ". We expected this, because the generator keeps part of the cause hidden from the "
            "features on purpose.",

            "Sentiment separates the two outcomes in the direction we expected but with "
            "considerable overlap. The median sentiment of a journey that completes is higher "
            "than one that stalls, but the distributions sit on top of each other for most of "
            "their range. This tells us sentiment is a contributing signal and not a decisive "
            "one, which is a more realistic expectation than we started with."],
         },

        {"heading": "Data Splitting and Leakage Audit", "paras": [
            "We split every dataset into 75 per cent training data and 25 per cent test data, "
            "using stratified sampling and a fixed random seed of 42. Stratification keeps the "
            "proportion of each class the same in both folds, which matters because our smallest "
            "class would otherwise be at risk of being underrepresented in the test fold by "
            "chance.",

            "Splitting before modelling is necessary because a model evaluated on data it has "
            "already seen reports how well it memorised, not how well it generalises. The risk "
            "we were most concerned about is leakage, where information from the test fold "
            "reaches the training process indirectly. Kapoor and Narayanan [9] found this to be "
            "the most common cause of irreproducible results across the seventeen fields they "
            "surveyed, and frequently one the original authors had not noticed, which is why we "
            "treated it as something to measure rather than assume. We control this by fitting "
            "the vectoriser "
            "and the scaler inside a pipeline object rather than fitting them on the full dataset "
            "first. During cross validation the pipeline refits those transformers on each "
            "training fold alone, so the test fold is never used to compute a vocabulary or a "
            "mean.",

            "We then audited the split rather than assuming it was clean, and found a defect. "
            f"The document corpus is clean, with zero records appearing in both folds. The "
            f"message corpus is not. It contains {M['duplicates_exact']:,} exact duplicate "
            f"messages, and {M['split']['overlap_documents']} of them appear in both the "
            f"training and the test fold, which is "
            f"{100 * M['split']['overlap_documents'] / M['split']['test_size']:.1f} per cent of "
            "that test set. Short messages such as a plain thank you are produced identically by "
            "different random draws, and a stratified random split has no way to separate them.",

            "Our first assumption was that this leakage was inflating our scores, since the model "
            "would be tested partly on strings it had already memorised. We decided to measure "
            "that rather than assume it. We trained the sentiment classifier once and then scored "
            "the test set in two parts, the rows that also appear in training and the rows that "
            "do not.",

            "The result contradicted us. Accuracy on the leaked rows was "
            f"{LI.get('accuracy_on_leaked', 0):.4f} and accuracy on the clean rows was "
            f"{LI.get('accuracy_on_clean', 0):.4f}, so the model performs slightly worse on the "
            "rows it has seen before. The explanation is that the duplicated messages are the "
            "short ambiguous ones, which are both the most likely to be generated twice and the "
            "hardest to classify correctly. Duplication is concentrated in the difficult cases, "
            "so it pulls the leaked score down rather than pushing it up.",

            "The leakage is still a defect and we have recorded it as one. The correct fix is to "
            "remove duplicates before splitting, or to group identical strings so that they "
            "cannot fall on both sides. We have not applied that fix yet because we wanted the "
            "measurement on record first."],
         "table": {
             "caption": "Table V. Split configuration and audit results",
             "header": ["Dataset", "Split", "Train", "Test", "Class drift", "Overlap"],
             "widths": [0.2, 0.1, 0.12, 0.12, 0.17, 0.14],
             "rows": [
                 ["Documents", D["split"]["split_ratio"], f"{D['split']['train_size']:,}",
                  f"{D['split']['test_size']:,}",
                  f"{D['split']['max_class_proportion_drift']:.4f}",
                  f"{D['split']['overlap_documents']}"],
                 ["Messages", M["split"]["split_ratio"], f"{M['split']['train_size']:,}",
                  f"{M['split']['test_size']:,}",
                  f"{M['split']['max_class_proportion_drift']:.4f}",
                  f"{M['split']['overlap_documents']}"],
                 ["Journeys", K["split"]["split_ratio"], f"{K['split']['train_size']:,}",
                  f"{K['split']['test_size']:,}",
                  f"{abs(K['split']['train_positive_rate'] - K['split']['test_positive_rate']):.4f}",
                  "Not applicable"],
             ]},
         },

        {"heading": "Preliminary Validation and Testing", "paras": [
            "Since model implementation has not started, our testing at this stage is aimed at "
            "the data and the processing code. We wrote 34 test cases which expand to 55 "
            "individual checks through parameterisation, and all of them currently pass.",

            "We made two decisions about how the suite is written. First, no test calls a "
            "language model. A test whose result depends on generation temperature cannot be "
            "used to detect a regression, because it may fail for reasons unrelated to the "
            "change being tested. Second, all file handling tests write to a temporary directory, "
            "so running the suite never touches the development database or the stored documents.",

            "Two of the cases are unusual in that they assert a defect is present rather than "
            "absent. One asserts that duplicates exist in the message corpus and the other that "
            "the known fold overlap exists. Both have an upper bound, so they fail if the problem "
            "grows worse. We chose this over simply removing the assertions because a silent "
            "known defect is more dangerous than a documented one."],
         "table": {
             "caption": "Table VI. Test coverage by category",
             "header": ["Category", "Cases", "Example"],
             "widths": [0.2, 0.09, 0.56],
             "rows": [
                 ["Data validation", "7",
                  "Missing values, class balance, data types, feature domain ranges"],
                 ["Preprocessing", "3",
                  "Matrix shape and sparsity, pruning effect, scaler output"],
                 ["Split integrity", "4",
                  "Stratification, fold overlap, reproducibility with a fixed seed"],
                 ["Functional", "4",
                  "Each of seven prepared documents produces the expected outcome"],
                 ["Boundary", "3",
                  "Zero byte file, file one byte over the size limit, feature limits"],
                 ["Exceptional", "3",
                  "HTML disguised as a PDF, path traversal attempt, malformed identifier"],
                 ["Access control", "2",
                  "Retrieval across organisations and across departments"],
                 ["Regression", "2", "Two previously fixed extraction faults"],
                 ["Performance", "2",
                  "Analysis under five seconds, classification under 150 milliseconds"],
                 ["Security", "1", "Personal identifiers removed before text leaves the system"],
             ]},
         },

        {"heading": "Project Scope and Next Phase", "paras": [
            "The intended users of the system are new employees and the human resources staff "
            "who manage their onboarding. The system is organisation aware, so two companies "
            "using the same deployment see only their own data and their own policy documents.",

            "The next phase follows the standard sequence of model implementation, training, "
            "testing, evaluation and comparison. For the document type problem we plan to compare "
            "a linear support vector classifier against logistic regression, both over the "
            "combined word and character features already prepared. For intent and sentiment we "
            "plan logistic regression as a baseline. For the stall risk problem we plan to "
            "compare logistic regression against a gradient boosting classifier, since the "
            "relationship between the hidden traits and the outcome may not be linear.",

            "Evaluation will use accuracy and macro averaged F1 for the classification problems, "
            "and ROC AUC together with a calibration check for the risk problem, since a "
            "probability that is used to rank employees needs to be meaningful and not only "
            "correctly ordered. We will report five fold cross validation and ablation results "
            "rather than a single held out number.",

            "Because the risk score is applied to people, each prediction will be accompanied by "
            "a per feature attribution using the additive approach of Lundberg and Lee [10]. For "
            "a standardised linear model these attributions are exact rather than sampled. We "
            "also intend to publish a model card for each trained model in the form proposed by "
            "Mitchell et al. [11], recording intended use, training data and known limitations, "
            "since a score used in a human resources decision should not be distributable "
            "without that context.",

            "We are aware of four limitations and plan to address them in that order. The "
            "datasets are synthetic, and we would like to retrain the document classifier on a "
            "public corpus such as RVL-CDIP, on which the document models in [1] and [3] are "
            "benchmarked. The message corpus contains duplicates that should "
            "be removed before splitting. Three of the journey features are almost perfectly "
            "correlated and we should either combine them or drop two. Finally our generated "
            f"documents average only {D['char_len']['mean']:.0f} characters, which is far shorter "
            "than a real scanned certificate, so the document task we are solving is easier than "
            "the real one."],
         },
    ],
    "references": [
        "Y. Huang, T. Lv, L. Cui, Y. Lu, and F. Wei, \"LayoutLMv3: Pre-training for document AI "
        "with unified text and image masking,\" in Proc. 30th ACM Int. Conf. Multimedia, 2022, "
        "pp. 4083-4091.",

        "G. Kim, T. Hong, M. Yim, J. Nam, J. Park, J. Yim, W. Hwang, S. Yun, D. Han, and "
        "S. Park, \"OCR-free document understanding transformer,\" in Proc. European Conf. "
        "Computer Vision (ECCV), 2022, pp. 498-517.",

        "J. Li, Y. Xu, T. Lv, L. Cui, C. Zhang, and F. Wei, \"DiT: Self-supervised pre-training "
        "for document image transformer,\" in Proc. 30th ACM Int. Conf. Multimedia, 2022, "
        "pp. 3530-3539.",

        "Y. Xu, M. Li, L. Cui, S. Huang, F. Wei, and M. Zhou, \"LayoutLM: Pre-training of text "
        "and layout for document image understanding,\" in Proc. 26th ACM SIGKDD Int. Conf. "
        "Knowledge Discovery and Data Mining, 2020, pp. 1192-1200.",

        "J. Devlin, M. W. Chang, K. Lee, and K. Toutanova, \"BERT: Pre-training of deep "
        "bidirectional transformers for language understanding,\" in Proc. NAACL-HLT, 2019, "
        "pp. 4171-4186.",

        "N. Reimers and I. Gurevych, \"Sentence-BERT: Sentence embeddings using Siamese "
        "BERT-networks,\" in Proc. EMNLP-IJCNLP, 2019, pp. 3982-3992.",

        "P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Kuttler, "
        "M. Lewis, W. Yih, T. Rocktaschel, S. Riedel, and D. Kiela, \"Retrieval-augmented "
        "generation for knowledge-intensive NLP tasks,\" in Advances in Neural Information "
        "Processing Systems, vol. 33, 2020, pp. 9459-9474.",

        "Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, and H. Wang, "
        "\"Retrieval-augmented generation for large language models: A survey,\" "
        "arXiv:2312.10997, 2023.",

        "S. Kapoor and A. Narayanan, \"Leakage and the reproducibility crisis in "
        "machine-learning-based science,\" Patterns, vol. 4, no. 9, 2023.",

        "S. M. Lundberg and S. I. Lee, \"A unified approach to interpreting model predictions,\" "
        "in Advances in Neural Information Processing Systems, vol. 30, 2017, pp. 4765-4774.",

        "M. Mitchell, S. Wu, A. Zaldivar, P. Barnes, L. Vasserman, B. Hutchinson, E. Spitzer, "
        "I. D. Raji, and T. Gebru, \"Model cards for model reporting,\" in Proc. Conf. Fairness, "
        "Accountability, and Transparency, 2019, pp. 220-229.",

        "T. Gebru, J. Morgenstern, B. Vecchione, J. W. Vaughan, H. Wallach, H. Daume III, and "
        "K. Crawford, \"Datasheets for datasets,\" Communications of the ACM, vol. 64, no. 12, "
        "pp. 86-92, 2021.",

        "S. I. Nikolenko, Synthetic Data for Deep Learning. Cham, Switzerland: Springer, 2021.",

        "C. R. Harris, K. J. Millman, S. J. van der Walt, R. Gommers, P. Virtanen, "
        "D. Cournapeau, E. Wieser, J. Taylor, S. Berg, and N. J. Smith, \"Array programming "
        "with NumPy,\" Nature, vol. 585, pp. 357-362, 2020.",

        "F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, "
        "P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, "
        "M. Brucher, M. Perrot, and E. Duchesnay, \"Scikit-learn: Machine learning in Python,\" "
        "Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.",
    ],
}


TEMPLATE = Path(r"C:\Users\Rohith\Downloads\Final project paper template.docx")



def main():
    out_dir = ROOT / "docs" / "paper"
    out_docx = out_dir / "OnboardAI_MidTerm_Paper.docx"
    out_tex = out_dir / "OnboardAI_MidTerm_Paper.tex"

    # The Word version is rendered into the supplied IEEE template so it keeps
    # the official styles and the single, multi and two column section layout.
    import render_ieee
    try:
        render_ieee.render(PAPER, TEMPLATE, out_docx, ROOT / "docs" / "_build")
        print(f"Saved {out_docx} (built on the supplied IEEE template)")
    except Exception as exc:
        print(f"IEEE template render failed ({type(exc).__name__}: {exc})")
        print("Falling back to the plain renderer.")
        render_docx(PAPER, out_docx)

    render_latex(PAPER, out_tex, style="ieee")
    print(f"Saved {out_tex}")


if __name__ == "__main__":
    main()
