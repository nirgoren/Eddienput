from pynput.keyboard import Key, Listener, Controller, KeyCode
from clock import Clock
import time
import random
import json
from key_emulation import *

WAIT_CONST = 'W'

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

#P1

# P = 'j'
# K = 'u'
# S = 'i'
# H = 'o'
# D = 'l'
# T = 'k'
#
# down = 's'
# left = 'a'
# right = 'd'
# up = Key.space

clock = Clock(60)
to_release = set()
pressed = set()

button_map = {
}


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
    # macros
    s = s.replace('1', '2+4')
    s = s.replace('3', '2+6')
    s = s.replace('7', '4+8')
    s = s.replace('9', '6+8')
    s = s.replace('5', 'W')
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
                frame_moves.append((button_map[button], command))
        moves.append(frame_moves)
    moves.append([])
    return moves


def wait(frames):
    clock.sleep(frames)


def reset():
    clock.reset()


def press(button):
    #t0 = time.perf_counter()
    press_key(to_key_code(button))
    #print(time.perf_counter() - t0)
    print("pressed", button)


def release(button):
    #t0 = time.perf_counter()
    release_key(to_key_code(button))
    #print(time.perf_counter() - t0)
    print("released", button)


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
    wait(1)


def perform_actions(actions):
    for frame in actions:
        run_frame(frame)


def do_action():
    i = random.randint(0, len(queues)-1)
    clock.reset()
    perform_actions(queues[i])


def on_press(key):
    print("received", str(key))
    if str(key) == "'*'":
        do_action()


if __name__ == "__main__":

    f = open('config.json', 'r')
    button_map.update(json.load(f))
    f.close()

    queues = []
    f = open('recordings.txt', 'r')
    for line in f:
        # ignore comment lines
        if line.startswith('#'):
            pass
        queues.append(string_to_frames(line))
    f.close()
    # queues.append(string_to_frames('4 5 4 W20 4 5 4 W20 [4] W20 ]4[ 6 5 [6] W17 ]6[ W20 2 3 6 P W13 K+S+H'))
    # queues.append(string_to_frames('2 3 6 [K] W10 ]K['))

    with Listener(on_press=on_press) as listener:
        listener.join()
