"""
whatsapp_utils.py

Provides a Python interface to send WhatsApp messages through the locally running
Node.js bot (based on whatsapp-web.js).

Key function:
- send_whatsapp_message(): Sends a message to a student's WhatsApp using their phone number.

This module decouples message sending from core session logic and allows clean external triggering.
"""

import requests

WHATSAPP_API_URL = "http://localhost:3000/send-message"


# Memory store for last sent message: { phone_number: "last_question_text" }
last_sent_messages = {}


def send_whatsapp_message(phone_number: int, message: str) -> bool:
    """
    Sends a message to a WhatsApp user via your Node.js bot.

    Parameters:
        phone_number (int): Phone number in international format (e.g. 85254069056)
        message (str): The message to send

    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        # Store the last sent message before sending
        last_sent_messages[phone_number] = message

        response = requests.post(
            WHATSAPP_API_URL,
            json={"phone_number": str(phone_number), "message": message},
        )

        if response.status_code == 200:
            print("✅ Message sent successfully!")
            return True
        else:
            print("❌ Failed to send:", response.json())
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
