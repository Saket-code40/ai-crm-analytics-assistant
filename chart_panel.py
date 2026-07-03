"""
chart_panel.py — Interactive Visualization Panel for AI CRM Analytics.

Provides a Power BI / Tableau-style interactive chart experience
with controls for chart type, sorting, filtering, colors, and data export.

Only one public function:
    render_chart_panel(result, question, msg_time)
"""

import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

from chat_utils import generate_chart


# ==============================
# Constants
# ==============================

# Available chart types in the selector
CHART_TYPES = [
    "Auto",
    "Bar",
    "Horizontal Bar",
    "Line",
    "Pie",
    "Donut",
    "Scatter",
    "Area",
]

# Top N options (visual filter — does NOT modify SQL)
TOP_N_OPTIONS = {
    "All": None,
    "Top 5": 5,
    "Top 10": 10,
    "Top 20": 20,
    "Top 50": 50,
}

# Plotly qualitative color palettes
COLOR_THEMES = {
    "Plotly": None,           # Default Plotly palette
    "Pastel": px.colors.qualitative.Pastel,
    "Dark24": px.colors.qualitative.Dark24,
    "Bold": px.colors.qualitative.Bold,
    "Safe": px.colors.qualitative.Safe,
}

# Large dataset threshold
LARGE_DATASET_THRESHOLD = 100


# ==============================
# Data Analysis Helpers
# ==============================

def _detect_columns(df):
    """
    Detect the category (x) and metric (y) columns from a DataFrame.

    Strategy:
        - First non-numeric column → category (x)
        - First numeric column     → metric (y)

    Args:
        df: DataFrame to analyze

    Returns:
        tuple: (x_col, y_col) or (None, None) if undetectable
    """
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()
    num_cols = df.select_dtypes(include="number").columns.tolist()

    x_col = cat_cols[0] if cat_cols else None
    y_col = num_cols[0] if num_cols else None

    return x_col, y_col


def _prepare_data(df, top_n, sort_order, y_col):
    """
    Apply visual-only transformations: Top N filter + sorting.

    Does NOT modify the original DataFrame — returns a new copy.

    Args:
        df:         Original DataFrame
        top_n:      int or None (None = show all)
        sort_order: "None", "Ascending", or "Descending"
        y_col:      Column name to sort on

    Returns:
        DataFrame (filtered + sorted copy)
    """
    prepared = df.copy()

    # Apply sorting
    if sort_order == "Ascending":
        prepared = prepared.sort_values(by=y_col, ascending=True)
    elif sort_order == "Descending":
        prepared = prepared.sort_values(by=y_col, ascending=False)

    # Apply Top N filter
    if top_n is not None:
        prepared = prepared.head(top_n)

    return prepared


# ==============================
# Chart Builders
# ==============================

def _build_chart(df, chart_type, question, show_values,
                 show_legend, color_seq):
    """
    Build a Plotly figure based on user-selected chart type.

    Falls back to generate_chart() for "Auto" mode.

    Args:
        df:           Prepared DataFrame
        chart_type:   String from CHART_TYPES
        question:     Original question (for title)
        show_values:  Boolean — show value labels
        show_legend:  Boolean — show legend
        color_seq:    Color sequence (list) or None

    Returns:
        plotly Figure or None
    """
    x_col, y_col = _detect_columns(df)
    color_col = None
    text_auto = show_values

    # 3-column DataFrames get color grouping
    non_metric_cols = [c for c in df.columns if c != y_col]
    if len(non_metric_cols) >= 2 and len(df.columns) == 3:
        x_col = non_metric_cols[0]
        color_col = non_metric_cols[1]

    fig = None

    # --------------------------
    # Auto — delegate to existing logic
    # --------------------------
    if chart_type == "Auto":
        fig = generate_chart(df, question)
        if fig is not None:
            _apply_figure_options(fig, show_legend)

    # --------------------------
    # Bar (vertical)
    # --------------------------
    elif chart_type == "Bar" and x_col and y_col:
        fig = px.bar(
            df, x=x_col, y=y_col, color=color_col,
            text_auto=text_auto, title=question,
            barmode="group",
        )

    # --------------------------
    # Horizontal Bar
    # --------------------------
    elif chart_type == "Horizontal Bar" and x_col and y_col:
        fig = px.bar(
            df, x=y_col, y=x_col, color=color_col,
            orientation="h", text_auto=text_auto,
            title=question, barmode="group",
        )

    # --------------------------
    # Line
    # --------------------------
    elif chart_type == "Line" and x_col and y_col:
        fig = px.line(
            df, x=x_col, y=y_col, color=color_col,
            markers=True, title=question,
        )

    # --------------------------
    # Area
    # --------------------------
    elif chart_type == "Area" and x_col and y_col:
        fig = px.area(
            df, x=x_col, y=y_col, color=color_col,
            title=question,
        )

    # --------------------------
    # Pie
    # --------------------------
    elif chart_type == "Pie" and x_col and y_col:
        fig = px.pie(
            df, names=x_col, values=y_col,
            title=question,
        )

    # --------------------------
    # Donut
    # --------------------------
    elif chart_type == "Donut" and x_col and y_col:
        fig = px.pie(
            df, names=x_col, values=y_col,
            title=question, hole=0.4,
        )

    # --------------------------
    # Scatter (requires 2 numeric cols)
    # --------------------------
    elif chart_type == "Scatter":
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if len(num_cols) >= 2:
            fig = px.scatter(
                df, x=num_cols[0], y=num_cols[1],
                color=color_col, title=question,
            )
        else:
            # Can't do scatter with < 2 numeric — fall back to auto
            fig = generate_chart(df, question)
            if fig is not None:
                _apply_figure_options(fig, show_legend)

    # Apply common options to non-Auto charts
    if fig is not None and chart_type != "Auto":
        _apply_figure_options(fig, show_legend)

    # Apply color theme
    if fig is not None and color_seq is not None and chart_type != "Auto":
        fig.update_layout(colorway=color_seq)

    return fig


