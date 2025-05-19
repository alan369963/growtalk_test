"""
vocab_session_controller.py

Orchestrates the entire conversational vocabulary training session:
- Starts session with a student based on training day and vocab index
- Guides student through scaffolded learning: ask → hint → explanation
- Tracks attempts, evaluates answers, and advances progress in Google Sheet
- Uses LLM to dynamically generate every teaching and feedback message

One session controller manages the full flow of one vocab word at a time per student.
"""

from sheet_utils import get_current_vocab_row, advance_vocab_index
from llm_utils import (
    ask_vocab_meaning_question,
    give_vocab_correct_reply,
    give_vocab_hint_or_explanation,
    evaluate_answer,
)
from whatsapp_utils import send_whatsapp_message

vocab_sessions = {}


def start_vocab_session(phone_number, sheet_user, sheet_vocab):
    vocab_row = get_current_vocab_row(sheet_user, sheet_vocab, phone_number)

    if vocab_row is None:
        send_whatsapp_message(phone_number, "🎉 你已經完成哂今日所有生字啦，做得好叻！")
        return

    message = ask_vocab_meaning_question(vocab_row)
    vocab_sessions[phone_number] = {"attempt": 1, "last_vocab": vocab_row}
    send_whatsapp_message(phone_number, f"{message}")


def handle_vocab_reply(phone_number, user_reply, sheet_user, sheet_vocab):
    session = vocab_sessions.get(phone_number)

    if not session:
        send_whatsapp_message(phone_number, "請先輸入 'vocab' 開始今日生字學習 ✍️")
        return

    vocab_row = session["last_vocab"]
    correct_answer = vocab_row["ChineseExplaination"]
    attempt = session["attempt"]

    is_correct = evaluate_answer(user_reply, correct_answer)

    if is_correct:
        msg = give_vocab_correct_reply(vocab_row)
        send_whatsapp_message(phone_number, msg)
        advance_vocab_index(sheet_user, phone_number)
        del vocab_sessions[phone_number]
        start_vocab_session(phone_number, sheet_user, sheet_vocab)
    else:
        if attempt == 1:
            msg = give_vocab_hint_or_explanation(vocab_row, attempt=1)
            vocab_sessions[phone_number]["attempt"] = 2
            send_whatsapp_message(phone_number, msg)
        else:
            msg = give_vocab_hint_or_explanation(vocab_row, attempt=2)
            advance_vocab_index(sheet_user, phone_number)
            del vocab_sessions[phone_number]
            send_whatsapp_message(phone_number, msg)
            start_vocab_session(phone_number, sheet_user, sheet_vocab)
