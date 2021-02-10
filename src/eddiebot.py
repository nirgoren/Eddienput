from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pynput.keyboard import Key, Listener, Controller, KeyCode
from clock import Clock
import time
import random
import json
import pyxinput  # requires installation: https://github.com/shauleiz/vXboxInterface/releases
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
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

config_file = 'config.json'
recordings_file = None
symbols_map = direction_maps[direction_map_index%len(direction_maps)]
macros_map = {}
repetitions = REPETITIONS_DEFAULT
virtual_controller = pyxinput.vController()
sequences = [[]]
weights = [[]]
buttons_queue = []
log_queue = []


def set_button_value(button, value):
    log_queue.append((button, value, time.perf_counter()*60))
    virtual_controller.set_value(button, value)
    #print("pressed:", button, value, time.perf_counter()*60)


def play_queue():
    global log_queue
    log_queue = []
    for frame in buttons_queue:
        clock.sleep()
        for button, val in frame:
            set_button_value(button, val)
    # for button, val, t in log_queue:
    #     print("pressed:", button, val, t)


# parse a string into a series of frame commands
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


# press/release the inputs for the given frame
def process_frame(frame):
    global buttons_queue
    frame_queue = []
    # wait for the next frame
    frame_press_buttons = [x[0] for x in frame if x[1] != 'release']
    frame_press_buttons = [x if isinstance(x, str) else 'Dpad' for x in frame_press_buttons]
    released = set()

    for button in to_release:
        if button not in frame_press_buttons:
            frame_queue.append((button, 0))
            released.update({button})
    for button in released:
        to_release.discard(button)
    for button, command in frame:
        value = 1
        if not isinstance(button, str):
            value = button['Dpad']
            button = 'Dpad'
        if command == 'tap':
            frame_queue.append((button, value))
            to_release.update({button})
        elif command == 'press':
            frame_queue.append((button, value))
            to_release.discard(button)
        elif command == 'release':
            frame_queue.append((button, 0))
    buttons_queue.append(frame_queue)


def process_recording(recordings):
    for frame in recordings:
        process_frame(frame)


def run_scenario():
    # for option in sequences:
    #     print(option)
    global buttons_queue
    buttons_queue = []
    for _ in range(repetitions):
        for i, recordings in enumerate(sequences):
            if len(recordings) != 0:
                # choose a random option with probability proportional to the weight of each option
                s = sum(weights[i])
                r = random.random()*s
                accumulated = 0
                c = None
                for j in range(len(recordings)):
                    accumulated += weights[i][j]
                    if r < accumulated:
                        c = j
                        break
                process_recording(recordings[c])
    clock.reset()
    play_queue()

def load_recordings():
    global sequences
    global weights
    # sequences[i][j] is the j'th option of the i'th part of the whole sequences
    sequences = []
    weights = []
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
            if i < len(sequences):
                i += 1
            j = -1
            sequences.append([])
            weights.append([])
        elif line.startswith(OPTION):
            # get option weight (default is 1)
            weight = re.findall(r'\d+', line)
            if weight:
                weight = int(weight[0])
            else:
                weight = 1
            weights[i].append(weight)
            sequences[i].append('')
            j += 1
        elif line.startswith(MIX_END):
            i += 1
            j = 0
        else:
            if len(sequences) == i:
                sequences.append([''])
                weights.append([1])
            # append to current recording
            sequences[i][j] = sequences[i][j]+line

    for i in range(len(sequences)):
        for j in range(len(sequences[i])):
            sequences[i][j] = string_to_frames(sequences[i][j])
    f.close()
    print("loaded recordings from", recordings_file)


def reset():
    global symbols_map
    global macros_map
    global repetitions
    global resets
    global recordings_file
    f = open(config_file, 'r')
    config = json.load(f)
    symbols_map = direction_maps[direction_map_index]
    symbols_map.update(config["Symbols"])
    macros_map = config["Macros"]
    if resets == 0:
        repetitions = config["Repetitions"]
        recordings_file = config["Recordings_file"]
    f.close()
    print("Loaded config from", config_file)
    load_recordings()
    resets += 1
    print('Eddie is ready ('+str(resets)+')')

def on_press(key):
    global direction_map_index
    global repetitions
    # print("received", str(key))
    if str(key) == r"'\x12'":  # ctrl+r
        print("Reloading script")
        reset()
    if str(key) == r"<49>":  # ctrl+1
        direction_map_index = 0
        print("Switching to P" + str(direction_map_index+1) + " side")
        reset()
    if str(key) == r"<50>":  # ctrl+2
        direction_map_index = 1
        reset()
        print("Switching to P" + str(direction_map_index+1) + " side")
    if str(key) == r"<189>":  # minus
        repetitions = max(1, repetitions-1)
        print("Number of repetitions set to", repetitions)
    if str(key) == r"<187>":  # plus
        repetitions = min(20, repetitions+1)
        print("Number of repetitions set to", repetitions)
    if str(key) == r"<96>" or str(key) == r"'\x10'":  # numpad0 or ctrl+p
        run_scenario()
        print("Sequence complete")
    if str(key) == "Key.home":  # home
        set_button_value('BtnStart', 1)
        clock.reset()
        clock.sleep()
        release('BtnStart')
        print("Pressed start")

# GUI stuff
class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setText('\n\n Drop a Config or Recording File Here \n\n')
        self.setStyleSheet('''
            QLabel{
                border: 4px dashed #aaa
            }
        ''')

class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(400, 400)
        self.setAcceptDrops(True)
        self.setWindowTitle('EddieBot')
        mainLayout = QVBoxLayout()

        self.photoViewer = ImageLabel()
        mainLayout.addWidget(self.photoViewer)
        self.setLayout(mainLayout)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        global recordings_file
        global config_file
        if event.mimeData().hasText:
            event.setDropAction(Qt.CopyAction)
            file_path: str = event.mimeData().urls()[0].toLocalFile()
            if file_path.endswith('.json'):
                config_file = file_path
                reset()
            elif file_path.endswith('.txt'):
                recordings_file = file_path
                load_recordings()
            else:
                print("Invalid suffix (valid options are .json for a config file and .txt for recordings file")
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    reset()
    app = QApplication(sys.argv)
    w = GUI()
    w.show()
    with Listener(on_press=on_press) as listener:
        sys.exit(app.exec_())
        #listener.join()
