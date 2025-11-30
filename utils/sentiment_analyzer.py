import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

SENTIMENT_CATEGORIES = ["positive", "neutral", "negative"]

def analyze_sentiment(text: str) -> str:
    prompt = f"""
    Analyze the sentiment of this customer message.
    Only respond with one word: {", ".join(SENTIMENT_CATEGORIES)}

    Message: {text}
    """

    try:
        response = model.generate_content(prompt)
        sentiment = response.text.strip().lower()

        if sentiment not in SENTIMENT_CATEGORIES:
            return "neutral"

        return sentiment

    except Exception as e:
        print(f"[Sentiment Error] {e}")
        return "neutral"
