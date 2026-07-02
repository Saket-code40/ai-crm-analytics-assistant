import sqlite3
import pandas as pd
import plotly.express as px

from ai_sql import generate_sql

# ----------------------------
# Connect Database
# ----------------------------

conn = sqlite3.connect("crm.db")

# ----------------------------
# Ask User
# ----------------------------

question = input("\nAsk your CRM: ")

# ----------------------------
# Generate SQL
# ----------------------------

sql = generate_sql(question)

print("\n========== GENERATED SQL ==========\n")
print(sql)

# ----------------------------
# Execute SQL
# ----------------------------

try:

    result = pd.read_sql(sql, conn)

    print("\n========== RESULT ==========\n")
    print(result)

    # -----------------------------------------
    # No data
    # -----------------------------------------

    if result.empty:
        print("\nNo data found.")

    # -----------------------------------------
    # TWO COLUMNS
    # -----------------------------------------

    elif len(result.columns) == 2:

        x_col = result.columns[0]
        y_col = result.columns[1]

        if pd.api.types.is_numeric_dtype(result[y_col]):

            q = question.lower()

            # Pie Chart
            if any(word in q for word in [
                "distribution",
                "share",
                "percentage",
                "pie"
            ]):

                fig = px.pie(
                    result,
                    names=x_col,
                    values=y_col,
                    title=question
                )

            # Line Chart
            elif any(word in q for word in [
                "trend",
                "growth",
                "month",
                "year",
                "daily",
                "time"
            ]):

                fig = px.line(
                    result,
                    x=x_col,
                    y=y_col,
                    markers=True,
                    title=question
                )

            # Default Bar Chart
            else:

                fig = px.bar(
                    result,
                    x=x_col,
                    y=y_col,
                    title=question,
                    text_auto=True
                )

            fig.show()

    # -----------------------------------------
    # THREE COLUMNS
    # -----------------------------------------

    elif len(result.columns) == 3:

        x_col = result.columns[0]
        color_col = result.columns[1]
        y_col = result.columns[2]

        if pd.api.types.is_numeric_dtype(result[y_col]):

            q = question.lower()

            # Multi-line Trend
            if any(word in q for word in [
                "trend",
                "growth",
                "month",
                "year"
            ]):

                fig = px.line(
                    result,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    markers=True,
                    title=question
                )

            # Grouped Bar Chart
            else:

                fig = px.bar(
                    result,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    barmode="group",
                    title=question,
                    text_auto=True
                )

            fig.show()

    # -----------------------------------------
    # MORE THAN 3 COLUMNS
    # -----------------------------------------

    else:

        print("\nChart skipped (More than 3 columns returned).")

except Exception as e:

    print("\nExecution Error:")
    print(e)

finally:

    conn.close()

# -------------------------------------
# Generate AI Insights    
#-------------------------------------

from ai_insights import generate_insight

print("\nGenerating AI Insights...\n")

insight = generate_insight(question, result)

print(insight)