import os

GROBID_URL = os.getenv("GROBID_URL", "http://localhost:8070")

SUPPORTED_DOMAIN = "NLP / Computational Linguistics"

# Second-pass dataset search limits (kept in config, not user-facing).
MAX_SECOND_PASS_DATASET_QUERIES = int(
    os.getenv("MAX_SECOND_PASS_DATASET_QUERIES", "3")
)
MAX_SECOND_PASS_RESULTS_PER_SOURCE = int(
    os.getenv("MAX_SECOND_PASS_RESULTS_PER_SOURCE", "2")
)

NLP_CL_KEYWORDS = [
    "nlp",
    "natural language processing",
    "computational linguistics",
    "language model",
    "text classification",
    "sentiment analysis",
    "machine translation",
    "question answering",
    "summarization",
    "named entity recognition",
    "information extraction",
    "speech",
    "corpus",
    "corpora",
    "treebank",
    "lexicon",
    "parallel corpus",
    "multilingual",
]

EVIDENCE_TERMS = [
    "dataset",
    "benchmark",
    "corpus",
    "corpora",
    "evaluation set",
    "test set",
    "training set",
    "we evaluate",
    "we use",
    "we used",
    "trained on",
    "experiments on",
]