"""
sheet_utils.py

Provides all helper functions for interacting with Google Sheets, including:
- Reading student progress and training day
- Fetching vocab and reading question data
- Advancing indexes (vocab or comprehension question)
- Updating specific cells in the sheet based on phone number

Ensures all data used in sessions is retrieved dynamically and synced across students.
"""

from oauth2client.service_account import ServiceAccountCredentials
import gspread
import config

"""
##############
General
##############
"""


def connect_to_sheet(sheet_name: str, worksheet_title: str):
    """
    Connects to a specific Google Sheet.

    This function uses the Google Sheets API via the gspread library to access
    a given spreadsheet. The credentials are loaded from file path specified in
    config.GOOGLE_SHEETS_CREDENTIAL_PATH.

    Parameters:
        sheet_name (str): The name of the Google Sheet.
        worksheet_title (str): The title of the specific worksheet/tab.

    Returns:
        gspread.models.Worksheet: A gspread worksheet object that can be used to read/write data.

    Raises:
        ValueError: If the sheet name or worksheet title is not found.

    Troubleshoot:
        Please check if the sheet is shared with the cred.json email e.g. growtalk-bot@your-project.iam.gserviceaccount.com
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        config.GOOGLE_SHEETS_CREDENTIAL_PATH, scope
    )
    client = gspread.authorize(creds)

    try:
        sheet = client.open(sheet_name).worksheet(worksheet_title)
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(
            f"❌ Spreadsheet '{sheet_name}' not found. Please check the name or sharing settings."
        )
    except gspread.exceptions.WorksheetNotFound:
        raise ValueError(
            f"❌ Worksheet '{worksheet_title}' not found in '{sheet_name}'. Please check the tab name."
        )


def update_sheet(sheet, phone_number: int, column: str, data: any) -> None:
    """
    Updates a specific cell in the given Google Sheet, based on the phone number.

    Parameters:
        sheet (gspread.Worksheet): The worksheet object to update.
        phone_number (int): The phone number to locate the row.
        column (str): The column header name to update.
        data (any): The value to write into the cell.

    Returns:
        None
    """
    row_index = get_row_index_by_phone(sheet, phone_number)

    headers = sheet.row_values(1)
    try:
        col_index = headers.index(column) + 1
    except ValueError:
        raise ValueError(f"Column '{column}' not found in sheet.")

    sheet.update_cell(row_index, col_index, data)


def get_row_index_by_phone(sheet, phone_number: int) -> int:
    """
    Returns the 1-based row index (including header) for a user based on their phone number.

    Parameters:
        sheet (gspread.Worksheet): The worksheet object.
        phone_number (int): The phone number to search for.

    Returns:
        int: The 1-based row index.
    """
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):  # Start from row 2 to account for header
        if str(row.get("phone_no")) == str(phone_number):
            return i
    raise ValueError(f"Phone number {phone_number} not found in sheet.")


def get_student_name_by_phone(sheet_user, phone_number: int) -> str:
    """
    Retrieves the student's English name from the user sheet using their phone number.

    Parameters:
        sheet_user (gspread.Worksheet): The worksheet containing user data.
        phone_number (int): The student's WhatsApp phone number (e.g., 85254069056).

    Returns:
        str: The English name of the student.

    Raises:
        ValueError: If the student is not found.
    """
    records = sheet_user.get_all_records()
    for row in records:
        if str(row.get("phone_no")) == str(phone_number):
            return row.get("eng_name")

    raise ValueError(f"❌ Student with phone number {phone_number} not found.")


def advance_day_of_training(sheet_user, phone_number: int) -> None:
    """
    Update the user's day_of_training by 1 in the given sheet.

    Parameters:
        sheet (gspread.Worksheet): The worksheet object to update.
        phone_number (int): The phone number used to locate the student row.

    Returns:
        None
    """
    # Locate the studnet
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    data = sheet_user.get_all_records()[row_index - 2]

    current_number = data.get("day_of_training")
    if current_number is None:
        raise ValueError("Column 'day_of_training' not found in student row.")

    new_number = current_number + 1

    # Use your existing update function
    update_sheet(sheet_user, phone_number, column="day_of_training", data=new_number)
    update_sheet(
        sheet_user, phone_number, column="current_question_number", data=1
    )  # Reset current_question_number to 1
    update_sheet(
        sheet_user, phone_number, column="current_vocab_number", data=0
    )  # Reset current_question_number to 0


"""
##############
READING EXERCISE
##############
"""


def get_passage(sheet_user, sheet_comprehension, phone_number: int) -> str:
    """
    Returns the passage for the training day

    Parameters:
        sheet_user (gspread.Worksheet): User sheet
        sheet_comprehension (gspread.Worksheet): Comprehension sheet
        phone_number (int): Student's phone number

    Returns:
        str: Passage text
    """
    # Locate student
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    user_data = sheet_user.get_all_records()[row_index - 2]

    # Identify what is they day of training of the student
    day = user_data["day_of_training"]

    records = sheet_comprehension.get_all_records()
    for row in records:
        if row["day_of_training"] == day:
            return row["passage_text"]

    raise ValueError(f"No passage found for Day {day}")


def get_current_question(sheet_user, sheet_comprehension, phone_number: int) -> str:
    """
    To retrieve a Question

    Parameters:
        sheet_user (gspread.Worksheet): User sheet
        sheet_comprehension (gspread.Worksheet): Comprehension sheet
        phone_number (int): Student's phone number

    Returns:
        str: The corresponding value (question or answer text)
    """
    # Locate student
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    user_data = sheet_user.get_all_records()[row_index - 2]

    day = user_data["day_of_training"]
    q_num = user_data["current_question_number"]

    records = sheet_comprehension.get_all_records()
    for row in records:
        if row["day_of_training"] == day and row["question_id"] == q_num:
            return row["question_text"]

    raise ValueError(f"Cannot find question")


def get_current_answer(sheet_user, sheet_comprehension, phone_number: int) -> str:
    """
    To retrieve a comprehension Answer

    Parameters:
        sheet_user (gspread.Worksheet): User sheet
        sheet_comprehension (gspread.Worksheet): Comprehension sheet
        phone_number (int): Student's phone number

    Returns:
        str: The corresponding value answer text
    """
    # Locate student
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    user_data = sheet_user.get_all_records()[row_index - 2]

    day = user_data["day_of_training"]
    q_num = user_data["current_question_number"]

    records = sheet_comprehension.get_all_records()
    for row in records:
        if row["day_of_training"] == day and row["question_id"] == q_num:
            return row["answer_text"]

    raise ValueError(f"Cannot find question")


def advance_question_progress(sheet_user, phone_number: int) -> None:
    """
    Update the user's current_question_number by 1 in the given sheet.

    Parameters:
        sheet (gspread.Worksheet): The worksheet object to update.
        phone_number (int): The phone number used to locate the student row.

    Returns:
        None
    """
    # Locate the row
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    data = sheet_user.get_all_records()[
        row_index - 2
    ]  # Adjust for header (row 2 = index 0)

    current_number = data.get("current_question_number")
    if current_number is None:
        raise ValueError("Column 'current_question_number' not found in student row.")

    new_number = current_number + 1

    # Use your existing update function
    update_sheet(
        sheet_user, phone_number, column="current_question_number", data=new_number
    )


def get_open_question(sheet_user, sheet_open_reading, phone_number: int) -> str:
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    user_data = sheet_user.get_all_records()[row_index - 2]
    day = user_data["day_of_training"]
    q_num = user_data["current_open_question_number"]

    records = sheet_open_reading.get_all_records()
    for row in records:
        if row["day_of_training"] == day and row["question_id"] == q_num:
            return row["question_text"]

    raise ValueError("Cannot find open-ended question")


def advance_open_question_progress(sheet_user, phone_number: int) -> None:
    """
    Increments the student's current_open_question_number by 1 in the user sheet.

    Parameters:
        sheet_user (gspread.Worksheet): The user sheet object.
        phone_number (int): The student's phone number.

    Returns:
        None
    """
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    user_data = sheet_user.get_all_records()[row_index - 2]

    current_number = user_data.get("current_open_question_number")
    if current_number is None:
        raise ValueError(
            "Column 'current_open_question_number' not found in user sheet."
        )

    new_number = current_number + 1

    update_sheet(
        sheet_user, phone_number, column="current_open_question_number", data=new_number
    )


"""
##############
VOCAB EXERCISE
##############
"""


def get_current_vocab_row(sheet_user, sheet_vocab, phone_number: int) -> dict | None:
    """
    Returns the next vocab row for a user based on their day_of_training and current_vocab_index.
    If no vocab left for the day, returns None.
    """
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    user_data = sheet_user.get_all_records()[row_index - 2]
    day = user_data["day_of_training"]
    vocab_index = user_data.get("current_vocab_number")

    # Filter vocab list by day
    vocab_data = [v for v in sheet_vocab.get_all_records() if v["Day"] == day]

    # If no more vocab left
    if vocab_index >= len(vocab_data):
        return None

    return vocab_data[vocab_index]


def advance_vocab_index(sheet_user, phone_number: int) -> None:
    row_index = get_row_index_by_phone(sheet_user, phone_number)
    user_data = sheet_user.get_all_records()[row_index - 2]
    current_index = user_data.get("current_vocab_number", 0)

    update_sheet(sheet_user, phone_number, "current_vocab_number", current_index + 1)


"""
TEST
"""

user_sheet = connect_to_sheet("User List", "Sheet1")
reading_sheet = connect_to_sheet("Question List", "reading_close_end")
vocab_sheet = connect_to_sheet("Question List", "vocab")
