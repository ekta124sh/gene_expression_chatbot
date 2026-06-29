"""
GeneXA - Gene Expression Search Assistant
Production-grade Streamlit application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import io
import time

from db.connection import get_db_connection
from db.queries import GeneQueryEngine
from nlp.parser import NLPParser
from utils.logger import get_logger
from utils.export import export_to_excel, export_to_csv
from components.cards import gene_summary_card
from components.charts import expression_bar_chart, expression_heatmap

logger = get_logger(__name__)

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GeneXA · Gene Expression Assistant",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #0a0e1a;
    --bg-card: #111827;
    --bg-input: #1a2236;
    --accent: #00d4aa;
    --accent-dim: #00d4aa22;
    --accent2: #6366f1;
    --text-primary: #f0f6ff;
    --text-muted: #8899bb;
    --border: #1e2d4a;
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
    --radius: 12px;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d1424 !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 4rem !important; max-width: 1400px; }

/* Chat messages */
.user-msg {
    background: var(--accent2);
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px 60px;
    font-size: 0.95rem;
    line-height: 1.5;
    box-shadow: 0 2px 12px #6366f133;
}
.bot-msg {
    background: var(--bg-card);
    color: var(--text-primary);
    padding: 14px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 60px 8px 0;
    font-size: 0.95rem;
    line-height: 1.6;
    border-left: 3px solid var(--accent);
    box-shadow: 0 2px 12px #00000033;
}
.bot-msg code {
    background: #1a2236;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: var(--accent);
}

/* Cards */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: var(--accent); }
.metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
}
.metric-card .label {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}

/* Gene summary card */
.gene-card {
    background: linear-gradient(135deg, #111827 0%, #1a2236 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    margin: 8px 0;
    position: relative;
    overflow: hidden;
}
.gene-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.gene-name {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}
.gene-meta {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-top: 4px;
}
.expression-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}
.badge-high { background: #22c55e22; color: #22c55e; border: 1px solid #22c55e44; }
.badge-low  { background: #ef444422; color: #ef4444; border: 1px solid #ef444444; }
.badge-mid  { background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b44; }

/* Input styling */
.stTextInput > div > div > input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    padding: 14px 16px !important;
    font-size: 0.95rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-dim) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--accent), #00b894) !important;
    color: #0a0e1a !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-family: 'Inter', sans-serif !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Pill tags */
.pill {
    display: inline-block;
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid #00d4aa33;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    margin: 2px;
}

/* Dividers */
hr { border-color: var(--border) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: var(--bg-card) !important; border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: var(--text-muted) !important; border-radius: 8px !important; }
.stTabs [aria-selected="true"] { background: var(--accent) !important; color: #0a0e1a !important; font-weight: 600 !important; }

/* History items */
.history-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0;
    font-size: 0.85rem;
    cursor: pointer;
    transition: border-color 0.15s;
}
.history-item:hover { border-color: var(--accent); }
.history-time { color: var(--text-muted); font-size: 0.72rem; margin-top: 2px; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: var(--radius) !important; }

/* Section headers */
.section-eyebrow {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 6px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─── State initialization ────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "active_filters" not in st.session_state:
    st.session_state.active_filters = {"gene": "", "tissue": "", "condition": ""}

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 16px 0 24px;'>
        <div style='font-size:1.5rem; font-weight:800; color:#00d4aa; letter-spacing:-0.02em;'>
            🧬 GeneXA
        </div>
        <div style='font-size:0.78rem; color:#8899bb; margin-top:4px;'>
            Gene Expression Intelligence Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Filters")
    gene_filter = st.text_input("Gene name", placeholder="e.g. TP53, BRCA1", key="f_gene")
    tissue_filter = st.selectbox("Tissue type", ["All", "Lung", "Liver", "Brain", "Heart", "Kidney", "Blood", "Breast"], key="f_tissue")
    condition_filter = st.selectbox("Condition", ["All", "Normal", "Infected", "Cancer", "Hypoxia", "Stress", "Treated"], key="f_condition")

    st.markdown("---")
    st.markdown("### 💡 Quick Queries")
    quick_queries = [
        "Show top expressed genes in lung cancer",
        "Compare TP53 across all tissues",
        "Genes upregulated under infection",
        "BRCA1 expression in breast tissue",
        "Heatmap of all cancer conditions",
    ]
    for q in quick_queries:
        if st.button(q, key=f"qq_{q[:10]}", use_container_width=True):
            st.session_state._quick_query = q

    st.markdown("---")
    st.markdown("### 📜 Search History")
    if st.session_state.history:
        for h in reversed(st.session_state.history[-8:]):
            st.markdown(f"""
            <div class='history-item'>
                <div>{h['query'][:40]}{'...' if len(h['query']) > 40 else ''}</div>
                <div class='history-time'>{h['time']}</div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("🗑 Clear history", use_container_width=True):
            st.session_state.history = []
    else:
        st.markdown("<div style='color:#8899bb; font-size:0.82rem;'>No queries yet</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⭐ Favorites")
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            st.markdown(f"<span class='pill'>{fav}</span>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#8899bb; font-size:0.82rem;'>Save queries with ★</div>", unsafe_allow_html=True)

