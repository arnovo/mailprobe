\
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple

# Lazy imports so dry_run doesn't require Google deps
def _load_google():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    return service_account, build

def get_sheets_service(service_account_file: str):
    service_account, build = _load_google()
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    return build("sheets", "v4", credentials=creds)

def ensure_header(service, spreadsheet_id: str, worksheet: str, header: List[str]) -> None:
    """
    Ensures row 1 matches header. If empty, writes header.
    """
    rng = f"{worksheet}!1:1"
    resp = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=rng).execute()
    values = resp.get("values", [])
    if not values or not values[0]:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=rng,
            valueInputOption="RAW",
            body={"values": [header]},
        ).execute()
        return

def find_row_by_key(service, spreadsheet_id: str, worksheet: str, key_col_idx: int, key_value: str) -> Optional[int]:
    """
    Returns 1-based row index of first match in column key_col_idx, else None.
    Assumes header at row 1; searches from row 2.
    """
    col_letter = chr(ord("A") + key_col_idx)
    rng = f"{worksheet}!{col_letter}:{col_letter}"
    resp = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=rng).execute()
    values = resp.get("values", [])
    # values[0] is header (maybe)
    for i, row in enumerate(values[1:], start=2):
        if row and row[0].strip() == key_value:
            return i
    return None

def upsert_row(service, spreadsheet_id: str, worksheet: str, header: List[str], row_dict: Dict[str, Any], key_field: str = "linkedin_url") -> Tuple[str, int]:
    """
    Upsert by key_field.
    Returns (action, row_index)
    """
    key_col_idx = header.index(key_field)
    key_value = str(row_dict.get(key_field, "")).strip()
    if not key_value:
        raise ValueError(f"Missing key_field '{key_field}'")

    row_index = find_row_by_key(service, spreadsheet_id, worksheet, key_col_idx, key_value)
    row_values = [str(row_dict.get(col, "")) if row_dict.get(col, "") is not None else "" for col in header]

    if row_index is None:
        # Append
        rng = f"{worksheet}!A:A"
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=rng,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row_values]},
        ).execute()
        return ("inserted", -1)
    else:
        # Update exact row
        start = "A"
        end = chr(ord("A") + len(header) - 1)
        rng = f"{worksheet}!{start}{row_index}:{end}{row_index}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=rng,
            valueInputOption="RAW",
            body={"values": [row_values]},
        ).execute()
        return ("updated", row_index)