def _apply_figure_options(fig, show_legend):
    """
    Apply common figure options: legend visibility, hide Plotly logo.

    Args:
        fig:          Plotly Figure
        show_legend:  Boolean
    """
    fig.update_layout(
        showlegend=show_legend,
        template="plotly_white",
    )


# ==============================
# Plotly Config (Toolbar)
# ==============================

def _get_plotly_config():
    """
    Plotly config object — enables interactive toolbar.

    Features: Zoom, Pan, Box Select, Lasso, Reset Axes,
    Download PNG. Plotly watermark is hidden.

    Returns:
        dict (Plotly config)
    """
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["select2d"],
        "scrollZoom": True,

        "toImageButtonOptions": {
            "format": "png",
            "filename": "crm_chart",
            "height": 900,
            "width": 1600,
            "scale": 3,
        }
    }


# ==============================
# Main Public Function
# ==============================

def render_chart_panel(result: pd.DataFrame, question: str, msg_time: str):
    """
    Render the Interactive Visualization Panel with all controls.

    Displays:
        1. Control bar (chart type, sort, top-N, values, legend, colors)
        2. Large dataset warning (if > 100 rows)
        3. Interactive Plotly chart with toolbar
        4. Download CSV / Excel buttons

    Args:
        result:   DataFrame (from SQL query)
        question: Original user question (for title + Auto mode)
        msg_time: Message timestamp (used as unique Streamlit key prefix)
    """
    st.markdown("#### 📈 Visualization")

    # ----------------------------------
    # Detect columns once
    # ----------------------------------
    x_col, y_col = _detect_columns(result)

    if x_col is None or y_col is None:
        st.info("Cannot generate chart — no suitable category + metric columns detected.")
        return

    # ----------------------------------
    # Large dataset warning
    # ----------------------------------
    if len(result) > LARGE_DATASET_THRESHOLD:
        st.warning(
            f"⚠️ Dataset has **{len(result)}** rows. "
            "Consider using **Top N** filter for better visualization."
        )

    # ----------------------------------
    # Row 1: Primary controls
    # ----------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        chart_type = st.selectbox(
            "Chart Type",
            CHART_TYPES,
            key=f"chart_type_{msg_time}",
        )

    with col2:
        sort_order = st.selectbox(
            "Sort",
            ["None", "Ascending", "Descending"],
            key=f"sort_{msg_time}",
        )

    with col3:
        top_n_label = st.selectbox(
            "Show",
            list(TOP_N_OPTIONS.keys()),
            key=f"topn_{msg_time}",
        )
        top_n = TOP_N_OPTIONS[top_n_label]

    with col4:
        color_theme_name = st.selectbox(
            "Color Theme",
            list(COLOR_THEMES.keys()),
            key=f"color_{msg_time}",
        )
        color_seq = COLOR_THEMES[color_theme_name]

    # ----------------------------------
    # Row 2: Toggle controls
    # ----------------------------------
    col5, col6 = st.columns(2)

    with col5:
        show_values = st.checkbox(
            "Show Values",
            value=True,
            key=f"showval_{msg_time}",
        )

    with col6:
        show_legend = st.checkbox(
            "Show Legend",
            value=True,
            key=f"showlegend_{msg_time}",
        )

    # ----------------------------------
    # Prepare data (filter + sort)
    # ----------------------------------
    prepared = _prepare_data(result, top_n, sort_order, y_col)

    # ----------------------------------
    # Build chart
    # ----------------------------------
    fig = _build_chart(
        prepared,
        chart_type,
        question,
        show_values,
        show_legend,
        color_seq,
    )

    # ----------------------------------
    # Render chart with Plotly toolbar
    # ----------------------------------
    if fig is not None:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=_get_plotly_config(),
            key=f"viz_{msg_time}",
        )

    # ----------------------------------
    # Download buttons
    # ----------------------------------
    csv_data = prepared.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name=f"crm_data_{msg_time.replace(' ', '_').replace(':', '-')}.csv",
        mime="text/csv",
        key=f"dl_csv_{msg_time}",
    )

    # Excel via BytesIO (requires openpyxl — graceful fallback)
    try:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            prepared.to_excel(writer, index=False, sheet_name="Data")
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"crm_data_{msg_time.replace(' ', '_').replace(':', '-')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_xlsx_{msg_time}",
        )
    except ImportError:
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"crm_data_{msg_time.replace(' ', '_').replace(':', '-')}.csv",
            mime="text/csv",
            key=f"dl_csv_fallback_{msg_time}",
        )
