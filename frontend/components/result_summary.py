from collections import Counter

import streamlit as st


_SOURCE_ORDER = ["Hugging Face", "European Language Grid", "OpenML", "DataCite"]


def show_source_coverage_summary(result: dict) -> None:
    dataset_candidates = result.get("dataset_candidates", [])
    matched_results = result.get("matched_results", [])

    c1, c2 = st.columns(2)
    c1.metric("Dataset Candidates", len(dataset_candidates))
    c2.metric("Dataset-Paper Matches", len(matched_results))

    st.divider()

    st.caption("**Dataset candidates by source**")
    counts = Counter(c.get("source", "Unknown") for c in dataset_candidates)
    source_cols = st.columns(len(_SOURCE_ORDER))
    for i, source in enumerate(_SOURCE_ORDER):
        source_cols[i].metric(source, counts.get(source, 0))
