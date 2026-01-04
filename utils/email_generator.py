import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Latest Stable Model
model = genai.GenerativeModel("gemini-2.5-flash")


def detect_language(text: str) -> str:
    """
    Detect language for first incoming user message
    """
    prompt = f"Detect language for this text. Respond only language name:\n{text}"
    response = model.generate_content(prompt)
    return response.text.lower().strip()


def generate_email_response(
    user_query: str,
    intent: str,
    context: str,
    preferred_lang: str = "English"
) -> str:
    
    # Language format
    if preferred_lang.lower().startswith("hi"):
        lang_instruction = "Write response fully in Hindi. Use polite, customer-care tone."
    elif preferred_lang.lower().startswith("hing"):
        lang_instruction = "Write response in Hinglish (Hindi+English mix), friendly tone."
    else:
        lang_instruction = "Write response in English with professional tone."

    prompt = f"""
You are a helpful, professional customer support assistant.

Customer Query:
{user_query}

Issue Type:
{intent}

Relevant Help Info:
{context}

{lang_instruction}

Rules:
- 2 short paragraphs only
- Be empathetic & positive
- Add steps / solution guidance if applicable
- DO NOT mention AI, knowledge base, intent classification, sentiment etc.
- Close email with:
Best Regards,
GenSupport AI Support Team
"""

    response = model.generate_content(prompt)
    return response.text.strip()
