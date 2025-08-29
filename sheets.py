import logging
from config import settings
if settings.USE_SHEETS:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

def _client():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(settings.GOOGLE_CREDS_FILE, scope)
    return gspread.authorize(creds)

def append_row_safe(values: list[str]):
    if not settings.USE_SHEETS:
        return
    try:
        gc = _client()
        ws = gc.open(settings.GOOGLE_SHEET_NAME).sheet1
        ws.append_row(values)
    except Exception as e:
        logging.exception(f"Sheets append failed: {e}")
