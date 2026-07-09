import time
from typing import Dict

class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.split_times: Dict[str, float] = {}

    def start(self):
        self.start_time = time.perf_counter()
        self.end_time = None
        self.split_times = {}

    def stop(self) -> float:
        if self.start_time is None:
            return 0.0
        self.end_time = time.perf_counter()
        return self.end_time - self.start_time

    def split(self, label: str):
        if self.start_time is None:
            return
        self.split_times[label] = time.perf_counter() - self.start_time

    def get_duration_str(self) -> str:
        duration = self.stop() if self.end_time is None else (self.end_time - self.start_time)
        return f"{duration:.2f} seconds"
