"""Gene summary card rendered as HTML."""

import streamlit as st


def gene_summary_card(gene: str, tissue: str, condition: str, expression: float, sample_count: int = None):
    level = "HIGH" if expression >= 7 else "MODERATE" if expression >= 4 else "LOW"
    badge_class = "badge-high" if level == "HIGH" else "badge-mid" if level == "MODERATE" else "badge-low"

    sample_str = f"<span style='color:#8899bb; font-size:0.82rem;'>n = {sample_count} samples</span>" if sample_count else ""

    st.markdown(f"""
    <div class='gene-card'>
        <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
            <div>
                <div class='gene-name'>{gene}</div>
                <div class='gene-meta'>{tissue} · {condition}</div>
            </div>
            <span class='expression-badge {badge_class}'>{level}</span>
        </div>
        <div style='margin-top:14px; display:flex; align-items:baseline; gap:8px;'>
            <span style='font-size:2rem; font-weight:700; color:#00d4aa; font-family:JetBrains Mono,monospace;'>
                {expression:.3f}
            </span>
            <span style='color:#8899bb; font-size:0.82rem;'>expression units</span>
            {sample_str}
        </div>
    </div>
    """, unsafe_allow_html=True)
