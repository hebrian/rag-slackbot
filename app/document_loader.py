from langchain_google_community import GoogleDriveLoader
from google_auth import get_drive_credentials
from config import GDRIVE_FOLDER_ID

def load_documents():
    creds = get_drive_credentials()
    loader = GoogleDriveLoader(
        folder_id=GDRIVE_FOLDER_ID,
        credentials=creds,
        recursive=True
    )
    return loader.load()
