import streamlit as st

from api_client import search_datasets
from components.comparison_table import show_comparison_table
from components.result_cards import (
    show_dataset_candidates,
    show_dataset_grouped_matches,
    show_paper_evidence,
)
from components.result_summary import show_source_coverage_summary


st.set_page_config(
    page_title="Dataset Evidence Finder",
    page_icon="🔎",
    layout="wide",
)

st.title("Dataset Evidence Finder")
st.caption(
    "Find NLP/Computational Linguistics dataset candidates and evidence sentences from arXiv papers."
)

with st.sidebar:
    st.header("Search Settings")

    query = st.text_input(
        "Research topic",
        value="Vietnamese sentiment analysis",
    )

    max_datasets = st.slider(
        "Max datasets per source",
        min_value=1,
        max_value=30,
        value=10,
    )

    max_papers = st.slider(
        "Max arXiv papers",
        min_value=1,
        max_value=20,
        value=10,
    )

    use_full_text = st.checkbox(
        "Use arXiv PDF full text",
        value=True,
        help="If enabled, the backend downloads arXiv PDFs and extracts evidence from paper body text.",
    )

    st.subheader("Dataset Sources")
    st.caption("Hugging Face is always enabled.")

    use_elg = st.checkbox(
        "Use European Language Grid",
        value=True,
        help="Search EU-connected CL/NLP language resources from ELG.",
    )

    use_openml = st.checkbox(
        "Use OpenML",
        value=True,
        help="Search OpenML as a secondary source. Results are filtered for possible NLP/CL relevance.",
    )

    use_datacite = st.checkbox(
        "Use DataCite",
        value=False,
        help="Optional DOI-based dataset metadata source.",
    )

    search_button = st.button("Search", type="primary")

    st.divider()
    st.caption("Scope: NLP / Computational Linguistics only")


tab1, tab2, tab3 = st.tabs(
    [
        "Overview",
        "Dataset Candidates",
        "Paper Evidence",
    ]
)

if search_button:
    if not query.strip():
        st.error("Please enter a research topic.")
    else:
        with st.spinner("Searching dataset sources and extracting paper evidence..."):
            try:
                result = search_datasets(
                    query=query,
                    max_datasets=max_datasets,
                    max_papers=max_papers,
                    use_full_text=use_full_text,
                    use_datacite=use_datacite,
                    use_openml=use_openml,
                    use_elg=use_elg,
                )

                with tab1:
                    show_source_coverage_summary(result)
                    st.divider()
                    show_comparison_table(result["matched_results"])
                    st.caption(
                        "Results are grouped by dataset. Each dataset can contain multiple papers and evidence sentences."
                    )
                    show_dataset_grouped_matches(result["matched_results"])

                with tab2:
                    show_dataset_candidates(result["dataset_candidates"])

                with tab3:
                    show_paper_evidence(result["paper_evidence"])

            except Exception as e:
                st.error(f"Search failed: {e}")
else:
    st.info("Enter a topic in the sidebar and click Search.")
