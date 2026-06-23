import re


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def generate_dataset_aliases(dataset_name: str) -> list[str]:
    aliases = set()

    if not dataset_name:
        return []

    aliases.add(dataset_name)

    # Hugging Face style: owner/dataset
    if "/" in dataset_name:
        owner, short_name = dataset_name.split("/", 1)

        aliases.add(short_name)
        aliases.add(short_name.replace("-", " "))
        aliases.add(short_name.replace("_", " "))
        aliases.add(short_name.upper())
        aliases.add(short_name.lower())

        # Sometimes owner is meaningful
        aliases.add(f"{owner} {short_name}")
        aliases.add(f"{owner}/{short_name}")

    # General variants
    aliases.add(dataset_name.replace("-", " "))
    aliases.add(dataset_name.replace("_", " "))
    aliases.add(dataset_name.replace("/", " "))
    aliases.add(re.sub(r"[^A-Za-z0-9]+", " ", dataset_name).strip())

    # Remove duplicate normalized aliases
    cleaned = []
    seen = set()

    for alias in aliases:
        alias = alias.strip()
        alias_norm = normalize_text(alias)

        if alias and alias_norm and alias_norm not in seen:
            cleaned.append(alias)
            seen.add(alias_norm)

    return cleaned