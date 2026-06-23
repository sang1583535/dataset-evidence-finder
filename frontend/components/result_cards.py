import streamlit as st


def show_dataset_candidates(candidates):
    st.subheader("Dataset Candidates")

    if not candidates:
        st.info("No dataset candidates found.")
        return

    for item in candidates:
        with st.container(border=True):
            st.markdown(f"**{item['name']}**")
            st.write(f"Source: {item['source']}")

            if item.get("url"):
                st.markdown(f"[Open source page]({item['url']})")

            if item.get("description"):
                st.write(item["description"])

            if item.get("tags"):
                st.caption("Tags: " + ", ".join(item["tags"][:10]))

            aliases = item.get("aliases", [])
            if aliases:
                with st.expander("Aliases used for matching"):
                    st.write(aliases)


def show_paper_evidence(evidence_items):
    st.subheader("Paper Evidence Sentences")

    if not evidence_items:
        st.info("No evidence sentences found.")
        return

    for item in evidence_items:
        with st.container(border=True):
            st.markdown(f"**{item['paper_title']}**")
            st.markdown(f"[Open paper]({item['paper_url']})")
            st.write(item["evidence_sentence"])

            col1, col2 = st.columns(2)
            col1.caption(f"Evidence score: {item.get('score', 0)}")
            col2.caption(f"Source text: {item.get('source_text_type', 'unknown')}")

            names = item.get("extracted_dataset_names", [])
            if names:
                st.caption("Extracted names: " + ", ".join(names))


def show_matched_results(matches):
    st.subheader("Source-Aware Matched Results")

    if not matches:
        st.warning("No direct matches found between source datasets and paper evidence yet.")
        return

    for item in matches:
        with st.container(border=True):
            st.markdown(f"### {item['dataset_name']}")

            col1, col2, col3 = st.columns(3)
            col1.write(f"Source: {item['dataset_source']}")
            col2.write(f"Matched alias: `{item['matched_alias']}`")
            col3.write(f"Score: {item['match_score']}")

            st.write(f"Match type: `{item['match_type']}`")

            if item.get("dataset_url"):
                st.markdown(f"[Open dataset/source]({item['dataset_url']})")

            if item.get("paper_title"):
                st.markdown(f"**Paper:** {item['paper_title']}")

            if item.get("paper_url"):
                st.markdown(f"[Open paper]({item['paper_url']})")

            if item.get("evidence_sentence"):
                st.info(item["evidence_sentence"])