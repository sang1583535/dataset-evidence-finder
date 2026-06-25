import os

GROBID_URL = os.getenv("GROBID_URL", "http://localhost:8070")

SUPPORTED_DOMAIN = "NLP / Computational Linguistics"

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