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
    """Create authenticated gspread client"""
    try:
        service_account_info = st.secrets["sheets"]["service_account"]
        
        # Handle both string and dict formats
        if isinstance(service_account_info, str):
            service_account_info = json.loads(service_account_info)
            
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        raise Exception(f"Failed to connect to Google Sheets: {e}")

def get_spreadsheet():
    client = get_sheets_client()
    spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
    return client.open_by_key(spreadsheet_id)

def get_all_names(sheet_name="Remaining"):
    """Get all names from a sheet"""
    try:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet(sheet_name)
        names = worksheet.col_values(1)  # Column A
        # Remove header if present
        if names and names[0].lower() in ["name", "names"]:
            names = names[1:]
        return [n.strip() for n in names if n.strip()]
    except Exception as e:
        st.error(f"Error reading {sheet_name}: {e}")
        return []

def get_stats():
    """Return counts of Master, Remaining, and History"""
    return {
        "master": len(get_all_names("Master")),
        "remaining": len(get_all_names("Remaining")),
        "history": len(get_all_names("History"))
    }

def select_next_names(count=2):
    """Get the next N names from Remaining sheet"""
    remaining = get_all_names("Remaining")
    selected = remaining[:count]
    return selected

def remove_name_from_remaining(name: str):
    """Remove a name from the Remaining sheet after successful upload"""
    try:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet("Remaining")
        
        # Find the cell with the name
        cell = worksheet.find(name)
        if cell:
            worksheet.delete_rows(cell.row)
            return True
        return False
    except Exception as e:
        st.warning(f"Could not remove {name} from Remaining: {e}")
        return False

def add_to_history(name: str, youtube_link: str = ""):
    """Add successfully uploaded name to History sheet"""
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
    """Copy all names from Master to Remaining"""
    try:
        master_names = get_all_names("Master")
        spreadsheet = get_spreadsheet()
        
        # Clear Remaining sheet
        remaining_ws = spreadsheet.worksheet("Remaining")
        remaining_ws.clear()
        
        # Write header + names
        remaining_ws.update("A1", [["Name"]] + [[name] for name in master_names])
        return len(master_names)
    except Exception as e:
        raise Exception(f"Failed to reset Remaining list: {e}")
