from pynput.keyboard import Key, Listener, Controller, KeyCode
from clock import Clock
import time
import random
import json
import pyxinput  # requires installation: https://github.com/shauleiz/vXboxInterface/releases
from PyQt5.QtWidgets import QApplication, QWidget
import sys
import re

WAIT_CONST = 'W'
NEXT_CONST = 'next'
COMMENT_SYMBOL = '#'
MIX_START = 'startmix'
OPTION = 'option'
MIX_END = 'endmix'
FPS = 60
REPETITIONS_DEFAULT = 1

resets = 0
clock = Clock(FPS)
to_release = set()
P1_directions_map = {"2": { "Dpad": 2 },
                  "4": { "Dpad": 4 },
                  "6": { "Dpad": 8 },
                  "8": { "Dpad": 1 },
                  "1": { "Dpad": 6 },
                  "3": { "Dpad": 10 },
                  "7": { "Dpad": 5 },
                  "9": { "Dpad": 9 }
                 }

P2_directions_map = {"2": { "Dpad": 2 },
                  "4": { "Dpad": 8 },
                  "6": { "Dpad": 4 },
                  "8": { "Dpad": 1 },
                  "1": { "Dpad": 10 },
                  "3": { "Dpad": 6 },
                  "7": { "Dpad": 9 },
                  "9": { "Dpad": 5 }
                 }

direction_maps = [P1_directions_map, P2_directions_map]
direction_map_index = 0

symbols_map = direction_maps[direction_map_index%len(direction_maps)]
macros_map = {}
repetitions = REPETITIONS_DEFAULT
MyVirtual = pyxinput.vController()
sequences = [[]]
weights = [[]]


def string_to_frames(s: str):
    moves = []
    if s == '':
        s = 'W'
    if s.endswith('\n'):
        s = s[:-1]
    s = s.replace('\n', ' ')
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


def press(button, value):
    #t0 = time.perf_counter()
    MyVirtual.set_value(button, value)
    #print(time.perf_counter() - t0)
    #print("pressed:", button, "value:", value)


def release(button):
    #t0 = time.perf_counter()
    MyVirtual.set_value(button, 0)
    #print(time.perf_counter() - t0)
    #print("released:", button)


def run_frame(frame):
    frame_press_buttons = [x[0] for x in frame if x[1] != 'release']
    frame_press_buttons = [x if isinstance(x, str) else 'Dpad' for x in frame_press_buttons]
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
    # wait for the next frame
    clock.sleep()


def perform_actions(actions):
    for frame in actions:
        run_frame(frame)


def run_scenario():
    for _ in range(repetitions):
        for i, recordings in enumerate(sequences):
            if len(recordings) != 0:
                # choose a random option with probability proportional to the weight of each option
                s = sum(weights[i])
                r = random.random()*s
                accumulated = 0
                c = 0
                for j in range(len(recordings)):
                    accumulated += weights[i][j]
                    if r < accumulated:
                        c = j
                        break
                clock.reset()
                perform_actions(recordings[c])


def on_press(key):
    global direction_map_index
    # print("received", str(key))
    if str(key) == r"'\x12'":  # ctrl+r
        print("Reloading script")
        reset()
    if str(key) == r"<49>":  # ctrl+1
        direction_map_index = 0
        print("Switching to P" + str(direction_map_index+1) + " side")
    if str(key) == r"<50>":  # ctrl+2
        direction_map_index = 1
        print("Switching to P" + str(direction_map_index+1) + " side")
    if str(key) == r"<96>":
        run_scenario()
        print("Sequence complete")


def reset():
    global symbols_map
    global macros_map
    global repetitions
    global sequences
    global weights
    global resets
    resets += 1
    f = open('config.json', 'r')
    config = json.load(f)
    symbols_map = direction_maps[direction_map_index]
    symbols_map.update(config["Symbols"])
    macros_map = config["Macros"]
    repetitions = config["Repetitions"]
    recordings_file = config["Recordings_file"]
    f.close()
    sequences = [['']]
    weights = [[1]]
    f = open(recordings_file, 'r')
    i = 0
    j = 0
    for line in f:
        # ignore empty lines
        if len(line) == 0 or line.startswith('\n'):
            pass
        # ignore comment lines
        elif line.startswith(COMMENT_SYMBOL):
            pass
        elif line.startswith(MIX_START):
            i += 1
            j = -1
            sequences.append([''])
            weights.append([])
        elif line.startswith(OPTION):
            # get option weight (default is 1)
            weight = re.findall(r'\d+', line)
            if weight:
                weight = int(weight[0])
            else:
                weight = 1
            j += 1
            weights[i].append(weight)
            if j > 0:
                sequences[i].append('')
        elif line.startswith(MIX_END):
            i += 1
            j = 0
            sequences.append([''])
            weights.append([1])
        else:
            sequences[i][j] = sequences[i][j]+line

    for i in range(len(sequences)):
        for j in range(len(sequences[i])):
            sequences[i][j] = string_to_frames(sequences[i][j])
    f.close()
    print('Eddie is ready ('+str(resets)+')')


if __name__ == "__main__":
    reset()
    app = QApplication(sys.argv)

    w = QWidget()
    w.resize(250, 150)
    w.move(300, 300)
    w.setWindowTitle('EddieBot')
    w.show()
    with Listener(on_press=on_press) as listener:
        sys.exit(app.exec_())
        #listener.join()
