from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_insight(question, dataframe):

    prompt = f"""
You are a Senior CRM Business Analyst.

User Question:
{question}

SQL Result:

{dataframe.to_string(index=False)}

Write:

1. Executive Summary

2. Key Insights

3. Business Recommendations

Keep it concise and business-focused.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response.choices[0].message.content