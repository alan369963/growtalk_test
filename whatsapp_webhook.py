"""
whatsapp_webhook.py

FastAPI application that receives WhatsApp messages from the Node.js bot and
routes them into the appropriate training session (vocab, reading, etc.).

Core responsibilities:
- Log and store incoming messages
- Match student messages to training functions (e.g., start vocab)
- Maintain separation between input reception and logic execution

This serves as the bridge from WhatsApp to Python.
"""

# Run in Terminal
# uvicorn whatsapp_webhook:app --reload --port 8000

# Run in another Terminal
# cd whatsapp bot
# node .\index.js

from fastapi import FastAPI, Request
import uvicorn
from llm_utils import (
    generate_answer_to_student_question,
    greet_student,
    is_reply_relevant_to_learning,
    is_student_answering_question,
)
from sheet_utils import connect_to_sheet, get_student_name_by_phone
from vocab_session_controller import start_vocab_session, handle_vocab_reply
from whatsapp_utils import send_whatsapp_message, last_sent_messages
from reading_session_controller import (
    start_reading_session,
    handle_reading_reply,
    reading_sessions,
)
from open_reading_session_controller import (
    start_open_reading_session,
    handle_open_reading_reply,
    open_reading_sessions,
)


app = FastAPI()

user_sheet = connect_to_sheet("User List", "Sheet1")
reading_sheet = connect_to_sheet("Question List", "reading_close_end")
vocab_sheet = connect_to_sheet("Question List", "vocab")


@app.post("/receive-whatsapp")
async def receive_message(request: Request):
    data = await request.json()
    phone_number = data["phone_number"]
    message = data["message"].strip().lower()
    student_name = get_student_name_by_phone(user_sheet, phone_number)

    print(f"📥 Received message from {phone_number}: {message}")

    if "start" in message:
        print("💬 Greeting student...")
        greet = greet_student(student_name)
        send_whatsapp_message(phone_number, greet)

    elif "vocab" in message:
        print("🧠 Starting vocab session...")
        start_vocab_session(phone_number, user_sheet, vocab_sheet)

    elif "reading" in message:
        print("📘 Starting reading session...")
        start_reading_session(phone_number, user_sheet, reading_sheet)

    elif "reflect" in message:
        print("🪞 Starting open-ended reading session...")
        start_open_reading_session(phone_number, user_sheet, reading_sheet)

    elif phone_number in open_reading_sessions:
        handle_open_reading_reply(phone_number, message, user_sheet, reading_sheet)

    elif phone_number in reading_sessions:
        handle_reading_reply(phone_number, message, user_sheet, reading_sheet)

    else:
        print("📚 Unrecognized input")
        question_prompt = last_sent_messages
        # Check if the student actually trying to answer?
        if is_student_answering_question(message, question_prompt):
            handle_vocab_reply(phone_number, message, user_sheet, vocab_sheet)
            return
        # If student is not answering but question still related to English/learning?
        elif is_reply_relevant_to_learning(message, question_prompt):
            response = generate_answer_to_student_question(message)
            send_whatsapp_message(phone_number, response)
            start_vocab_session(phone_number, user_sheet, vocab_sheet)
            return
        # If studnet is not answering the question & the reply is not relevant to English learning → gently decline
        else:
            send_whatsapp_message(
                phone_number, "呢個問題好有趣，不過我哋而家專心學英文先啦 😊"
            )
            start_vocab_session(phone_number, user_sheet, vocab_sheet)
            return

    return {"status": "received"}
