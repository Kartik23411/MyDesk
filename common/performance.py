# Messure fps and latecy of the connection

import time
from collections import deque

class PerformanceTracker:

    def __init__(self, window_size=30):
        self.frame_times = deque(maxlen=window_size)
        self.last_frame_time = None
        self.frame_count = 0

    def record_frame(self):
        current_time = time.time();
        if self.last_frame_time is not None:
            frame_time = current_time - self.last_frame_time
            self.frame_times.append(frame_time)

        self.last_frame_time = current_time
        self.frame_count += 1
    
    def get_fps(self):
        if len(self.frame_times) == 0:
            return 0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)

        if avg_frame_time == 0:
            return 0
        return 1.0/avg_frame_time
    
    def get_avg_frame_time_ms(self):

        if len(self.frame_times)==0:
            return 0
        return (sum(self.frame_times)/len(self.frame_times)) * 1000
    
    def reset(self):
        self.frame_times.clear()
        self.last_frame_time = None
        self.frame_count = 0;