import streamlit as st

from api_client import search_datasets, get_reference_catalogues
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
        min_value=5,
        max_value=30,
        value=10,
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

    use_datacite = st.checkbox(
        "Use DataCite metadata search",
        value=False,
        help="Optional. DataCite can add DOI-based dataset metadata, but it may return broad results.",
    )

    search_button = st.button("Search", type="primary")

    st.divider()
    st.caption("Scope: NLP / Computational Linguistics only")


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Matched Results",
        "Dataset Candidates",
        "Paper Evidence",
        "Reference Catalogues",
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
                )

                with tab1:
                    st.caption(
                        "Matches are created using dataset aliases, normalized matching, and fuzzy matching."
                    )
                    show_matched_results(result["matched_results"])

                with tab2:
                    show_dataset_candidates(result["dataset_candidates"])

                with tab3:
                    show_paper_evidence(result["paper_evidence"])

                with tab4:
                    catalogues = get_reference_catalogues()
                    st.subheader("Reference CL/NLP Catalogues")

                    for item in catalogues:
                        with st.container(border=True):
                            st.markdown(f"**{item['name']}**")
                            st.write(item["role"])
                            st.write(f"Integration status: `{item['integration_status']}`")
                            st.write(item["note"])
                            st.markdown(f"[Open catalogue]({item['url']})")

            except Exception as e:
                st.error(f"Search failed: {e}")
else:
    st.info("Enter a topic in the sidebar and click Search.")