from clock import Clock
import time
import random
import json
import vcontroller
from playsound import playsound
import re

START_PLAYING_SOUND = 'boop.mp3'
END_PLAYING_SOUND = 'boop_low.mp3'
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

P1_directions_map = {}
P2_directions_map = {}
direction_maps = [P1_directions_map, P2_directions_map]
direction_map_index = 0

config_file = 'config.json'
recordings_file = ''
symbols_map = direction_maps[direction_map_index%len(direction_maps)]
macros_map = {}
repetitions = REPETITIONS_DEFAULT
controller_state = vcontroller.State()
weights = [[]]
buttons_queue = []
sequences = []
log_queue = []


def set_button_value(button, value):
    log_queue.append((button, value, time.perf_counter()*60))
    controller_state.update_state(button, value)
    #print("pressed:", button, value, time.perf_counter()*60)


def play_queue():
    global log_queue
    log_queue = []
    for frame in buttons_queue:
        clock.sleep()
        for button, val in frame:
            set_button_value(button, val)
        vcontroller.set_state(controller_state)
    # for button, val, t in log_queue:
    #     print("pressed:", button, val, t)


# parse a string into a series of frame commands
def string_to_frames(s: str):
    moves = []
    if s == '':
        s = 'W'
    frames = s.split()
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
    frames = s.split()
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
    print("Playing sequence")
    playsound(START_PLAYING_SOUND)
    clock.reset()
    play_queue()
    playsound(END_PLAYING_SOUND)
    print("Sequence complete")


# Returns true iff the recordings file is valid
def parse_recordings() -> bool:
    with open(recordings_file, 'r') as f:
        mix_mode = False
        for i, line in enumerate(f):
            line = line.strip()
            # ignore empty lines
            if len(line) == 0:
                pass
            # ignore comment lines
            elif line.startswith(COMMENT_SYMBOL):
                pass
            elif line == 'startmix':
                if not mix_mode:
                    mix_mode = True
                else:
                    print('Line', i+1, ': Entering mix mode while in mix mode')
                    return False
            elif line.startswith('option'):
                if not mix_mode:
                    print('Line', i+1, ': Defining an option while not in mix mode')
                    return False
                temp = line.split()
                if len(temp) > 2:
                    print('Line', i+1, ': Invalid option line')
                    return False
                elif len(temp) > 1:
                    if not temp[1].isnumeric():
                        print('Line', i + 1, ': Invalid option line, option weight must be an integer')
                        return False
            elif line == 'endmix':
                if mix_mode:
                    mix_mode = False
                else:
                    print('Line', i + 1, ': Exiting mix mode while in not in mix mode')
                    return False
            else:
                frames = line.split()
                for frame in frames:
                    commands = frame.split('+')
                    for command in commands:
                        if command.startswith('[') or command.startswith(']'):
                            command = command[1:-1]
                        if command.startswith('W') and command[1:].isnumeric():
                            pass
                        elif command not in symbols_map and command not in direction_maps and command not in macros_map:
                            print('Line', i + 1, ': Invalid symbol:', command)
                            return False
    if mix_mode:
        print('Did not properly exit mix mode')
        return False
    return True


def load_recordings():
    if not parse_recordings():
        print('Did not load recordings from', recordings_file)
        return
    global sequences
    global weights
    # sequences[i][j] is the j'th option of the i'th part of the whole sequences
    sequences = []
    weights = []
    f = open(recordings_file, 'r')
    i = 0
    j = 0
    for line in f:
        line = line.strip()
        # ignore empty lines
        if len(line) == 0:
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
            sequences[i][j] = sequences[i][j] + ' ' + line

    for i in range(len(sequences)):
        for j in range(len(sequences[i])):
            sequences[i][j] = string_to_frames(sequences[i][j])
    f.close()
    print("loaded recordings from", recordings_file)


def reset():
    global symbols_map
    global P1_directions_map
    global P2_directions_map
    global direction_maps
    global macros_map
    global repetitions
    global resets
    global recordings_file
    f = open(config_file, 'r')
    config = json.load(f)
    P1_directions_map = config["P1_directions"]
    P2_directions_map = config["P2_directions"]
    direction_maps = [P1_directions_map, P2_directions_map]
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



