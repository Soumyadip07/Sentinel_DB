import pyodbc
import threading
import time
import sys
import os

# Stress Test Script for SentinelDB
# Simulates high connection load and long-running queries to trigger anomalies.

# Add src to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.config as config

CONNECTION_STRING = (
    f"DRIVER={config.DB_DRIVER};"
    f"SERVER={config.DB_SERVER};"
    f"DATABASE={config.DB_NAME};"
    f"UID={config.DB_USER};"
    f"PWD={config.DB_PASSWORD}"
)


def attack_database(duration=30, threads=20):
    print(
        f"🔥 ATTACKING DATABASE: Spawning {threads} threads for {duration} seconds..."
    )

    stop_event = threading.Event()

    def worker():
        try:
            conn = pyodbc.connect(CONNECTION_STRING, timeout=5)
            cursor = conn.cursor()
            while not stop_event.is_set():
                try:
                    # 50% chance to run a slow query (WAITFOR DELAY)
                    # This will trigger the "Long Running Query" alert (> 5000ms)
                    cursor.execute("WAITFOR DELAY '00:00:06'")
                except:
                    pass
                time.sleep(0.5)
            conn.close()
        except Exception as e:
            pass  # Ignore connection errors during stress test

    # Launch threads
    qt_threads = []
    for _ in range(threads):
        t = threading.Thread(target=worker)
        t.start()
        qt_threads.append(t)

    time.sleep(duration)
    stop_event.set()

    for t in qt_threads:
        t.join()

    print("✅ Attack Complete. Check your monitor for alerts!")


if __name__ == "__main__":
    attack_database()
