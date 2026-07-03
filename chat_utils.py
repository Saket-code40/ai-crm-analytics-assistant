"""
chat_utils.py — Business logic for the AI CRM chat pipeline.

This module isolates all question-processing logic from the Streamlit UI,
making it testable, reusable, and maintainable.

Functions:
    generate_chart(result, question)    → Plotly figure or None
    process_question(question, conversation) → message dict with full response
"""

import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------------------------------------------------------------------
# Local imports (same directory)
# ---------------------------------------------------------------------------
from ai_sql import generate_sql
from ai_insights import generate_insight
from followup import generate_followups


# ==============================
# Chart Generation
# ==============================

def generate_chart(result: pd.DataFrame, question: str):
    """
    Intelligently select and generate a Plotly chart based on the
    dataframe structure and question context.

    Detection priority:
        1. DataFrame structure inspection (date, percentage, numeric, cardinality)
        2. Question keyword matching (distribution, trend, etc.)
        3. Defaults based on column count and row count

    Logic:
        4+ columns     → None (table-only)
        2 cols, both numeric     → Scatter
        2 cols, x is date-like   → Line
        2 cols, y has "percent" → Donut
        2 cols, >10 rows         → Horizontal Bar
        3 cols                  → Grouped Bar or Multi-line
        2 cols, keywords match  → Pie / Line / Bar (keyword-driven)
        default                 → Vertical Bar

    Args:
        result:   DataFrame returned from SQL execution
        question: Original user question (for context hints)

    Returns:
        plotly.graph_objects.Figure or None
    """

    # Skip if no numeric data to plot
    numeric_cols = result.select_dtypes(include="number").columns
    if len(numeric_cols) == 0:
        return None

    q = question.lower()
    fig = None

    # ---------------------------------
    # TWO columns → rich chart options
    # ---------------------------------
    if len(result.columns) == 2:
        x = result.columns[0]
        y = result.columns[1]

        if pd.api.types.is_numeric_dtype(result[y]):

            # ===== LAYER 1: DataFrame structure inspection =====

            # Both columns numeric → Scatter
            if pd.api.types.is_numeric_dtype(result[x]):
                fig = px.scatter(
                    result,
                    x=x,
                    y=y,
                    title=question
                )

            # x column looks like a date → Line
            elif _is_date_like(result, x):
                fig = px.line(
                    result,
                    x=x,
                    y=y,
                    markers=True,
                    title=question
                )

            # y column name contains "percent" → Donut
            elif any(word in y.lower() for word in [
                "percent", "percentage", "ratio", "rate", "share"
            ]):
                fig = px.pie(
                    result,
                    names=x,
                    values=y,
                    title=question,
                    hole=0.4
                )

            # ===== LAYER 2: Question keyword matching =====

            # Pie — distribution / share / percentage
            elif any(word in q for word in [
                "distribution", "share", "percentage", "pie", "split", "breakdown"
            ]):
                fig = px.pie(
                    result,
                    names=x,
                    values=y,
                    title=question,
                    hole=0.4
                )

            # Line — time-based trends
            elif any(word in q for word in [
                "month", "year", "trend", "growth", "daily", "weekly",
                "quarterly", "over time", "timeline"
            ]):
                fig = px.line(
                    result,
                    x=x,
                    y=y,
                    markers=True,
                    title=question
                )

            # ===== LAYER 3: Row-count-based defaults =====

            # Horizontal Bar — many categories (>10 rows)
            elif len(result) > 10:
                fig = px.bar(
                    result,
                    x=y,
                    y=x,
                    orientation="h",
                    title=question,
                    text_auto=True
                )

            # Vertical Bar — default for 2 columns
            else:
                fig = px.bar(
                    result,
                    x=x,
                    y=y,
                    text_auto=True,
                    title=question
                )

    # ---------------------------------
    # THREE columns → grouped / colored
    # ---------------------------------
    elif len(result.columns) == 3:
        x = result.columns[0]
        color = result.columns[1]
        y = result.columns[2]

        if pd.api.types.is_numeric_dtype(result[y]):

            # Multi-line for time-based grouped data
            if any(word in q for word in [
                "trend", "growth", "month", "year", "over time"
            ]) or _is_date_like(result, x):
                fig = px.line(
                    result,
                    x=x,
                    y=y,
                    color=color,
                    markers=True,
                    title=question
                )

            # Grouped Bar — default for 3 columns
            else:
                fig = px.bar(
                    result,
                    x=x,
                    y=y,
                    color=color,
                    barmode="group",
                    title=question,
                    text_auto=True
                )

    return fig


def _is_date_like(df: pd.DataFrame, col: str) -> bool:
    """
    Check if a column contains date-like values.

    Detection strategies:
        1. Column name contains date-related keywords
        2. Column dtype is datetime64
        3. Sample values match YYYY-MM-DD pattern

    Args:
        df:  DataFrame
        col: Column name to check

    Returns:
        True if the column appears to be a date column
    """
    # Check column name
    name_lower = col.lower()
    if any(word in name_lower for word in [
        "date", "time", "month", "year", "quarter", "week",
        "created", "modified", "closed", "entered"
    ]):
        return True

    # Check dtype
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        return True

    # Check sample values for YYYY-MM-DD pattern
    sample = df[col].dropna().head(5).astype(str)
    for val in sample:
        if len(val) >= 10 and val[4] == "-" and val[7] == "-":
            return True

    return False


# ==============================
# Question Processing Pipeline
# ==============================

def process_question(question: str, conversation: list) -> dict:
    """
    Full pipeline: Question → SQL → Execute → Chart → Insight → Follow-ups.

    This function orchestrates every step of the AI response generation.
    It is designed to be called from the UI layer and returns a complete
    message dictionary that the UI can render.

    Args:
        question:    The user's natural language question
        conversation: List of previous conversation context dicts
                      (for follow-up question awareness)

    Returns:
        dict with keys:
            "time"      → str   (timestamp)
            "question"  → str   (the question asked)
            "sql"       → str   (generated SQL)
            "result"    → DataFrame (query results)
            "chart"     → Figure or None
            "insight"   → str   (AI business insight)
            "followups" → list[str] (suggested follow-up questions)

    Raises:
        Exception: If SQL generation or execution fails
    """

    conn = sqlite3.connect("crm.db")

    try:
        # Step 1 — Generate SQL
        sql = generate_sql(question, conversation)

        # Step 2 — Execute SQL
        result = pd.read_sql(sql, conn)

        # Step 3 — Generate chart
        chart = generate_chart(result, question)

        # Step 4 — Generate AI business insight
        insight = generate_insight(question, result)

        # Step 5 — Generate follow-up suggestions
        followups = generate_followups(question, result)

        # Build complete message object
        message = {
            "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "question": question,
            "sql": sql,
            "result": result,
            "chart": chart,
            "insight": insight,
            "followups": followups,
        }

        return message

    finally:
        conn.close()
