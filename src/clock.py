import time
from time import perf_counter


class Clock:

    def __init__(self, fps):
        self.frame_length = 1 / fps
        self.next = perf_counter() + self.frame_length

    def sleep(self):
        while perf_counter() < self.next:
            pass
            # time.sleep(0)
        self.next += self.frame_length + int(perf_counter()-self.next)

    def reset(self):
        self.next = perf_counter() + self.frame_length
