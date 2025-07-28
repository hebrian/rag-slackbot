import sqlite3
import pandas as pd

# Load Google Sheet
import gspread
from google.oauth2.credentials import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def load_contacts_sheet():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open("CYI Directory").sheet1
    rows = sheet.get_all_records()
    return pd.DataFrame(rows)

contacts_df = load_contacts_sheet()

print(contacts_df.head())

# Write to SQLite
conn = sqlite3.connect("cyi_directory.db")
contacts_df.to_sql("Alumni", conn, if_exists="replace", index=False)
conn.close()


