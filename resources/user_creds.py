import os

from dotenv import load_dotenv

load_dotenv()


class VerifiedUserCreds:
    EMAIL = os.getenv("VERIFIED_USER_EMAIL")
    PASSWORD = os.getenv("VERIFIED_USER_PASSWORD")
