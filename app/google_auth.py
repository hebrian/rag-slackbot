# google_auth.py
import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Default SCOPES for Drive RAG access
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]

# File locations (can be overridden by env vars)
TOKEN_PATH = Path(os.getenv("GDRIVE_TOKEN_PATH", "token.json"))
CREDENTIALS_PATH = Path(os.getenv("GDRIVE_CREDENTIALS_PATH", "credentials.json"))

def get_drive_credentials(scopes: list = SCOPES) -> Credentials:
    """
    Loads or refreshes credentials to access the Google Drive API.
    Returns a `Credentials` object that can be used by Google clients.
    """
    creds = None

    # Load existing token.json
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), scopes)

    # Refresh or generate new token if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH),
                scopes=scopes
            )
            creds = flow.run_local_server(
                port=0,
                access_type='offline',
                prompt='consent'
            )
        # Save the credentials for next time
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return creds
