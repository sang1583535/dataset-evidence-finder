import pandas as pd
import streamlit as st


def build_comparison_rows(matches: list[dict]) -> list[dict]:
    rows = []
    for m in matches:
        evidences = m.get("evidences", [])
        source_types = sorted(
            set(e.get("source_text_type", "unknown") for e in evidences)
        )
        rows.append(
            {
                "Dataset": m.get("dataset_name", ""),
                "Dataset Source": m.get("dataset_source", ""),
                "Paper": m.get("paper_title", ""),
                "Evidence Count": m.get("evidence_count", 0),
                # "Best Match Score": round(float(m.get("best_match_score", 0.0)), 1),
                "Evidence Sources": ", ".join(source_types),
                "Dataset URL": m.get("dataset_url") or "",
                "Paper URL": m.get("paper_url") or "",
            }
        )
    return rows


def show_comparison_table(matches: list[dict]) -> None:
    st.subheader("Match Overview")

    if not matches:
        st.info("No matches to display.")
        return

    rows = build_comparison_rows(matches)
    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        width="stretch",
        column_config={
            "Dataset URL": st.column_config.LinkColumn("Dataset URL"),
            "Paper URL": st.column_config.LinkColumn("Paper URL"),
            # "Best Match Score": st.column_config.NumberColumn(
            #     "Best Match Score", format="%.1f"
            # ),
        },
        hide_index=True,
    )
