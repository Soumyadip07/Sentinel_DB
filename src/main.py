import time

import sys
import os
import signal
import logging

# Ensure we have access to src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.config as config
from src.db_connector import DatabaseConnector
from src.anomaly_detection import AnomalyDetector
from src.alerting import AlertManager

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("monitor.log")],
)
logger = logging.getLogger("DBMonitor")


def main():
    logger.info("Starting Database Health Monitor...")

    # Initialize components
    db_connector = DatabaseConnector()
    anomaly_detector = AnomalyDetector(
        window_size=60
    )  # 1 hour of history if updating every 60s
    alert_manager = AlertManager()

    # Graceful shutdown handler
    def signal_handler(sig, frame):
        logger.info("Shutting down monitor...")
        db_connector.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while True:
            start_time = time.time()

            # 1. Collect Data
            try:
                metrics = db_connector.get_metrics()
                if not metrics:
                    logger.warning(
                        "Failed to collect metrics. Retrying in next interval..."
                    )
                    time.sleep(config.CHECK_INTERVAL_SECONDS)
                    continue

                active_connections = metrics.get("active_connections", 0)
                cpu_load = metrics.get("cpu_load", 0)
                long_queries = metrics.get("long_running_queries", [])

                logger.info(
                    f"Metrics Collected: Connections={active_connections}, CPU={cpu_load}%, LongQueries={len(long_queries)}"
                )

                # 2. Update Anomaly Detector
                # We specifically track connection counts for anomaly detection based on requirements
                anomaly_detector.add_metric(active_connections)

                # 3. Check for Anomalies
                if anomaly_detector.is_anomaly():
                    message = (
                        f"Unusual spike in active connections detected! "
                        f"Current: {active_connections}. "
                        f"CPU Load: {cpu_load}%. "
                        f"Active Long Queries: {len(long_queries)}"
                    )
                    logger.warning("ANOMALY DETECTED: " + message)
                    alert_manager.send_alert(message)

                # Check for critical thresholds (independent of Z-score)
                if cpu_load > 90:
                    alert_manager.send_alert(f"Critical CPU Load: {cpu_load}%")

                if len(long_queries) > 0:
                    logger.warning(
                        f"Detected {len(long_queries)} long-running queries."
                    )

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)

            # Sleep for the remainder of the interval
            elapsed_time = time.time() - start_time
            sleep_time = max(0, config.CHECK_INTERVAL_SECONDS - elapsed_time)
            time.sleep(sleep_time)

    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        db_connector.close()


if __name__ == "__main__":
    main()
