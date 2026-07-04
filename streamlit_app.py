import pandas as pd
import streamlit as st
import plotly.express as px
from kpi import get_kpis
from datetime import datetime
from followup import generate_followups
from ai_sql import generate_sql
from ai_insights import generate_insight
from chat_utils import process_question
from chart_panel import render_chart_panel
from database_manager import get_connection

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

if "auto_analyze" not in st.session_state:
    st.session_state.auto_analyze = False

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

    # ----------------------------------
    # Recent Chats — dynamically built
    # ----------------------------------
    recent_questions = [
        msg["question"] for msg in st.session_state.messages
    ]
    if recent_questions:
        st.markdown("---")
        st.subheader("💬 Recent Chats")
        for i, q in enumerate(reversed(recent_questions)):
            if st.button(
                q,
                key=f"recent_{i}",
                use_container_width=True,
                icon="💬"
            ):
                st.session_state.next_question = q
                st.session_state.auto_analyze = False
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
# Ask AI Page — Conversational UI
# =====================================

elif page == "Ask AI":

    st.header("🤖 Ask Your CRM")

    # ------------------------------------------
    # Handle incoming question (from followup/recent chat).
    # We write directly into the widget's keyed state so
    # st.text_input() picks it up on this rerun.
    # ------------------------------------------
    if "next_question" in st.session_state:
        st.session_state.chat_input = st.session_state.next_question
        del st.session_state.next_question

    # ------------------------------------------
    # Question input — uses keyed state (chat_input)
    # so follow-ups can pre-fill it reliably.
    # ------------------------------------------
    question = st.text_input(
        "Ask your CRM",
        placeholder="Example: Show opportunity amount by sales stage",
        key="chat_input"
    )

    # ------------------------------------------
    # Helper: store a processed message in all
    # required session state structures
    # ------------------------------------------
    def _store_message(message):
        """Persist a message in messages, history, and conversation memory."""
        # Main message list (used for rendering)
        st.session_state.messages.append(message)

        # History (used by Query History page)
        st.session_state.history.append({
            "time": message["time"],
            "question": message["question"],
            "sql": message["sql"],
            "rows": len(message["result"]),
            "result": message["result"].to_dict("records"),
            "insight": message["insight"],
        })

        # Conversation memory (last 5 — sent to LLM for context)
        st.session_state.conversation.append({
            "question": message["question"],
            "sql": message["sql"],
            "rows": len(message["result"]),
            "result": message["result"].head(5).to_dict("records"),
            "insight": message["insight"],
        })
        if len(st.session_state.conversation) > 5:
            st.session_state.conversation.pop(0)

    # ------------------------------------------
    # Auto-analyze (triggered by follow-up clicks)
    # ------------------------------------------
    if st.session_state.auto_analyze and question.strip():
        st.session_state.auto_analyze = False

        try:
            with st.spinner("🧠 Generating SQL..."):
                message = process_question(
                    question,
                    st.session_state.conversation
                )

            _store_message(message)

            # Force a rerun to show the new message immediately
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")

    # ------------------------------------------
    # Manual Analyze button
    # ------------------------------------------
    if st.button("🚀 Analyze", key="analyze_btn"):
        if question.strip():
            try:
                with st.spinner("🧠 Analyzing your question..."):
                    message = process_question(
                        question,
                        st.session_state.conversation
                    )

                _store_message(message)

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("Please enter a question first.")

    # ------------------------------------------
    # Display all messages — ChatGPT style
    # ------------------------------------------
    for message in st.session_state.messages:

        # --- User bubble ---
        with st.chat_message("user"):
            st.markdown(message["question"])

        # --- AI response bubble ---
        with st.chat_message("assistant"):

            # 1) Generated SQL (collapsible expander)
            with st.expander("💻 Generated SQL", expanded=False):
                st.code(message["sql"], language="sql")

            # 2) Result Table
            st.markdown("#### 📊 Result Table")
            st.dataframe(
                message["result"],
                use_container_width=True,
                hide_index=True
            )

            # 3) Interactive Visualization Panel
            if message["chart"] is not None:
                render_chart_panel(
                    result=message["result"],
                    question=message["question"],
                    msg_time=message["time"]
                )
            # 4) Business Insights
            st.markdown("#### 🤖 Business Insights")
            st.markdown(message["insight"])

            # 5) Suggested Follow-up Questions
            if message.get("followups"):
                st.markdown("#### 💡 Suggested Follow-up Questions")
                cols = st.columns(len(message["followups"]))
                for i, q in enumerate(message["followups"]):
                    with cols[i]:
                        if st.button(
                            q,
                            key=f"followup_{message['time']}_{i}",
                            use_container_width=True
                        ):
                            st.session_state.next_question = q
                            st.session_state.auto_analyze = True
                            st.rerun()
# =====================================
# Analytics Page
# =====================================

elif page == "Analytics":

    st.header("📊 Analytics Dashboard")

    conn = get_connection()


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