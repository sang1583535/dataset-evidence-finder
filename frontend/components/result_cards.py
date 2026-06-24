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
            col2.write(f"Evidence count: {item.get('evidence_count', 0)}")
            col3.write(f"Best match score: {item.get('best_match_score', 0.0)}")

            if item.get("dataset_url"):
                st.markdown(f"[Open dataset/source]({item['dataset_url']})")

            st.markdown(f"**Paper:** {item['paper_title']}")
            st.markdown(f"[Open paper]({item['paper_url']})")

            evidences = item.get("evidences", [])
            with st.expander(f"Show evidence sentences ({len(evidences)})"):
                for idx, evidence in enumerate(evidences, start=1):
                    st.markdown(f"**Evidence {idx}:**")
                    st.write(evidence.get("evidence_sentence", ""))
                    st.caption(
                        f"Matched alias: {evidence.get('matched_alias', '')} | "
                        f"Match type: {evidence.get('match_type', '')} | "
                        f"Match score: {evidence.get('match_score', 0.0)} | "
                        f"Evidence score: {evidence.get('evidence_score', 0)} | "
                        f"Source text: {evidence.get('source_text_type', 'unknown')}"
                    )