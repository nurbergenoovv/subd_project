from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USERNAME")
DB_PASS = os.environ.get("DB_PASSWORD")


SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = os.environ.get("SMTP_PORT")
SMTP_USERNAME = os.environ.get("USERNAME")
SMTP_PASSWORD = os.environ.get("PASSWORD")
SMTP_DOMAIN = os.environ.get("DOMAIN")

FRONT_DOMAIN = os.environ.get("FRONT_DOMAIN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")