import streamlit as st

from api_client import search_datasets
from components.result_cards import (
    show_dataset_candidates,
    show_paper_evidence,
    show_matched_results,
)


st.set_page_config(
    page_title="NLP/CL Dataset Evidence Finder",
    page_icon="🔎",
    layout="wide",
)

st.title("NLP/CL Dataset Evidence Finder")
st.caption(
    "Find NLP/Computational Linguistics dataset candidates and evidence sentences from arXiv papers."
)

with st.sidebar:
    st.header("Search Settings")

    query = st.text_input(
        "Research topic",
        value="machine translation dataset",
    )

    max_datasets = st.slider(
        "Max datasets per source",
        min_value=1,
        max_value=30,
        value=5,
    )

    max_papers = st.slider(
        "Max arXiv papers",
        min_value=1,
        max_value=10,
        value=3,
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
        value=False,
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
        "Matched Results",
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
                    st.caption(
                        "Matches are grouped by dataset and paper. Each paper can contain multiple evidence sentences."
                    )
                    show_matched_results(result["matched_results"])

                with tab2:
                    source_counts = {
                        "Hugging Face": 0,
                        "European Language Grid": 0,
                        "OpenML": 0,
                        "DataCite": 0,
                    }
                    for item in result["dataset_candidates"]:
                        source = item.get("source")
                        if source in source_counts:
                            source_counts[source] += 1

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Hugging Face", source_counts["Hugging Face"])
                    col2.metric(
                        "European Language Grid",
                        source_counts["European Language Grid"],
                    )
                    col3.metric("OpenML", source_counts["OpenML"])
                    col4.metric("DataCite", source_counts["DataCite"])

                    show_dataset_candidates(result["dataset_candidates"])

                with tab3:
                    show_paper_evidence(result["paper_evidence"])

            except Exception as e:
                st.error(f"Search failed: {e}")
else:
    st.info("Enter a topic in the sidebar and click Search.")