"""Reusable chart components for GeneXA."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional

_DARK = dict(paper_bgcolor="#111827", plot_bgcolor="#111827", font_color="#f0f6ff")
_PALETTE = px.colors.qualitative.Vivid


def expression_bar_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """Horizontal bar chart of expression levels."""
    if "expression_level" not in df.columns or "gene_name" not in df.columns:
        return None

    fig = px.bar(
        df.sort_values("expression_level"),
        x="expression_level",
        y="gene_name",
        orientation="h",
        color="expression_level",
        color_continuous_scale="Viridis",
        template="plotly_dark",
        labels={"expression_level": "Expression Level", "gene_name": "Gene"},
        title="Expression Levels",
    )
    fig.update_layout(**_DARK, height=max(250, len(df) * 30), coloraxis_showscale=False)
    fig.update_traces(marker_line_width=0)
    return fig


def expression_heatmap(pivot_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns.tolist(),
        y=pivot_df.index.tolist(),
        colorscale="Viridis",
        hoverongaps=False,
        colorbar=dict(title="Expression", tickfont=dict(color="#f0f6ff")),
    ))
    fig.update_layout(
        **_DARK,
        height=420,
        xaxis_title="Condition",
        yaxis_title="Gene",
        title="Gene × Condition Heatmap",
    )
    return fig
