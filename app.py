import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

from utils.rag_utils import search_similar
from utils.sentiment_analyzer import analyze_sentiment
from utils.email_generator import generate_email_response
from utils.ocr_utils import extract_text_from_image
from utils.intent_classifier import classify_intent

from database.db import init_db, create_ticket, add_message
from dotenv import load_dotenv

LOGS_DIR = "logs"
LOG_FILE = os.path.join(LOGS_DIR, "interactions.jsonl")


def setup_environment() -> None:
    load_dotenv()
    os.makedirs(LOGS_DIR, exist_ok=True)
    init_db()
    print("[INIT] Environment setup complete.")


def log_interaction(record: Dict[str, Any]) -> None:
    record_with_meta = {
        "timestamp": datetime.utcnow().isoformat(),
        **record,
    }

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record_with_meta, ensure_ascii=False) + "\n")
    except:
        pass


def support_pipeline(
    query_text: str,
    source_type: str = "text",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    
    if metadata is None:
        metadata = {}

    # Step 1 — Intent Classification
    intent = classify_intent(query_text)

    # Step 2 — RAG Search
    kb_results = search_similar(query_text, top_k=2)
    context = "\n".join(kb_results)

    # Step 3 — Sentiment + Agent Decision
    sentiment = analyze_sentiment(query_text)

    if sentiment == "negative" or intent == "complaint":
        action = "escalate_to_human_support"
    elif intent in ["order_status", "refund_request", "technical_issue", "payment_issue"]:
        action = "auto_reply"
    else:
        action = "request_more_details"

    # Step 4 — Language Preference
    preferred_lang = metadata.get("language_preference", "English")

    # Step 5 — Email Response Generation
    response_email = generate_email_response(
        user_query=query_text,
        intent=intent,
        context=context,
        preferred_lang=preferred_lang
    )

    # Step 6 — DB Ticket + Messages
    ticket_id = create_ticket(
        user_id="guest_user",
        intent=intent,
        sentiment=sentiment,
        action=action
    )
    
    add_message(ticket_id, "user", query_text)
    add_message(ticket_id, "assistant", response_email)

    # Results back to UI
    result = {
        "ticket_id": ticket_id,
        "source_type": source_type,
        "query_text": query_text,
        "metadata": metadata,
        "intent": intent,
        "agent_action": action,
        "retrieved_context": kb_results,
        "response_email": response_email,
        "sentiment": sentiment,
    }

    log_interaction(result)

    return result


def handle_text_query() -> None:
    print("\n=== Text Query Mode ===")
    query = input("Enter customer message: ").strip()
    if not query: return
    
    result = support_pipeline(query_text=query, source_type="text")
    print(result["response_email"])


def handle_image_query() -> None:
    print("\n=== Image Query Mode ===")
    image_path = input("Enter image path: ")
    if not os.path.isfile(image_path):
        print("Incorrect path.")
        return
    
    ex = extract_text_from_image(image_path)
    print("[OCR OUTPUT]:", ex)

    result = support_pipeline(ex, source_type="image", metadata={"image_path": image_path})
    print(result["response_email"])


def main_menu() -> None:
    while True:
        print("\n1. Text Query\n2. Image Query\n3. Exit")
        c = input("Select (1/2/3): ").strip()
        if c == "1": handle_text_query()
        elif c == "2": handle_image_query()
        elif c == "3": break
        else: print("Invalid choice")


if __name__ == "__main__":
    setup_environment()
    main_menu()
