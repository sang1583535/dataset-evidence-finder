REFERENCE_CATALOGUES = [
    {
        "name": "ELRA Catalogue",
        "role": "Authoritative CL/NLP language-resource catalogue",
        "integration_status": "reference_only",
        "note": "Used as an important reference source for language resources. Full integration may depend on metadata access, licensing, and time constraints.",
        "url": "https://catalogue.elra.info/",
    },
    {
        "name": "LDC Catalog",
        "role": "Authoritative linguistic data catalogue",
        "integration_status": "reference_only",
        "note": "Useful for recognized speech, text, lexicon, and multilingual resources. Access often depends on licensing or membership.",
        "url": "https://catalog.ldc.upenn.edu/",
    },
    {
        "name": "DataCite",
        "role": "Optional DOI-based dataset metadata source",
        "integration_status": "optional_implemented_source",
        "note": "Can provide additional dataset titles, DOI links, descriptions, and subjects.",
        "url": "https://datacite.org/",
    },
]


def get_reference_catalogues():
    return REFERENCE_CATALOGUES