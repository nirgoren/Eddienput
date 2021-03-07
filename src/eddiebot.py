from PyQt5.QtCore import QThreadPool

from clock import Clock
import time
import random
import json
import vcontroller
import winsound
import re

START_PLAYING_SOUND = "boop.wav"
END_PLAYING_SOUND = "boop_low.wav"
QUE_SOUND = "beep.wav"
WAIT_CONST = 'W'
NEXT_CONST = 'next'
COMMENT_SYMBOL = '#'
MIX_START = 'startmix'
OPTION = 'option'
MIX_END = 'endmix'
FPS_DEFAULT = 60
EMPTY_PREFIX_FRAMES = 60
REPETITIONS_DEFAULT = 1
DIRECTION_MAP_INDEX_DEFAULT = 1  # default to P2 side

writer = None

fps = FPS_DEFAULT
resets = 0
clock = Clock(fps)
to_release = set()

playing = False
mute = False
P1_directions_map = {}
P2_directions_map = {}
direction_maps = [P1_directions_map, P2_directions_map]
direction_map_index = 1

recordings_file = ''
symbols_map = direction_maps[direction_map_index%len(direction_maps)]
macros_map = {}
repetitions = REPETITIONS_DEFAULT
controller_state = vcontroller.State()
weights = [[]]
buttons_queue = []
sequences = []
log_queue = []

direction_value_map = {
    "down": 0x2,
    "left": 0x4,
    "right": 0x8,
    "up": 0x1,
    "down_left": 0x6,
    "down_right": 0xA,
    "up_left": 0x5,
    "up_right": 0x9
}

threadpool = QThreadPool()


def toggle_mute():
    global mute
    if not mute:
        mute = True
        print('Sequence start/end sound muted', file=writer)
    else:
        mute = False
        print('Sequence start/end sound un-muted', file=writer)


def play_sound_async(sound):
    winsound.PlaySound(sound, winsound.SND_ASYNC | winsound.SND_ALIAS)


def set_button_value(button, value):
    log_queue.append((button, value, time.perf_counter()*60))
    controller_state.update_state(button, value)
    #print("pressed:", button, value, time.perf_counter()*60)


def release_all():
    controller_state.reset()
    vcontroller.set_state(controller_state)


def tap_button(button, value=1):
    set_button_value(button, value)
    vcontroller.set_state(controller_state)
    clock.reset()
    # wait a bit to make sure the button is registered (for emulators etc)
    for _ in range(3):
        clock.sleep()
    release_all()


def play_queue():
    global log_queue
    global playing
    log_queue = []
    for frame in buttons_queue:
        if playing:
            clock.sleep()
            for button, val in frame:
                if button == 'beep':
                    if val == 1:
                        play_sound_async(QUE_SOUND)
                else:
                    set_button_value(button, val)
            vcontroller.set_state(controller_state)
        else:
            release_all()
    playing = False
    # for button, val, t in log_queue:
    #     print("pressed:", button, val, t)
    return


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
            value = direction_value_map[button['Dpad']]
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
    global playing
    playing = True
    buttons_queue = []

    # set scenario prefix
    buttons_queue.extend([[]]*EMPTY_PREFIX_FRAMES)

    for _ in range(repetitions):
        for i, recordings in enumerate(sequences):
            if len(recordings) != 0:
                # choose a random option with probability proportional to the weight of each option
                s = sum(weights[i])
                if s == 0:
                    continue
                r = random.random()*s
                accumulated = 0
                c = None
                for j in range(len(recordings)):
                    accumulated += weights[i][j]
                    if r < accumulated:
                        c = j
                        break
                process_recording(recordings[c])
    print("Playing sequence", file=writer)
    clock.reset()
    if not mute:
        play_sound_async(START_PLAYING_SOUND)
    play_queue()
    if not mute:
        play_sound_async(END_PLAYING_SOUND)
    print("Sequence complete", file=writer)


