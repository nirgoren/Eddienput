import time
from time import perf_counter

eps = 0.001

class Clock:
    def __init__(self, fps):
        self.frame_length = 1 / fps
        self.next = perf_counter() + self.frame_length

    def sleep(self):
        while perf_counter() < self.next:
            pass
        self.next += self.frame_length + int(perf_counter()-self.next)*self.frame_length
        # self.next = perf_counter() + self.frame_length

    def reset(self):
        self.next = int(perf_counter() + self.frame_length) + 1
