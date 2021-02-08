from pynput.keyboard import Key, Listener, Controller, KeyCode
from clock import Clock
import time
import random
import json
from key_emulation import *

WAIT_CONST = 'W'
NEXT_CONST = 'next'
COMMENT_SYMBOL = '#'

#P2
# P = 'numpad_1'
# K = 'numpad_4'
# S = 'numpad_5'
# H = 'numpad_6'
# D = 'numpad_3'
# T = 'numpad_2'
#
# down = 'down'
# left = 'left'
# right = 'right'
# up = 'up'

clock = Clock(60)
to_release = set()
pressed = set()
symbols_map = {}
macros_map = {}
repetitions = 1


def string_to_frames(s: str):
    moves = []
    s = s.replace('\n', '')
    frames = s.split(' ')
    res = []
    for frame in frames:
        if not frame.startswith(WAIT_CONST):
            res.append(frame)
        else:
            if len(frame) == 1:
                res.append('W')
            else:
                # support for Wn with n being a natural number
                res.extend(['W' for i in range(int(frame[1:]))])
    s = ' '.join(res)
    # todo: define macros at the config file
    for macro in macros_map:
        s = s.replace(macro, macros_map[macro])
    frames = s.split(' ')
    for frame in frames:
        frame_moves = []
        frame = frame.split('+')
        for button in frame:
            if button.startswith('W'):
                pass
            else:
                command = 'tap'
                if button.startswith('['):
                    command = 'press'
                    button = button[1:-1]
                elif button.startswith(']'):
                    command = 'release'
                    button = button[1:-1]
                frame_moves.append((symbols_map[button], command))
        moves.append(frame_moves)
    moves.append([])
    return moves


def wait():
    clock.sleep()


def reset():
    clock.reset()


def press(button):
    #t0 = time.perf_counter()
    press_key(to_key_code(button))
    #print(time.perf_counter() - t0)
    #print("pressed", button)


def release(button):
    #t0 = time.perf_counter()
    release_key(to_key_code(button))
    #print(time.perf_counter() - t0)
    #print("released", button)


def run_frame(frame):
    frame_press_buttons = [x[0] for x in frame if x[1] != 'release']
    released = set()
    for button in to_release:
        if button not in frame_press_buttons:
            pressed.discard(button)
            release(button)
            released.update({button})
    for button in released:
        to_release.discard(button)
    for button, command in frame:
        if command == 'tap':
            if button not in pressed:
                to_release.update({button})
                pressed.update({button})
                press(button)
        elif command == 'press':
            pressed.update({button})
            press(button)
        elif command == 'release':
            pressed.discard(button)
            release(button)
    wait()


def perform_actions(actions):
    for frame in actions:
        run_frame(frame)


def do_action():
    for _ in range(repetitions):
        for recordings in sequences:
            if len(recordings) != 0:
                r = random.randint(0, len(recordings) - 1)
                clock.reset()
                perform_actions(recordings[r])


def on_press(key):
    #print("received", str(key))
    if str(key) == "'*'":
        do_action()


if __name__ == "__main__":

    f = open('config.json', 'r')
    j = json.load(f)
    symbols_map.update(j["Symbols"])
    macros_map.update(j["Macros"])
    repetitions = j["Repetitions"]
    f.close()

    sequences = [[]]
    f = open('recordings.txt', 'r')
    i = 0
    for line in f:
        # ignore comment lines
        if line.startswith(COMMENT_SYMBOL):
            pass
        elif line.startswith(NEXT_CONST):
            i += 1
            sequences.append([])
            continue
        else:
            sequences[i].append(string_to_frames(line))
    f.close()

    with Listener(on_press=on_press) as listener:
        listener.join()
