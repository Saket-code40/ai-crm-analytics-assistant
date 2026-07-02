from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_followups(question, result):

    prompt = f"""
You are a CRM Business Analyst.

The user asked:

{question}

Based on this question and its result, suggest exactly 5 useful follow-up questions.

Rules:
- Only return questions.
- One question per line.
- No numbering.
- Keep each question under 10 words.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    questions = response.choices[0].message.content.split("\n")

    return [q.strip("- ").strip() for q in questions if q.strip()]