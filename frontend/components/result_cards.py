from collections import defaultdict

import streamlit as st

from components.badges import render_badges, source_badge
from utils.text_highlight import highlight_matched_alias


_SOURCE_ORDER = {
    "Hugging Face": 0,
    "European Language Grid": 1,
    "OpenML": 2,
    "DataCite": 3,
}


def show_dataset_candidates(candidates: list[dict]) -> None:
    st.subheader("Dataset Candidates")

    if not candidates:
        st.info("No dataset candidates found.")
        return

    sources = sorted(
        set(item.get("source", "Unknown") for item in candidates),
        key=lambda s: _SOURCE_ORDER.get(s, 999),
    )

    for source in sources:
        source_items = [
            item for item in candidates if item.get("source", "Unknown") == source
        ]
        with st.expander(f"{source} ({len(source_items)})", expanded=True):
            for item in source_items:
                with st.container(border=True):
                    badge_html = source_badge(item.get("source", ""))
                    st.markdown(
                        f'{badge_html} **{item.get("name", "")}**',
                        unsafe_allow_html=True,
                    )
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


def show_paper_evidence(evidence_items: list[dict]) -> None:
    st.subheader("Paper Candidates")
    st.caption(
        "Potential papers returned by search, each with extracted evidence sentences."
    )

    if not evidence_items:
        st.info("No paper candidates found.")
        return

    groups: dict[str, list[dict]] = defaultdict(list)
    paper_meta: dict[str, str] = {}
    for item in evidence_items:
        key = item.get("paper_url") or item.get("paper_title", "")
        groups[key].append(item)
        paper_meta[key] = item.get("paper_url", "")

    for key, sentences in groups.items():
        paper_title = sentences[0].get("paper_title", "")
        paper_url = paper_meta[key]
        with st.container(border=True):
            st.markdown(f"**{paper_title}**")
            if paper_url:
                st.markdown(f"[Open paper]({paper_url})")
            st.caption(f"{len(sentences)} evidence sentence(s)")

            for idx, item in enumerate(sentences, start=1):
                with st.container(border=True):
                    st.write(f"**{idx}.** {item.get('evidence_sentence', '')}")
                    names = item.get("extracted_dataset_names", [])
                    caption = f"Source: {item.get('source_text_type', 'unknown')}"
                    section = item.get("section_title")
                    if section:
                        caption += f" | Section: {section}"
                    if names:
                        caption += " | Extracted: " + ", ".join(names)
                    st.caption(caption)


def show_dataset_grouped_matches(matches: list[dict]) -> None:
    if not matches:
        st.warning(
            "No direct matches found between source datasets and paper evidence yet."
        )
        return

    groups: dict[str, list[dict]] = defaultdict(list)
    for m in matches:
        groups[m.get("dataset_name", "Unknown")].append(m)

    dataset_stats: list[tuple[str, list[dict], float, int]] = []
    for dataset_name, items in groups.items():
        best_score = max(m.get("best_match_score", 0.0) for m in items)
        total_evidence = sum(len(m.get("evidences", [])) for m in items)
        dataset_stats.append((dataset_name, items, best_score, total_evidence))

    dataset_stats.sort(key=lambda x: (-x[2], -x[3]))

    for dataset_name, items, best_score, total_evidence in dataset_stats:
        first = items[0]
        dataset_source = first.get("dataset_source", "")
        dataset_url = first.get("dataset_url")

        all_source_types = sorted(
            set(
                e.get("source_text_type", "unknown")
                for m in items
                for e in m.get("evidences", [])
            )
        )
        badges_html = render_badges([dataset_source] + all_source_types)

        with st.container(border=True):
            st.markdown(f"### {dataset_name}")
            st.markdown(badges_html, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Papers", len(items))
            c2.metric("Total Evidence", total_evidence)
            # c3.metric("Best Match Score", f"{best_score:.1f}")

            if dataset_url:
                st.markdown(f"[Open dataset/source]({dataset_url})")

            for m in items:
                paper_title = m.get("paper_title", "Unknown Paper")
                paper_url = m.get("paper_url", "")
                evidences = m.get("evidences", [])

                with st.expander(f"📄 {paper_title} ({len(evidences)} evidence)"):
                    if paper_url:
                        st.markdown(f"[Open paper]({paper_url})")

                    for idx, ev in enumerate(evidences, start=1):
                        sentence = ev.get("evidence_sentence", "")
                        alias = ev.get("matched_alias", "")
                        highlighted = highlight_matched_alias(sentence, alias)

                        with st.container(border=True):
                            st.markdown(
                                f"**Evidence {idx}:** {highlighted}",
                                unsafe_allow_html=True,
                            )
                            st.caption(
                                f"Alias: **{alias}** | "
                                f"Type: {ev.get('match_type', '')} | "
                                f"Source: {ev.get('source_text_type', 'unknown')}"
                                + (f" | Section: {ev['section_title']}" if ev.get("section_title") else "")
                            )


def show_matched_results(matches: list[dict]) -> None:
    show_dataset_grouped_matches(matches)
