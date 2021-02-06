from pynput.keyboard import Key, Listener, Controller, KeyCode
import time
from time import perf_counter
import pydirectinput

# add missing numpad buttons to mapping
NUMPAD_MAPPING = {
    'numpad_enter': 0x9C + 1024,
    'numpad_1': 0x4F,
    'numpad_2': 0x50,
    'numpad_3': 0x51,
    'numpad_4': 0x4B,
    'numpad_5': 0x4C,
    'numpad_6': 0x4D,
    'numpad_7': 0x47,
    'numpad_8': 0x48,
    'numpad_9': 0x49,
    'numpad_0': 0x52
}

pydirectinput.KEYBOARD_MAPPING.update(NUMPAD_MAPPING)

class Clock:

    def __init__(self, fps):
        self.start = perf_counter()
        self.frame_length = 1 / fps

    @property
    def tick(self):
        return (perf_counter() - self.start)

    def sleep(self, frame_count):
        self.start = perf_counter()
        while self.tick < self.frame_length * frame_count:
            pass
            time.sleep(0)

#P2

P = 'numpad_1'
K = 'numpad_4'
S = 'numpad_5'
H = 'numpad_6'
D = 'numpad_3'

down = 'down'
left = 'left'
right = 'right'
up = 'up'

#P1

# P = 'j'
# K = 'u'
# S = 'i'
# H = 'o'
# D = 'l'
#
# down = 's'
# left = 'a'
# right = 'd'
# up = Key.space

clock = Clock(60)
keyboard = Controller()

def wait(frames):
    clock.sleep(frames)

def tap(button):
    pydirectinput.keyDown(button)
    wait(1)
    pydirectinput.keyUp(button)

def press(button):
    keyboard.press(button)

def release(button):
    keyboard.release(button)

def do_action():
    tap(down)
    wait(40)
    tap(P)
    wait(40)
    tap(D)
    wait(40)
    tap(S)

def on_press(key):
    print(str(key))
    if str(key) == "'*'":
        do_action()

with Listener(on_press=on_press) as listener:
    listener.join()