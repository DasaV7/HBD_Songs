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
        # Method 1: Try nested secrets
        if "sheets" in st.secrets and "service_account" in st.secrets["sheets"]:
            sa_info = st.secrets["sheets"]["service_account"]
            
            # Convert AttrDict / dict to normal dict
            if hasattr(sa_info, "to_dict"):
                sa_info = sa_info.to_dict()
            else:
                sa_info = dict(sa_info)
                
        # Method 2: Try full JSON string
        elif "sheets" in st.secrets and "service_account_json" in st.secrets["sheets"]:
            sa_info = json.loads(st.secrets["sheets"]["service_account_json"])
        else:
            raise Exception("No service account found in secrets")

        # Fix private_key newlines if needed
        if "private_key" in sa_info:
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")

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
        if names and names[0].lower() in ["name", "names"]:
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