# ─── Main area ───────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown("""
    <div style='margin-bottom:8px;'>
        <div class='section-eyebrow'>Biotech Intelligence Platform</div>
        <h1 style='font-size:1.9rem; font-weight:800; margin:0; letter-spacing:-0.02em;'>
            Gene Expression Search Assistant
        </h1>
        <p style='color:#8899bb; font-size:0.92rem; margin-top:6px;'>
            Ask in natural language · Instant database queries · AI-powered insights
        </p>
    </div>
    """, unsafe_allow_html=True)
with col_badge:
    st.markdown("""
    <div style='text-align:right; padding-top:12px;'>
        <span class='pill'>v2.0</span>
        <span class='pill'>MySQL</span>
        <span class='pill'>NLP</span>
    </div>
    """, unsafe_allow_html=True)

# KPI bar
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown("<div class='metric-card'><div class='value'>24,312</div><div class='label'>Genes indexed</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown("<div class='metric-card'><div class='value'>48</div><div class='label'>Tissue types</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown("<div class='metric-card'><div class='value'>12</div><div class='label'>Conditions</div></div>", unsafe_allow_html=True)
with k4:
    st.markdown("<div class='metric-card'><div class='value'>1.2M</div><div class='label'>Expression records</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Main tabs ───────────────────────────────────────────────────────────────
tab_chat, tab_explore, tab_compare, tab_heatmap, tab_export = st.tabs([
    "💬 Chat", "🔬 Explore", "📊 Compare", "🌡 Heatmap", "📥 Export"
])

# ─── TAB 1: Chat ─────────────────────────────────────────────────────────────
with tab_chat:
    chat_col, info_col = st.columns([3, 1.1])

    with chat_col:
        # Welcome message
        if not st.session_state.messages:
            st.markdown("""
            <div class='bot-msg'>
                👋 Hi! I'm <strong>GeneXA</strong>, your gene expression intelligence assistant.<br><br>
                Try asking things like:<br>
                • <code>What's the expression of TP53 in lung under infected condition?</code><br>
                • <code>Show me all genes upregulated in liver cancer</code><br>
                • <code>Compare BRCA1 and BRCA2 expression across tissues</code>
            </div>
            """, unsafe_allow_html=True)

        # Render conversation
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"<div class='user-msg'>🧑‍💻 {msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='bot-msg'>🧬 {msg['content']}</div>", unsafe_allow_html=True)
                if msg.get("df") is not None:
                    df = msg["df"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    if not df.empty and "expression_level" in df.columns:
                        fig = expression_bar_chart(df)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)

        # Input area
        st.markdown("<br>", unsafe_allow_html=True)
        query_val = st.session_state.pop("_quick_query", "")

        with st.container():
            inp_col, btn_col, fav_col = st.columns([6, 1, 1])
            with inp_col:
                user_input = st.text_input(
                    "Ask about gene expression",
                    value=query_val,
                    placeholder="e.g. Show TP53 expression in lung under infection...",
                    label_visibility="collapsed",
                    key="chat_input"
                )
            with btn_col:
                send = st.button("Send →", use_container_width=True)
            with fav_col:
                fav = st.button("⭐ Save", use_container_width=True)

        if fav and user_input and user_input not in st.session_state.favorites:
            st.session_state.favorites.append(user_input)
            st.success("Saved to favorites!")

        if send and user_input.strip():
            _process_query(user_input.strip())

    with info_col:
        st.markdown("<div class='section-eyebrow'>AI Suggestions</div>", unsafe_allow_html=True)
        suggestions = [
            "TP53 expression in lung cancer",
            "EGFR upregulation under hypoxia",
            "BRCA1 vs BRCA2 comparison",
            "Top 10 genes in infected liver",
        ]
        for s in suggestions:
            if st.button(s, key=f"sug_{s[:8]}", use_container_width=True):
                st.session_state._quick_query = s
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-eyebrow'>Last Query Stats</div>", unsafe_allow_html=True)
        if st.session_state.last_results is not None:
            df = st.session_state.last_results
            st.markdown(f"<div class='metric-card'><div class='value'>{len(df)}</div><div class='label'>Results returned</div></div>", unsafe_allow_html=True)
            if "expression_level" in df.columns:
                avg_exp = df["expression_level"].mean()
                st.markdown(f"<br><div class='metric-card'><div class='value'>{avg_exp:.2f}</div><div class='label'>Avg expression</div></div>", unsafe_allow_html=True)

# ─── TAB 2: Explore ──────────────────────────────────────────────────────────
with tab_explore:
    st.markdown("### 🔬 Database Explorer")
    st.markdown("Browse and filter gene expression records directly.")

    ex_c1, ex_c2, ex_c3, ex_c4 = st.columns(4)
    with ex_c1:
        exp_gene = st.text_input("Gene", placeholder="TP53", key="ex_gene")
    with ex_c2:
        exp_tissue = st.selectbox("Tissue", ["All", "Lung", "Liver", "Brain", "Heart", "Kidney"], key="ex_tissue")
    with ex_c3:
        exp_cond = st.selectbox("Condition", ["All", "Normal", "Infected", "Cancer", "Hypoxia"], key="ex_cond")
    with ex_c4:
        exp_limit = st.slider("Max rows", 10, 500, 50, key="ex_limit")

    if st.button("🔍 Fetch Records", key="ex_fetch"):
        with st.spinner("Querying database..."):
            try:
                engine = GeneQueryEngine()
                df = engine.explore(
                    gene=exp_gene or None,
                    tissue=None if exp_tissue == "All" else exp_tissue,
                    condition=None if exp_cond == "All" else exp_cond,
                    limit=exp_limit
                )
                if df.empty:
                    st.warning("No records found for those filters.")
                else:
                    st.success(f"Found {len(df)} records")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.session_state.last_results = df
            except Exception as e:
                st.error(f"Database error: {e}")
                logger.error(f"Explore query error: {e}")

# ─── TAB 3: Compare ──────────────────────────────────────────────────────────
with tab_compare:
    st.markdown("### 📊 Comparative Gene Expression Analysis")
    cmp_c1, cmp_c2 = st.columns(2)
    with cmp_c1:
        genes_input = st.text_area("Genes to compare (one per line)", height=120, placeholder="TP53\nBRCA1\nEGFR\nMYC")
    with cmp_c2:
        cmp_tissue = st.selectbox("Tissue context", ["All", "Lung", "Liver", "Brain", "Breast", "Blood"], key="cmp_tissue")
        cmp_cond = st.selectbox("Condition", ["All", "Normal", "Cancer", "Infected"], key="cmp_cond")

    if st.button("⚡ Compare Genes", key="cmp_run"):
        gene_list = [g.strip().upper() for g in genes_input.split("\n") if g.strip()]
        if len(gene_list) < 2:
            st.warning("Enter at least 2 genes to compare.")
        else:
            with st.spinner("Running comparative analysis..."):
                try:
                    engine = GeneQueryEngine()
                    df = engine.compare_genes(
                        genes=gene_list,
                        tissue=None if cmp_tissue == "All" else cmp_tissue,
                        condition=None if cmp_cond == "All" else cmp_cond
                    )
                    if df.empty:
                        st.warning("No data found for these genes.")
                    else:
                        fig = px.bar(
                            df, x="gene_name", y="expression_level",
                            color="tissue_type" if "tissue_type" in df.columns else "gene_name",
                            barmode="group",
                            template="plotly_dark",
                            color_discrete_sequence=px.colors.qualitative.Vivid,
                            title="Comparative Gene Expression",
                        )
                        fig.update_layout(
                            paper_bgcolor="#111827", plot_bgcolor="#111827",
                            font_color="#f0f6ff", title_font_size=16,
                            legend_title_text="Tissue",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        st.session_state.last_results = df
                except Exception as e:
                    st.error(f"Comparison error: {e}")
                    logger.error(f"Compare error: {e}")

# ─── TAB 4: Heatmap ──────────────────────────────────────────────────────────
with tab_heatmap:
    st.markdown("### 🌡 Expression Heatmap")
    hm_c1, hm_c2 = st.columns(2)
    with hm_c1:
        hm_genes = st.text_area("Genes (one per line)", height=120, placeholder="TP53\nBRCA1\nEGFR\nMYC\nKRAS", key="hm_genes")
    with hm_c2:
        hm_cond = st.multiselect("Conditions", ["Normal", "Infected", "Cancer", "Hypoxia", "Stress"], default=["Normal", "Cancer"])

    if st.button("🌡 Generate Heatmap", key="hm_run"):
        gene_list = [g.strip().upper() for g in hm_genes.split("\n") if g.strip()]
        if not gene_list or not hm_cond:
            st.warning("Enter at least one gene and one condition.")
        else:
            with st.spinner("Building heatmap..."):
                try:
                    engine = GeneQueryEngine()
                    df = engine.heatmap_data(genes=gene_list, conditions=hm_cond)
                    if df.empty:
                        st.warning("No data found.")
                    else:
                        pivot = df.pivot_table(index="gene_name", columns="condition", values="expression_level", aggfunc="mean")
                        fig = go.Figure(data=go.Heatmap(
                            z=pivot.values,
                            x=pivot.columns.tolist(),
                            y=pivot.index.tolist(),
                            colorscale="Viridis",
                            hoverongaps=False,
                            colorbar=dict(title="Expression")
                        ))
                        fig.update_layout(
                            title="Gene Expression Heatmap",
                            paper_bgcolor="#111827", plot_bgcolor="#111827",
                            font_color="#f0f6ff", height=420,
                            xaxis_title="Condition",
                            yaxis_title="Gene"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.session_state.last_results = df
                except Exception as e:
                    st.error(f"Heatmap error: {e}")
                    logger.error(f"Heatmap error: {e}")

# ─── TAB 5: Export ───────────────────────────────────────────────────────────
with tab_export:
    st.markdown("### 📥 Export Results")
    if st.session_state.last_results is not None:
        df = st.session_state.last_results
        st.markdown(f"**{len(df)} records** ready for export from your last query.")
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

        exp_c1, exp_c2 = st.columns(2)
        with exp_c1:
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download CSV",
                data=csv_bytes,
                file_name=f"genexa_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with exp_c2:
            excel_bytes = export_to_excel(df)
            st.download_button(
                "⬇ Download Excel",
                data=excel_bytes,
                file_name=f"genexa_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.info("Run a query first to see export options here.")


# ─── Query processor (called from chat tab) ──────────────────────────────────
def _process_query(query: str):
    """Process user query end-to-end."""
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.history.append({"query": query, "time": datetime.now().strftime("%H:%M")})

    with st.spinner("🧬 Searching gene database..."):
        try:
            parser = NLPParser()
            parsed = parser.parse(query)

            engine = GeneQueryEngine()
            df = engine.execute(parsed)

            if df.empty:
                response = f"No expression data found for **{parsed.get('gene', 'that gene')}** in **{parsed.get('tissue', 'that tissue')}** under **{parsed.get('condition', 'that condition')}**. Try adjusting your query or checking the spelling."
                st.session_state.messages.append({"role": "assistant", "content": response, "df": None})
            else:
                gene = parsed.get("gene", "the gene")
                tissue = parsed.get("tissue", "")
                condition = parsed.get("condition", "")
                avg_exp = df["expression_level"].mean() if "expression_level" in df.columns else None
                badge = _expression_badge(avg_exp)

                response = (
                    f"Found **{len(df)} records** for `{gene}`"
                    + (f" in **{tissue}**" if tissue else "")
                    + (f" under **{condition}** condition" if condition else "")
                    + (f". Average expression: **{avg_exp:.3f}** {badge}" if avg_exp is not None else ".")
                )
                st.session_state.messages.append({"role": "assistant", "content": response, "df": df})
                st.session_state.last_results = df

        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"⚠️ Something went wrong: `{str(e)}`. Please try rephrasing your query.",
                "df": None
            })

    st.rerun()


def _expression_badge(value):
    if value is None:
        return ""
    if value >= 7:
        return "<span class='expression-badge badge-high'>HIGH</span>"
    elif value >= 4:
        return "<span class='expression-badge badge-mid'>MODERATE</span>"
    else:
        return "<span class='expression-badge badge-low'>LOW</span>"