# Returns true iff the recordings file is valid
def parse_recordings() -> bool:
    with open(recordings_file, 'r') as f:
        mix_mode = False
        awaiting_option_declaration = False
        awaiting_option_definition = False
        for i, line in enumerate(f):
            if i == 0:  # Skip first line (config file)
                continue
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
                    awaiting_option_declaration = True
                else:
                    print('Line', i+1, ': Entering mix mode while in mix mode', file=writer)
                    return False
            elif line.startswith('option'):
                if not mix_mode:
                    print('Line', i+1, ': Defining an option while not in mix mode', file=writer)
                    return False
                if awaiting_option_definition:
                    print('Line', i + 1, ': Defining an option while expecting option definition', file=writer)
                    return False
                temp = line.split()
                if len(temp) > 2:
                    print('Line', i+1, ': Invalid option line', file=writer)
                    return False
                elif len(temp) > 1:
                    if not temp[1].isnumeric():
                        print('Line', i + 1, ': Invalid option line, option weight must be an integer', file=writer)
                        return False
                awaiting_option_declaration = False
                awaiting_option_definition = True
            elif line == 'endmix':
                if awaiting_option_declaration:
                    print('Line', i + 1, ': Exiting mix mode while expecting option declaration', file=writer)
                    return False
                elif awaiting_option_definition:
                    print('Line', i + 1, ': Exiting mix mode while expecting option definition', file=writer)
                    return False
                elif not mix_mode:
                    print('Line', i + 1, ': Exiting mix mode while not in mix mode', file=writer)
                    return False
                else:
                    mix_mode = False
            else:
                if not awaiting_option_declaration:
                    awaiting_option_definition = False
                    frames = line.split()
                    for frame in frames:
                        commands = frame.split('+')
                        for command in commands:
                            if command.startswith('[') or command.startswith(']'):
                                command = command[1:-1]
                            if command.startswith('W') and command[1:].isnumeric():
                                pass
                            elif command not in symbols_map and command not in direction_maps and command not in macros_map:
                                print('Line', i + 1, ': Invalid symbol:', command, file=writer)
                                return False
                else:
                    print('Line', i + 1, ': expecting an option definition', file=writer)
                    return False
    if mix_mode:
        print('Did not properly exit mix mode', file=writer)
        return False
    return True


def load_recordings():
    global sequences
    global weights
    global resets
    writer.set_color('red')
    if not load_config():
        print('Failed to load recordings from', recordings_file, file=writer)
        writer.set_color('white')
        return False
    if not parse_recordings():
        print('Failed to load recordings from', recordings_file, file=writer)
        writer.set_color('white')
        return False
    writer.set_color('white')

    # sequences[i][j] is the j'th option of the i'th part of the whole sequences
    sequences = []
    weights = []
    f = open(recordings_file, 'r')
    i = 0
    j = 0

    for line_number, line in enumerate(f):
        if line_number == 0:  # skip first line (config file location)
            continue
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
    writer.set_color('green')
    print("Loaded recordings from", recordings_file, file=writer)
    resets += 1
    print('Eddie is ready ('+str(resets)+')', file=writer)
    writer.set_color('white')
    return True


def load_config():
    global symbols_map
    global P1_directions_map
    global P2_directions_map
    global direction_maps
    global macros_map
    global repetitions
    global recordings_file
    global fps
    global clock
    with open(recordings_file, 'r') as f:
        config_file = f.readline().strip()
    try:
        f = open(config_file, 'r')
    except OSError:
        print("Could not read file:", config_file, file=writer)
        return False
    config = json.load(f)
    if "FPS" in config:
        fps = config["FPS"]
    else:
        fps = FPS_DEFAULT
    clock = Clock(fps)
    P1_directions_map = config["P1_directions"]
    P2_directions_map = config["P2_directions"]
    direction_maps = [P1_directions_map, P2_directions_map]
    symbols_map = direction_maps[direction_map_index]
    symbols_map.update(config["Symbols"])
    macros_map = config["Macros"]
    print("Loaded config from", config_file)
    return True


def reset():
    load_recordings()

