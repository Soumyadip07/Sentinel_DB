import numpy as np
import collections
import time
from typing import List, Deque
import src.config as config


class AnomalyDetector:
    """Detects database anomalies using Z-score statistical analysis."""

    def __init__(self, window_size: int = 50):
        # Rolling window for historical connection counts (last hour if interval=60s)
        self.history: Deque[float] = collections.deque(maxlen=window_size)

    def add_metric(self, value: float):
        """Adds a new data point to the history."""
        self.history.append(value)

    def is_anomaly(self) -> bool:
        """
        Checks if the latest added metric is an anomaly based on Z-Score calculation against historical data.
        Returns True if anomalous, False otherwise.
        """
        if len(self.history) < 10:  # Need minimum data points for meaningful stats
            return False

        current_value = self.history[-1]

        # Calculate Mean (μ) and Standard Deviation (σ)
        mean = np.mean(
            list(self.history)[:-1]
        )  # Exclude current value from baseline calculation?
        # Typically include current value in mean for rolling window, or exclude for prediction.
        # Using previous data points as baseline is better for detection.
        if len(self.history) > 1:
            baseline = list(self.history)[:-1]
        else:
            return False  # Not enough history

        mean = np.mean(baseline)
        std_dev = np.std(baseline)

        if std_dev == 0:
            return False  # Avoid division by zero; no variance

        z_score = (current_value - mean) / std_dev

        print(
            f"Current: {current_value}, Mean: {mean:.2f}, StdDev: {std_dev:.2f}, Z-Score: {z_score:.2f}"
        )

        return abs(z_score) > config.ANOMALY_Z_SCORE_THRESHOLD
