import re

from app.services.alias_generator import normalize_text


_GENERIC_TASK_PHRASES: set[str] = {
    "machine translation",
    "neural machine translation",
    "natural language generation",
    "text classification",
    "sentiment analysis",
    "question answering",
    "named entity recognition",
    "summarization",
    "speech recognition",
    "automatic speech recognition",
    "language modeling",
    "information retrieval",
}

_GENERIC_TOKENS: set[str] = {
    "machine", "translation", "nlg", "nlp", "natural", "language", "generation",
    "classification", "sentiment", "analysis", "question", "answering",
    "summarization", "speech", "recognition", "dataset", "corpus", "benchmark",
    "text", "data", "neural", "information", "retrieval", "modeling",
}

_STRONG_USAGE_PHRASES: list[str] = [
    "we use", "we used",
    "we evaluate", "we evaluated",
    "we train", "we trained",
    "trained on", "evaluated on",
    "experiments on", "evaluation on",
    "we conduct experiments on", "we experiment on",
]

_DATASET_CONTEXT_TERMS: set[str] = {
    "dataset", "datasets", "benchmark", "benchmarks",
    "corpus", "corpora", "training set", "test set", "evaluation set",
}

_GENERIC_BACKGROUND_PHRASES: list[str] = [
    "a given corpus", "a parallel corpus", "parallel corpus",
    "large corpus", "training corpus", "given parallel corpus",
]


def is_generic_alias(alias: str) -> bool:
    norm = normalize_text(alias)
    if norm in _GENERIC_TASK_PHRASES:
        return True
    tokens = [t for t in norm.split() if t]
    if not tokens:
        return True
    generic_count = sum(1 for t in tokens if t in _GENERIC_TOKENS)
    return generic_count / len(tokens) >= 0.6


def is_dataset_like_alias(alias: str) -> bool:
    if is_generic_alias(alias):
        return False
    norm = normalize_text(alias)
    if not norm or len(norm) < 3:
        return False
    # Has digits (e.g. FLORES-200, CoNLL-2003, SST-2)
    if re.search(r"\d", alias):
        return True
    # Uppercase acronym-style with at least 3 chars (e.g. XNLI, VIVOS, MAP-CC)
    if re.match(r"^[A-Z][A-Z0-9\-_]{2,}$", alias.strip()):
        return True
    # Hyphenated, at most 4 normalized tokens (e.g. nlg-bench with non-generic parts)
    tokens = norm.split()
    if "-" in alias and len(tokens) <= 4:
        return True
    # Single non-generic word
    if len(tokens) == 1 and tokens[0] not in _GENERIC_TOKENS and len(tokens[0]) >= 4:
        return True
    # Multi-word with at least 2 non-generic tokens
    non_generic = [t for t in tokens if t not in _GENERIC_TOKENS]
    if len(non_generic) >= 2:
        return True
    if len(non_generic) == 1 and len(tokens) <= 3:
        return True
    return False


def allow_fuzzy_for_alias(alias: str) -> bool:
    if not is_dataset_like_alias(alias):
        return False
    # Has digits (e.g. FLORES-200, CoNLL-2003)
    if re.search(r"\d", alias):
        return True
    # Pure uppercase acronym >= 4 chars (e.g. XNLI, VIVOS)
    if re.match(r"^[A-Z][A-Z0-9]{3,}$", alias.strip()):
        return True
    # Hyphenated short name (e.g. MAP-CC)
    norm_tokens = normalize_text(alias).split()
    if "-" in alias and len(norm_tokens) <= 4:
        return True
    return False


def has_strong_usage_phrase(sentence: str) -> bool:
    lower = sentence.lower()
    return any(phrase in lower for phrase in _STRONG_USAGE_PHRASES)


def has_dataset_usage_context(sentence: str) -> bool:
    lower = sentence.lower()
    for phrase in _GENERIC_BACKGROUND_PHRASES:
        if phrase in lower:
            return False
    has_strong = any(phrase in lower for phrase in _STRONG_USAGE_PHRASES)
    has_context = any(term in lower for term in _DATASET_CONTEXT_TERMS)
    return has_strong or has_context


def is_valid_dataset_evidence(sentence: str, alias: str, match_type: str) -> bool:
    if match_type == "exact_alias_match":
        return has_dataset_usage_context(sentence)
    if match_type == "fuzzy_alias_match":
        return is_dataset_like_alias(alias) and has_strong_usage_phrase(sentence)
    return False
