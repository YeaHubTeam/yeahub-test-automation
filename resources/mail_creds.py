import os

from dotenv import load_dotenv

load_dotenv()


class MailCreds:
    HOST = os.getenv("MAIL_HOST")
    EMAIL = os.getenv("MAIL_EMAIL")
    PASSWORD = os.getenv("MAIL_PASSWORD")
    FOLDER = os.getenv("MAIL_FOLDER", "INBOX")
    PORT = int(os.getenv("MAIL_PORT", "993"))
