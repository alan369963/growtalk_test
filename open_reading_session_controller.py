from sheet_utils import get_open_question, advance_open_question_progress
from whatsapp_utils import send_whatsapp_message
from llm_utils import (
    respond_to_open_answer,
    is_reply_relevant_to_learning,
    generate_answer_to_student_question,
)

open_reading_sessions = {}


def start_open_reading_session(phone_number, sheet_user, sheet_open_reading):
    question = get_open_question(sheet_user, sheet_open_reading, phone_number)
    open_reading_sessions[phone_number] = {"question": question}
    send_whatsapp_message(phone_number, f"📝 開放式問題：\n{question}")


def handle_open_reading_reply(phone_number, user_reply, sheet_user, sheet_open_reading):
    if phone_number not in open_reading_sessions:
        send_whatsapp_message(phone_number, "請先輸入 'reflect' 開始開放式閱讀任務 ✍️")
        return

    question = open_reading_sessions[phone_number]["question"]

    if not is_reply_relevant_to_learning(user_reply, question):
        send_whatsapp_message(
            phone_number, "呢個問題好有趣，但不如我哋先集中討論文章內容 😄"
        )
        return

    # Generate LLM response to the student's interpretation
    reply = respond_to_open_answer(user_reply, question)
    send_whatsapp_message(phone_number, reply)

    # Move to next open question
    advance_open_question_progress(sheet_user, phone_number)
    del open_reading_sessions[phone_number]
    start_open_reading_session(phone_number, sheet_user, sheet_open_reading)
