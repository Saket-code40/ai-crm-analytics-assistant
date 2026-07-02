import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from kpi import get_kpis
from datetime import datetime
from followup import generate_followups
from ai_sql import generate_sql
from ai_insights import generate_insight

# -----------------------------
# Page Config
# -----------------------------

st.set_page_config(
    page_title="AI CRM Analytics",
    page_icon="📊",
    layout="wide"
)
# =====================================
# Session State
# =====================================
if "question" not in st.session_state:
    st.session_state.question = ""

if "sql" not in st.session_state:
    st.session_state.sql = None

if "result" not in st.session_state:
    st.session_state.result = None

if "insight" not in st.session_state:
    st.session_state.insight = None

if "history" not in st.session_state:
    st.session_state.history = []

if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "messages" not in st.session_state:
    st.session_state.messages = []

# =====================================
# Sidebar
# =====================================

with st.sidebar:

    st.title("🤖 AI CRM")

    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Ask AI",
            "Analytics",
            "Query History",
            "Settings"
        ]
    )

    st.markdown("---")

    st.subheader("💡 Suggested Questions")

    suggestions = [
        "Show account status distribution",
        "Top employees by accounts",
        "Show converted leads by month",
        "Lead source distribution",
        "Opportunity amount by sales stage",
        "Top lead sources by opportunity amount",
        "Compare account type with lead source",
        "Average opportunity amount"
    ]

    for i, q in enumerate(suggestions):
        if st.button(
            q,
            key=f"suggestion_{i}",
            use_container_width=True
    ):
            st.session_state.next_question = q
            st.rerun()
            st.markdown("---")

    st.success("🟢 Database Connected")
    st.write("SQLite")
    st.write("Tables: 3")

    st.markdown("---")

    st.caption("AI CRM Analytics v1.0")

# -----------------------------
# Title
# -----------------------------

st.title("🤖 AI CRM Analytics Assistant")

st.caption(
    "Ask questions about Accounts, Leads and Opportunities using natural language."
)
# =====================================
# Dashboard Page
# =====================================

if page == "Dashboard":

    kpi = get_kpis()

    st.subheader("📊 CRM Dashboard")

    # First Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📁 Accounts",
            f"{kpi['accounts']:,}"
        )

    with col2:
        st.metric(
            "👥 Leads",
            f"{kpi['leads']:,}"
        )

    with col3:
        st.metric(
            "💼 Opportunities",
            f"{kpi['opportunities']:,}"
        )

    with col4:
        st.metric(
            "✅ Converted",
            f"{kpi['converted']:,}"
        )

    # Second Row
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric(
            "🟢 Active Accounts",
            f"{kpi['active']:,}"
        )

    with col6:
        st.metric(
            "🔴 Inactive Accounts",
            f"{kpi['inactive']:,}"
        )

    with col7:
        st.metric(
            "💰 Revenue",
            f"₹{kpi['revenue']:,.0f}"
        )

    with col8:
        st.metric(
            "📈 Avg Deal Size",
            f"₹{kpi['avg_deal']:,.0f}"
        )

    st.divider()

# =====================================
# Ask AI Page
# =====================================

