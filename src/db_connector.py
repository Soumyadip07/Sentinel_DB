import pyodbc
import time
from typing import Dict, List, Optional
import src.config as config


class DatabaseConnector:
    """Manages database connections and queries for monitoring."""

    def __init__(self):
        self.connection_string = (
            f"DRIVER={config.DB_DRIVER};"
            f"SERVER={config.DB_SERVER};"
            f"DATABASE={config.DB_NAME};"
            f"UID={config.DB_USER};"
            f"PWD={config.DB_PASSWORD}"
        )
        self.connection = None

    def connect(self):
        """Establishes connection to the SQL Server database."""
        try:
            self.connection = pyodbc.connect(self.connection_string, timeout=5)
            print("Successfully connected to the database.")
        except pyodbc.Error as e:
            print(f"Error connecting to database: {e}")
            self.connection = None

    def close(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed.")

    def get_metrics(self) -> Dict[str, any]:
        """
        Collects database health metrics:
        - active_connections: Count of currently active sessions.
        - cpu_load: CPU usage percentage (requires specific DMVs).
        - long_running_queries: List of active queries taking longer than threshold.
        """
        if not self.connection:
            self.connect()
            if not self.connection:
                return {}  # Return empty if still cannot connect

        metrics = {
            "timestamp": time.time(),
            "active_connections": 0,
            "cpu_load": 0.0,
            "long_running_queries": [],
        }

        cursor = self.connection.cursor()

        try:
            # 1. Active Connections
            cursor.execute("SELECT COUNT(*) FROM sys.dm_exec_connections")
            metrics["active_connections"] = cursor.fetchone()[0]

            # 2. CPU Load (Querying ring buffer for historical CPU utilization is complex, using simplified DMV approach)
            # This query gets the latest CPU usage record
            cpu_query = """
                SELECT TOP(1)
                    CAST(record.value('(./Record/SchedulerMonitorEvent/SystemHealth/SystemIdle)[1]', 'int') AS INT) AS SystemIdle
                FROM sys.dm_os_ring_buffers
                WHERE ring_buffer_type = 'RING_BUFFER_SCHEDULER_MONITOR'
                AND record LIKE '%<SystemHealth>%'
                ORDER BY timestamp DESC
            """
            try:
                cursor.execute(cpu_query)
                row = cursor.fetchone()
                if row:
                    system_idle = row[0]
                    metrics["cpu_load"] = (
                        100 - system_idle
                    )  # Approximate total CPU load
            except Exception as e:
                print(f"Failed to fetch CPU load: {e}")

            # 3. Long-Running Queries
            long_query_sql = f"""
                SELECT session_id, status, command, total_elapsed_time, cpu_time
                FROM sys.dm_exec_requests
                WHERE total_elapsed_time > {config.LONG_RUNNING_QUERY_THRESHOLD_MS}
                AND session_id != @@SPID
            """
            cursor.execute(long_query_sql)
            columns = [column[0] for column in cursor.description]
            metrics["long_running_queries"] = [
                dict(zip(columns, row)) for row in cursor.fetchall()
            ]

        except pyodbc.Error as e:
            print(f"Error executing query: {e}")
            # Reconnect on next attempt
            self.close()

        return metrics
