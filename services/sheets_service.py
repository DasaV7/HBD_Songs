# services/sheets_service.py

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_sheets_client():
    try:
        if "sheets" not in st.secrets:
            raise Exception("No [sheets] section found in secrets")

        sheets_secrets = st.secrets["sheets"]
        spreadsheet_id = sheets_secrets.get("spreadsheet_id")
        if not spreadsheet_id:
            raise Exception("spreadsheet_id is missing")

        # ---------- Load service account ----------
        sa_raw = sheets_secrets.get("service_account")

        if sa_raw is None:
            raise Exception("service_account is missing in secrets")

        # Case 1: It is already a dict (nested secrets)
        if isinstance(sa_raw, dict):
            sa_info = dict(sa_raw)

        # Case 2: It is a JSON string (your current format)
        elif isinstance(sa_raw, str):
            sa_info = json.loads(sa_raw)

        else:
            # Streamlit AttrDict or similar
            try:
                sa_info = {k: sa_raw[k] for k in sa_raw}
            except Exception:
                raise Exception(f"Unsupported service_account type: {type(sa_raw)}")

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

        # Remove header if present
        if names and names[0].lower().strip() in ["name", "names"]:
            names = names[1:]

        return [n.strip() for n in names if n.strip()]
    except Exception as e:
        st.error(f"Error reading {sheet_name}: {e}")
        return []


def get_stats():
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