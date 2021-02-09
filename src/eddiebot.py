from pynput.keyboard import Key, Listener, Controller, KeyCode
from clock import Clock
import time
import random
import json
import pyxinput  # requires installation: https://github.com/shauleiz/vXboxInterface/releases

WAIT_CONST = 'W'
NEXT_CONST = 'next'
COMMENT_SYMBOL = '#'
FPS = 60
REPETITIONS_DEFAULT = 1

clock = Clock(FPS)
to_release = set()
symbols_map = {}
macros_map = {}
repetitions = REPETITIONS_DEFAULT
MyVirtual = pyxinput.vController()
sequences = [[]]


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
                res.append(WAIT_CONST)
            else:
                # support for Wn with n being a natural number
                res.extend([WAIT_CONST for i in range(int(frame[1:]))])
    s = ' '.join(res)
    for macro in macros_map:
        s = s.replace(macro, macros_map[macro])
    frames = s.split(' ')
    for frame in frames:
        frame_moves = []
        frame = frame.split('+')
        for button in frame:
            if button.startswith(WAIT_CONST):
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


def press(button, value):
    #t0 = time.perf_counter()
    MyVirtual.set_value(button, value)
    #print(time.perf_counter() - t0)
    #print("pressed", button)


def release(button):
    #t0 = time.perf_counter()
    MyVirtual.set_value(button, 0)
    #print(time.perf_counter() - t0)
    #print("released", button)


def run_frame(frame):
    frame_press_buttons = [x[0] for x in frame if x[1] != 'release']
    released = set()
    for button in to_release:
        if button not in frame_press_buttons:
            release(button)
            released.update({button})
    for button in released:
        to_release.discard(button)
    for button, command in frame:
        value = 1
        if not isinstance(button, str):
            value = button['Dpad']
            button = 'Dpad'
        if command == 'tap':
            press(button, value)
            to_release.update({button})
        elif command == 'press':
            press(button, value)
            to_release.discard(button)
        elif command == 'release':
            release(button)
    wait()


def perform_actions(actions):
    for frame in actions:
        run_frame(frame)


def run_scenario():
    for _ in range(repetitions):
        for recordings in sequences:
            if len(recordings) != 0:
                r = random.randint(0, len(recordings) - 1)
                clock.reset()
                perform_actions(recordings[r])


def on_press(key):
    # print("received", str(key))
    if str(key) == r"'\x12'":  # ctrl+r
        print("Reloading script")
        main()
    if str(key) == r"<96>":
        run_scenario()
        print("Sequence complete")


def main():
    global symbols_map
    global macros_map
    global repetitions
    global sequences
    f = open('config.json', 'r')
    j = json.load(f)
    symbols_map = j["Symbols"]
    macros_map = j["Macros"]
    repetitions = j["Repetitions"]
    recordings_file = j["Recordings_file"]
    f.close()
    sequences = [[]]
    f = open(recordings_file, 'r')
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
    print("Eddie is ready")


if __name__ == "__main__":
    main()
    with Listener(on_press=on_press) as listener:
        listener.join()
