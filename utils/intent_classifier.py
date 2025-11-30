import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment FIRST
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

INTENT_OPTIONS = [
    "order_status",
    "refund_request",
    "technical_issue",
    "payment_issue",
    "complaint",
    "general_query",
    "unknown"
]

def classify_intent(query: str) -> str:
    prompt = f"""
You are an AI intent classifier for customer support.

Classify the following message into ONLY ONE of these categories:
{", ".join(INTENT_OPTIONS)}

Message:
{query}

Return ONLY the category word.
"""

    try:
        response = model.generate_content(prompt)
        intent_raw = response.text.strip().lower()
        intent = re.sub(r"[^a-z_]", "", intent_raw)

        if intent not in INTENT_OPTIONS:
            
            return "unknown"

       
        return intent

    except Exception as e:
        print(f"[Intent Classifier Error] {e}")
        return "unknown"
