# services/sheets_service.py

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import bcrypt
import uuid

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_sheets_client():
    try:
        if "sheets" not in st.secrets:
            raise Exception("No [sheets] section found in secrets")

        sheets_secrets = st.secrets["sheets"]
        sa_raw = sheets_secrets.get("service_account")

        if sa_raw is None:
            raise Exception("service_account is missing in secrets")

        # Handle both dict and JSON string
        if isinstance(sa_raw, dict):
            sa_info = dict(sa_raw)
        elif isinstance(sa_raw, str):
            sa_info = json.loads(sa_raw)
        else:
            sa_info = {k: sa_raw[k] for k in sa_raw}

        # Fix private_key newlines
        if "private_key" in sa_info and isinstance(sa_info["private_key"], str):
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n").strip()

        credentials = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
        client = gspread.authorize(credentials)
        return client

    except Exception as e:
        raise Exception(f"Failed to connect to Google Sheets: {e}")


def get_spreadsheet():
    client = get_sheets_client()
    spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
    return client.open_by_key(spreadsheet_id)


def get_all_names(sheet_name="Remaining"):
    try:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet(sheet_name)
        names = worksheet.col_values(1)

        if names and names[0].lower().strip() in ["name", "names"]:
            names = names[1:]

        return [n.strip() for n in names if n.strip()]
    except Exception as e:
        st.error(f"Error reading {sheet_name}: {e}")
        return []


def get_stats():
    """Direct call - only use when user clicks Refresh"""
    return {
        "master": len(get_all_names("Master")),
        "remaining": len(get_all_names("Remaining")),
        "history": len(get_all_names("History"))
    }


def select_next_names(count=2):
    remaining = get_all_names("Remaining")
    return remaining[:count]


def remove_name_from_remaining(name: str):
    try:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet("Remaining")
        cell = worksheet.find(name)
        if cell:
            worksheet.delete_rows(cell.row)
            return True
        return False
    except Exception as e:
        st.warning(f"Could not remove {name}: {e}")
        return False


def add_to_history(name: str, youtube_link: str = ""):
    try:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet("History")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([name, timestamp, youtube_link])
        return True
    except Exception as e:
        st.warning(f"Could not add to History: {e}")
        return False


def reset_remaining_from_master():
    try:
        master_names = get_all_names("Master")
        spreadsheet = get_spreadsheet()
        remaining_ws = spreadsheet.worksheet("Remaining")
        remaining_ws.clear()
        remaining_ws.update("A1", [["Name"]] + [[name] for name in master_names])
        return len(master_names)
    except Exception as e:
        raise Exception(f"Failed to reset Remaining list: {e}")

def register_user(
    first_name,
    last_name,
    email,
    phone,
    age,
    gender,
    password,
    whatsapp_consent=True
):

    spreadsheet = get_spreadsheet()
    ws = spreadsheet.worksheet("Users")

    existing = ws.get_all_records()

    for row in existing:
        if row["email"].lower() == email.lower():
            return False, "Email already registered"

    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    user_id = f"USR{str(uuid.uuid4())[:8]}"

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    ws.append_row([
        user_id,
        first_name,
        last_name,
        email,
        phone,
        age,
        gender,
        password_hash,
        "user",
        whatsapp_consent,
        True,
        "Active",
        now,
        ""
    ])

    return True, user_id

def authenticate_user(
    email,
    password
):

    spreadsheet = get_spreadsheet()

    ws = spreadsheet.worksheet("Users")

    records = ws.get_all_records()

    for row in records:

        if row["email"].lower() == email.lower():

            if bcrypt.checkpw(
                password.encode(),
                row["password_hash"].encode()
            ):

                return {
                    "success": True,
                    "user_id": row["user_id"],
                    "role": row["role"],
                    "first_name": row["first_name"],
                    "email": row["email"]
                }

    return {
        "success": False
    }
def add_video_request(
    user_id,
    email,
    recipient_name,
    message,
    video_file="",
    youtube_url="",
    status="Pending"
):

    spreadsheet = get_spreadsheet()

    ws = spreadsheet.worksheet(
        "VideoRequests"
    )

    request_id = f"REQ{str(uuid.uuid4())[:8]}"

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    ws.append_row([
        request_id,
        user_id,
        email,
        recipient_name,
        message,
        video_file,
        youtube_url,
        status,
        now,
        ""
    ])


