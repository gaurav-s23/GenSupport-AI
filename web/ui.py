import streamlit as st
import os
import sys
import tempfile

# Make backend importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import support_pipeline
from utils.ocr_utils import extract_text_from_image
from database.db import get_all_tickets, get_ticket_messages
from utils.email_generator import detect_language


# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="GenSupport AI - Support System",
    layout="wide",
)

st.title("🤖 GenSupport AI - Support System")

# ---------- SESSION STATE INIT ----------

# Chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Free trial usage count
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

# Maximum free AI calls per session
MAX_FREE_TRIAL = 2

# Language state
if "language_preference" not in st.session_state:
    st.session_state.language_preference = None  # "english" / "hindi" / "hinglish"

if "await_lang_confirm" not in st.session_state:
    st.session_state.await_lang_confirm = False

if "detected_lang" not in st.session_state:
    st.session_state.detected_lang = "english"


# ---------- SIDEBAR MODE ----------
mode = st.sidebar.radio(
    "Choose Mode",
    ["💬 Chat Support", "📊 Admin Dashboard"],
    index=0
)


# =============== CHAT SUPPORT MODE ==================
if mode == "💬 Chat Support":

    st.subheader("💬 Chat with GenSupport AI")

    # Helper to add messages into history
    def add_to_chat(role: str, message: str, meta: dict | None = None):
        meta = meta or {}
        st.session_state.chat_history.append(
            {"role": role, "message": message, **meta}
        )

    # Show existing chat
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.chat_message("user").markdown(chat["message"])
        else:
            # Assistant message
            with st.chat_message("assistant"):
                st.markdown(chat["message"])
                # Meta understanding block
                meta_lines = []
                sentiment_icon = "😐"
                if chat.get("sentiment") == "positive":
                    sentiment_icon = "🙂"
                elif chat.get("sentiment") == "negative":
                    sentiment_icon = "😡"

                if chat.get("intent"):
                    meta_lines.append(f"**Intent:** `{chat['intent']}`")
                if chat.get("sentiment"):
                    meta_lines.append(f"**Sentiment:** {sentiment_icon} `{chat['sentiment']}`")
                if chat.get("agent_action"):
                    meta_lines.append(f"**Agent Action:** `{chat['agent_action']}`")
                if chat.get("ticket_id"):
                    meta_lines.append(f"**Ticket ID:** `{chat['ticket_id']}`")

                if meta_lines:
                    with st.expander("🧠 AI Understanding"):
                        st.markdown("\n\n".join(meta_lines))

    # Inputs
    user_input = st.chat_input("Type your query...")
    uploaded_image = st.file_uploader(
        "📷 Upload screenshot (optional)",
        type=["jpg", "jpeg", "png"],
        key="chat_image_upload",
    )

    # ------------- NEW MESSAGE HANDLING --------------
    if user_input or uploaded_image:

        # FREE TRIAL LIMIT CHECK
        if st.session_state.usage_count >= MAX_FREE_TRIAL:
            st.error("⚠️ Free Trial limit reached! Contact support to unlock full access.")
            st.stop()

        # Determine final query text
        if uploaded_image:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(uploaded_image.read())
                img_path = tmp.name
            extracted_text = extract_text_from_image(img_path)
            final_query = extracted_text or "[No text detected from image]"
            add_to_chat("user", f"📷 (Image OCR)\n{final_query}")
        else:
            final_query = user_input
            add_to_chat("user", final_query)

        # If language not chosen yet → detect and ask
        if st.session_state.language_preference is None:
            detected = detect_language(final_query).lower()
            st.session_state.detected_lang = detected
            st.session_state.await_lang_confirm = True
            st.rerun()
        else:
            # We already know language → call AI directly
            with st.spinner("🤖 Processing your request..."):
                result = support_pipeline(
                    query_text=final_query,
                    source_type="chat_ui",
                    metadata={"language_preference": st.session_state.language_preference},
                )

            st.session_state.usage_count += 1

            add_to_chat(
                "assistant",
                result["response_email"],
                meta={
                    "intent": result.get("intent"),
                    "sentiment": result.get("sentiment"),
                    "agent_action": result.get("agent_action"),
                    "ticket_id": result.get("ticket_id"),
                },
            )

            st.rerun()

    # ------------- LANGUAGE CONFIRMATION UI --------------
    if st.session_state.await_lang_confirm and st.session_state.language_preference is None:
        st.warning("🌍 Which language should GenSupport AI reply in?")

        detected = st.session_state.detected_lang
        if "hindi" in detected:
            options = ["Hindi", "Hinglish", "English"]
        else:
            options = ["English", "Hindi", "Hinglish"]

        chosen_lang = st.radio("Select language:", options)

        if st.button("Confirm Language"):
            st.session_state.language_preference = chosen_lang.lower()
            st.session_state.await_lang_confirm = False

            # After confirming language, answer the last user message
            # Find last user message
            last_user_message = None
            for chat in reversed(st.session_state.chat_history):
                if chat["role"] == "user":
                    last_user_message = chat["message"]
                    break

            if last_user_message is not None:
                if st.session_state.usage_count >= MAX_FREE_TRIAL:
                    st.error("⚠️ Free Trial limit reached! Contact support to unlock full access.")
                    st.stop()

                # Remove OCR label if present
                if last_user_message.startswith("📷 (Image OCR)\n"):
                    query_text = last_user_message.replace("📷 (Image OCR)\n", "", 1).strip()
                else:
                    query_text = last_user_message

                with st.spinner("🤖 Processing your request..."):
                    result = support_pipeline(
                        query_text=query_text,
                        source_type="chat_ui",
                        metadata={"language_preference": st.session_state.language_preference},
                    )

                st.session_state.usage_count += 1

                add_to_chat(
                    "assistant",
                    result["response_email"],
                    meta={
                        "intent": result.get("intent"),
                        "sentiment": result.get("sentiment"),
                        "agent_action": result.get("agent_action"),
                        "ticket_id": result.get("ticket_id"),
                    },
                )

            st.success(f"Language set to: {chosen_lang}")
            st.rerun()


# =============== ADMIN DASHBOARD MODE ==================
elif mode == "📊 Admin Dashboard":
    st.subheader("📊 Admin Dashboard - Tickets & Conversations")

    tickets = get_all_tickets()

    if not tickets:
        st.info("No tickets found yet. Interact with the chat to create some tickets.")
    else:
        import pandas as pd

        col1, col2 = st.columns([2, 3])

        with col1:
            st.markdown("### All Tickets")
            df = pd.DataFrame(tickets)
            st.dataframe(df)

            ticket_ids = [t["ticket_id"] for t in tickets]
            selected_id = st.selectbox("Select Ticket ID", ticket_ids)

        with col2:
            st.markdown(f"### 🎟 Ticket #{selected_id} Details")
            ticket = next(t for t in tickets if t["ticket_id"] == selected_id)

            st.markdown(f"**User ID:** `{ticket['user_id']}`")
            st.markdown(f"**Intent:** `{ticket['intent']}`")
            st.markdown(f"**Sentiment:** `{ticket['sentiment']}`")
            st.markdown(f"**Agent Action:** `{ticket['agent_action']}`")
            st.markdown(f"**Created At:** `{ticket['created_at']}`")

            st.markdown("---")
            st.markdown("### 💬 Conversation History")

            messages = get_ticket_messages(selected_id)
            if not messages:
                st.write("_No messages found for this ticket._")
            else:
                for msg in messages:
                    role = "user" if msg["sender"] == "user" else "assistant"
                    with st.chat_message(role):
                        st.markdown(msg["message"])
                        st.caption(msg["timestamp"])
