from sheet_utils import (
    get_passage,
    get_current_question,
    get_current_answer,
    advance_question_progress,
)
from llm_utils import (
    generate_question_message,
    evaluate_answer,
    give_hint_or_explanation,
    ask_why_correct,
    respond_to_reflection,
    is_student_answering_question,
    is_reply_relevant_to_learning,
    generate_answer_to_student_question,
)
from whatsapp_utils import send_whatsapp_message
from sheet_utils import get_student_name_by_phone

reading_sessions = {}


def start_reading_session(phone_number: int, sheet_user, sheet_comprehension):
    passage = get_passage(sheet_user, sheet_comprehension, phone_number)
    question = get_current_question(sheet_user, sheet_comprehension, phone_number)
    student_name = get_student_name_by_phone(sheet_user, phone_number)

    full_message = generate_question_message(question, student_name)
    reading_sessions[phone_number] = {
        "passage": passage,
        "question": question,
        "attempt": 1,
    }
    send_whatsapp_message(phone_number, full_message)


def handle_reading_reply(
    phone_number: int, user_reply: str, sheet_user, sheet_comprehension
):
    if phone_number not in reading_sessions:
        send_whatsapp_message(phone_number, "請先輸入 'reading' 開始今日閱讀任務 ✍️")
        return

    session = reading_sessions[phone_number]
    passage = session["passage"]
    question = session["question"]
    attempt = session["attempt"]
    correct_answer = get_current_answer(sheet_user, sheet_comprehension, phone_number)

    # Is this an actual answer?
    if not is_student_answering_question(user_reply, question):
        if is_reply_relevant_to_learning(user_reply, question):
            reply = generate_answer_to_student_question(user_reply)
            send_whatsapp_message(phone_number, reply)
        else:
            send_whatsapp_message(
                phone_number, "呢個問題好有趣，不過我哋而家專心學英文先啦 😊"
            )
        return

    # Evaluate answer
    is_correct = evaluate_answer(user_reply, correct_answer)

    if is_correct:

        # Reflective follow-up
        why_msg = ask_why_correct(question, user_reply, passage)
        send_whatsapp_message(phone_number, why_msg)

        # Await their reflection, then respond
        ####################################################################################

        # For simplicity, auto-advance after praise
        advance_question_progress(sheet_user, phone_number)
        del reading_sessions[phone_number]
        start_reading_session(phone_number, sheet_user, sheet_comprehension)
    else:
        if attempt < 3:
            hint_msg = give_hint_or_explanation(
                user_reply, correct_answer, question, passage, attempt
            )
            reading_sessions[phone_number]["attempt"] += 1
            send_whatsapp_message(phone_number, hint_msg)
        else:
            explanation = give_hint_or_explanation(
                user_reply, correct_answer, question, passage, attempt=3
            )
            send_whatsapp_message(phone_number, explanation)
            advance_question_progress(sheet_user, phone_number)
            del reading_sessions[phone_number]
            start_reading_session(phone_number, sheet_user, sheet_comprehension)
