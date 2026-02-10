from twilio.rest import Client
import requests
import src.config as config
import logging


class AlertManager:
    """Handles sending alerts via configured channels (Twilio SMS / Slack)."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_alert(self, message: str):
        """Dispatches an alert through available channels."""
        print("\n" + "!" * 50)
        print("🚨  CRITICAL ALERT: ANOMALY DETECTED  🚨")
        print("!" * 50 + "\n")
        print(f"[ALERT]: {message}\n")

        if config.SLACK_WEBHOOK_URL:
            self._send_slack_alert(message)

        if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
            self._send_twilio_alert(message)

        if not (config.SLACK_WEBHOOK_URL or config.TWILIO_ACCOUNT_SID):
            self.logger.warning(
                "No alerting channels configured! Printing to console instead."
            )
            print(f"[ALERT]: {message}")

    def _send_slack_alert(self, message: str):
        """Sends a notification to a Slack channel via webhook."""
        payload = {"text": f"🚨 *Database Anomaly Detected* 🚨\n\n{message}"}
        try:
            response = requests.post(config.SLACK_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            self.logger.info("Slack alert sent successfully.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Slack alert: {e}")

    def _send_twilio_alert(self, message: str):
        """Sends an SMS alert via Twilio API."""
        try:
            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"DB MONITOR ALERT: {message}",
                from_=config.TWILIO_FROM_PHONE,
                to=config.TWILIO_TO_PHONE,
            )
            self.logger.info(f"Twilio SMS sent successfully. SID: {message.sid}")
        except Exception as e:
            self.logger.error(f"Failed to send Twilio alert: {e}")
