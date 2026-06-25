from collections import Counter

import streamlit as st


_SOURCE_ORDER = ["Hugging Face", "European Language Grid", "OpenML", "DataCite"]


def show_source_coverage_summary(result: dict) -> None:
    dataset_candidates = result.get("dataset_candidates", [])
    paper_evidence = result.get("paper_evidence", [])
    matched_results = result.get("matched_results", [])

    total_matched_evidence = sum(
        len(m.get("evidences", [])) for m in matched_results
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dataset Candidates", len(dataset_candidates))
    c2.metric("Paper Evidence Sentences", len(paper_evidence))
    c3.metric("Dataset-Paper Matches", len(matched_results))
    c4.metric("Matched Evidence Sentences", total_matched_evidence)

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.caption("**Dataset candidates by source**")
        counts = Counter(c.get("source", "Unknown") for c in dataset_candidates)
        source_cols = st.columns(len(_SOURCE_ORDER))
        for i, source in enumerate(_SOURCE_ORDER):
            source_cols[i].metric(source, counts.get(source, 0))

    with col_right:
        st.caption("**Paper evidence by source type**")
        type_counts = Counter(
            e.get("source_text_type", "unknown") for e in paper_evidence
        )
        type_labels = sorted(type_counts)
        if type_labels:
            type_cols = st.columns(len(type_labels))
            for i, label in enumerate(type_labels):
                type_cols[i].metric(label, type_counts[label])
        else:
            st.info("No evidence found.")
