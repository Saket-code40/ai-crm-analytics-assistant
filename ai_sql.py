from groq import Groq
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from schema import get_schema

# Load environment variables
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_sql(question, conversation):

    schema = get_schema()
    conversation_context = ""
    for chat in conversation:
        conversation_context += f"""
        Previous Question:
        {chat['question']}
        Generated SQL:
        {chat['sql']}
        Rows Returned:
        {chat['rows']}
        Business Insight:
        {chat['insight']}
        -------------------------
"""

    prompt = f"""
You are an expert SQLite Database Engineer and CRM Data Analyst.

Database Name:
crm.db

Database Schema:

{schema}

IMPORTANT RULES

1. Return ONLY valid SQLite SQL.
2. Never return markdown.
3. Never explain anything.
4. Never use ```sql.
5. Generate ONLY SELECT queries.
6. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, ATTACH or DETACH statements.
7. Use exact table names.
8. Use exact column names.
9. Use JOIN whenever data is spread across multiple tables.
10. Use aliases (a, l, o) whenever joins are required.

----------------------------------------------------

Visualization Rules

A) Distribution Questions

Examples:
- account status distribution
- account type distribution
- lead source distribution

Return EXACTLY TWO columns:

<Category>, <Count>

Example:

SELECT account_status,
COUNT(*) AS total
FROM account_analytics
GROUP BY account_status;

----------------------------------------------------

B) Trend Questions

Examples:

- monthly
- yearly
- daily
- growth
- trend
- over time

Return EXACTLY TWO columns:

<Time>, <Value>

Example:

SELECT created_year,
COUNT(*) AS total
FROM lead_analytics
GROUP BY created_year
ORDER BY created_year;

----------------------------------------------------

C) Ranking Questions

Examples:

- top
- highest
- lowest
- ranking
- best
- most
- least

Return EXACTLY TWO columns:

<Category>, <Metric>

Example:

SELECT employee_name,
COUNT(*) AS total_accounts
FROM account_analytics
GROUP BY employee_name
ORDER BY total_accounts DESC;

----------------------------------------------------

D) Listing Questions

Return only the necessary columns.

Never use SELECT *.

----------------------------------------------------

JOIN RULES

If information belongs to multiple tables,
generate JOIN queries automatically.

Example:

SELECT
l.lead_source,
SUM(o.amount) AS total_amount
FROM lead_analytics l
JOIN opportunity_analytics o
ON l.lead_source = o.lead_source
GROUP BY l.lead_source
ORDER BY total_amount DESC;

----------------------------------------------------

Always generate optimized SQLite SQL.
----------------------------------------------------

DATE HANDLING RULES

All date columns (created_date, modified_date, date_closed,
next_followup_date, date_entered) are stored in YYYY-MM-DD format.

Always use SQLite DATE() and STRFTIME() functions.

When the user asks:

• Today

WHERE date_column = DATE('now')

• Yesterday

WHERE date_column = DATE('now','-1 day')

• This Month

WHERE date_column >= DATE('now','start of month')

• Last Month

WHERE date_column >= DATE('now','start of month','-1 month')
AND date_column < DATE('now','start of month')

• This Year

WHERE STRFTIME('%Y', date_column) = STRFTIME('%Y','now')

• Last Year

WHERE STRFTIME('%Y', date_column) =
CAST(STRFTIME('%Y','now') AS INTEGER) - 1

Never compare years using

STRFTIME('%Y','now') - 1

Always cast to INTEGER first.

----------------------------------------------------

CONVERSATION HISTORY

{conversation_context}

----------------------------------------------------

FOLLOW-UP QUESTION RULES

If the current question refers to a previous question using words like:

- this
- that
- these
- those
- it
- its
- they
- them
- compare
- only
- same
- above
- previous
- last
- earlier

Use the conversation history to understand the user's intent.

Do NOT ignore previous context.

If the current question is completely unrelated,
ignore the conversation history and answer normally.

----------------------------------------------------

Current User Question:

{question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    sql = response.choices[0].message.content

    # Clean response
    sql = (
        sql.replace("```sql", "")
           .replace("```", "")
           .strip()
    )

    print("\n========== GENERATED SQL ==========")
    print(sql)
    print("===================================\n")

    # ----------------------------
    # SECURITY CHECK
    # ----------------------------

    # Only SELECT queries are allowed
    if not sql.upper().startswith("SELECT"):
        raise Exception("Only SELECT queries are allowed.")

    # Prevent multiple SQL statements
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    if len(statements) > 1:
        raise Exception("Multiple SQL statements are not allowed.")

    # Remove trailing semicolon
    sql = statements[0]

    return sql