import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration (MSSQL via ODBC)
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "master")
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YourStrongPassword123")
DB_DRIVER = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

# Alerting Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_PHONE = os.getenv("TWILIO_FROM_PHONE")
TWILIO_TO_PHONE = os.getenv("TWILIO_TO_PHONE")

# Monitoring Settings
CHECK_INTERVAL_SECONDS = int(
    os.getenv("CHECK_INTERVAL_SECONDS", 10)
)  # Needs to be faster for demo purposes
LONG_RUNNING_QUERY_THRESHOLD_MS = int(
    os.getenv("LONG_RUNNING_QUERY_THRESHOLD_MS", 5000)
)
ANOMALY_Z_SCORE_THRESHOLD = float(os.getenv("ANOMALY_Z_SCORE_THRESHOLD", 2.0))
