# ⚙️ How It Works

The AI CRM Analytics Assistant converts natural language questions into interactive business insights through a multi-step pipeline.

```text
User Question
      │
      ▼
AI SQL Generator (Groq LLM)
      │
      ▼
Generated SQLite Query
      │
      ▼
Execute Query on CRM Database
      │
      ▼
Retrieve Data
      │
      ▼
Interactive Visualization Engine
      │
      ▼
AI Business Insights Generator
      │
      ▼
Suggested Follow-up Questions
      │
      ▼
Interactive Chat Interface
```

## 1️⃣ User Query

Users ask business questions in natural language.

**Example:**

> Show the top 5 employees by revenue.

---

## 2️⃣ AI SQL Generation

The application sends the user's question, database schema, and recent conversation history to the Groq LLM.

The AI understands:

- Database schema
- Previous conversation
- Business context

It generates an optimized **SQLite SELECT query**.

---

## 3️⃣ SQL Execution

The generated SQL is executed against the CRM SQLite database.

The application retrieves only the requested data.

---

## 4️⃣ Visualization Engine

The returned dataframe is analyzed automatically.

The system intelligently selects the most suitable visualization based on:

- Number of columns
- Data types
- Date detection
- Percentage detection
- Numeric relationships
- Category cardinality

Supported visualizations include:

- 📊 Bar Charts
- 📈 Line Charts
- 🥧 Pie Charts
- 🍩 Donut Charts
- 📉 Horizontal Bar Charts
- 🔵 Scatter Plots

Users can further customize:

- Chart type
- Sorting
- Top N filter
- Orientation
- Color theme
- Value labels
- Legend visibility

Charts can also be exported as:

- PNG
- CSV
- Excel

---

## 5️⃣ AI Business Insights

The query result is analyzed by the LLM to generate business-focused insights, including:

- Executive Summary
- Key Findings
- Business Recommendations

This helps users understand the data rather than just viewing raw numbers.

---

## 6️⃣ Suggested Follow-up Questions

After every response, the AI suggests relevant follow-up questions.

Example:

- Compare with last month
- Show only active accounts
- Display revenue trend
- Top 10 opportunities

This enables a conversational analytics experience.

---

## 7️⃣ Conversation Memory

The assistant remembers recent interactions to support follow-up questions.

Example:

```
User:
Top employees by revenue

↓

User:
Only top 3

↓

User:
Compare with last month
```

The AI understands the context without requiring the user to repeat the original question.

---

## 8️⃣ Query History

Every analysis is stored during the session, including:

- Question
- Generated SQL
- Returned rows
- AI Insights
- Timestamp

Users can revisit previous analyses at any time.

---

## 9️⃣ Interactive Dashboard

The application also provides a CRM dashboard with key business metrics such as:

- Total Accounts
- Total Leads
- Opportunities
- Converted Leads
- Active Accounts
- Revenue
- Average Deal Size

This gives users an immediate overview of CRM performance.

---

## 🔧 Technologies Used

- **Frontend:** Streamlit
- **Database:** SQLite
- **LLM:** Groq (Llama 3.3)
- **Visualization:** Plotly
- **Data Processing:** Pandas
- **Environment Management:** python-dotenv
