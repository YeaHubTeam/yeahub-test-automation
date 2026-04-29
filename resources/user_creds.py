import os

from dotenv import load_dotenv

load_dotenv()


class SuperAdminCreds:
    USERNAME = os.getenv("SUPER_ADMIN_USERNAME")
    PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")


class VerifiedUserCreds:
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")
