import os
import sys

# Add src to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import requests
import pyodbc
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from src import config

# Setup Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Verification")


def check_mssql():
    """Verify MSSQL connection."""
    logger.info("Checking MSSQL Connection...")
    connection_string = (
        f"DRIVER={config.DB_DRIVER};"
        f"SERVER={config.DB_SERVER};"
        f"DATABASE={config.DB_NAME};"
        f"UID={config.DB_USER};"
        f"PWD={config.DB_PASSWORD}"
    )

    try:
        conn = pyodbc.connect(connection_string, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        result = cursor.fetchone()
        logger.info(
            f"✅ MSSQL Connected Successfully! Version: {result[0].split('-')[0].strip()}"
        )
        conn.close()
        return True
    except pyodbc.Error as e:
        logger.error(f"❌ MSSQL Connection Failed: {e}")
        return False


def check_slack():
    """Verify Slack Webhook."""
    logger.info("Checking Slack Webhook...")
    if (
        not config.SLACK_WEBHOOK_URL
        or "hooks.slack.com" not in config.SLACK_WEBHOOK_URL
    ):
        logger.warning("⚠️ Slack Webook URL is not configured or invalid.")
        return False

    try:
        response = requests.post(
            config.SLACK_WEBHOOK_URL,
            json={
                "text": "✅ *DB Monitor Test Alert*: Slack integration verified successfully!"
            },
        )
        if response.status_code == 200:
            logger.info("✅ Slack Alert Sent Successfully!")
            return True
        else:
            logger.error(
                f"❌ Slack Alert Failed with Status {response.status_code}: {response.text}"
            )
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Slack Alert Failed: {e}")
        return False


def check_twilio():
    """Verify Twilio SMS."""
    logger.info("Checking Twilio SMS...")
    if not config.TWILIO_ACCOUNT_SID or not config.TWILIO_AUTH_TOKEN:
        logger.warning("⚠️ Twilio credentials are missing in .env.")
        return False

    try:
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        # Verify account status more gently without sending SMS if possible, or send one test SMS
        # Sending a test SMS to check integration
        message = client.messages.create(
            body="✅ DB Monitor Test Alert: Twilio integration verified successfully!",
            from_=config.TWILIO_FROM_PHONE,
            to=config.TWILIO_TO_PHONE,
        )
        logger.info(f"✅ Twilio SMS Sent Successfully! SID: {message.sid}")
        return True
    except TwilioRestException as e:
        logger.error(f"❌ Twilio Error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Twilio Setup Error: {e}")
        return False


if __name__ == "__main__":
    print("-" * 50)
    mssql_ok = check_mssql()
    print("-" * 50)
    slack_ok = check_slack()
    print("-" * 50)
    twilio_ok = check_twilio()
    print("-" * 50)

    if mssql_ok and (slack_ok or twilio_ok):
        logger.info(
            "🎉 Setup Verification Complete! You are ready to start the monitor."
        )
    else:
        logger.warning(
            "⚠️  Verification Incomplete. Please fix the errors above in .env and try again."
        )
