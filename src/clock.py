import time
from time import perf_counter

class Clock:

    def __init__(self, fps):
        self.start = perf_counter()
        self.frame_length = 1 / fps

    @property
    def tick(self):
        return perf_counter() - self.start

    def sleep(self, frame_count):
        while self.tick < self.frame_length * frame_count:
            pass
            time.sleep(0)
        self.start = perf_counter()

    def reset(self):
        self.start = perf_counter()