elif page == "Ask AI":

    st.header("🤖 Ask Your CRM")

    if "next_question" in st.session_state:
        st.session_state.question = st.session_state.next_question
        del st.session_state.next_question

    question = st.text_input(
        "Ask your CRM",
        value=st.session_state.question,
        placeholder="Example: Show opportunity amount by sales stage"
    )

    st.session_state.question = question

    # ========================
    # Helper Functions
    # ========================

    def generate_chart(result, question):
        """Generate appropriate chart based on result columns and question."""
        fig = None
        
        if len(result.columns) == 2:
            x = result.columns[0]
            y = result.columns[1]

            if pd.api.types.is_numeric_dtype(result[y]):
                q = question.lower()

                if any(word in q for word in ["distribution", "share", "percentage"]):
                    fig = px.pie(
                        result,
                        names=x,
                        values=y,
                        title=question
                    )

                elif any(word in q for word in ["month", "year", "trend", "growth"]):
                    fig = px.line(
                        result,
                        x=x,
                        y=y,
                        markers=True,
                        title=question
                    )

                else:
                    fig = px.bar(
                        result,
                        x=x,
                        y=y,
                        text_auto=True,
                        title=question
                    )

        elif len(result.columns) == 3:
            x = result.columns[0]
            color = result.columns[1]
            y = result.columns[2]

            if pd.api.types.is_numeric_dtype(result[y]):
                fig = px.bar(
                    result,
                    x=x,
                    y=y,
                    color=color,
                    barmode="group",
                    title=question
                )

        return fig

    # -----------------------------
    # Analyze Button
    # -----------------------------

    if st.button("🚀 Analyze"):

        conn = sqlite3.connect("crm.db")

        try:

            with st.spinner("Generating SQL..."):
                sql = generate_sql(
                    question,
                    st.session_state.conversation
                )

            result = pd.read_sql(sql, conn)

            with st.spinner("Generating AI Insights..."):
                insight = generate_insight(question, result)

            # Generate chart
            chart = generate_chart(result, question)

            # Generate followups
            followups = generate_followups(question, result)

            # Create complete message object
            message = {
                "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "question": question,
                "sql": sql,
                "result": result,
                "chart": chart,
                "insight": insight,
                "followups": followups
            }

            # Append to messages
            st.session_state.messages.append(message)

            # Update history for backwards compatibility
            st.session_state.history.append({
                "time": message["time"],
                "question": question,
                "sql": sql,
                "rows": len(result),
                "result": result.to_dict("records"),
                "insight": insight
            })

            # Update conversation memory
            st.session_state.conversation.append({
                "question": question,
                "sql": sql,
                "rows": len(result),
                "result": result.head(5).to_dict("records"),
                "insight": insight
            })
            if len(st.session_state.conversation) > 5:
                st.session_state.conversation.pop(0)

        except Exception as e:
            st.error(e)

        finally:
            conn.close()

    # -----------------------
    # Display Messages
    # -----------------------

    if st.session_state.messages:
        for message in st.session_state.messages:
            with st.container(border=True):
                st.markdown(f"**Question:** {message['question']}")
                
                # Display chart if available
                if message["chart"] is not None:
                    st.plotly_chart(message["chart"], use_container_width=True)
                
                # Display insight
                st.subheader("🤖 AI Business Insights")
                st.write(message["insight"])
                
                # Display followup questions
                st.subheader("💡 Suggested Follow-up Questions")
                for i, q in enumerate(message["followups"]):
                    if st.button(q, key=f"followup_{message['time']}_{i}"):
                        st.session_state.next_question = q
                        st.rerun()
# =====================================
# Analytics Page
# =====================================

elif page == "Analytics":

    st.header("📊 Analytics Dashboard")

    conn = sqlite3.connect("crm.db")


# =====================================
# Query History
# =====================================

elif page == "Query History":

    st.header("📜 Query History")

    if len(st.session_state.history) == 0:
        st.info("No queries yet.")
    
    else:
        for item in reversed(st.session_state.history):
            with st.expander(
            f"{item['time']} • {item['question']}"
        ):
                st.markdown("### ❓ Question")
                st.write(item["question"])
                st.markdown("### 📊 Rows Returned")
                st.write(item["rows"])
                st.markdown("### 💻 Generated SQL")
                st.code(item["sql"], language="sql")
                st.markdown("### 🤖 AI Insight")
                st.write(item.get("insight", "No AI Insight available."))
    if st.button("Clear History"):
        st.session_state.history = []
        st.success("Query history cleared.")

# =====================================
# Settings
# =====================================

elif page == "Settings":

    st.header("⚙️ Settings")
    st.info("Coming Soon")