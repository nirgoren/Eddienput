from PyQt5.QtCore import QThreadPool

from clock import Clock
import time
import random
import json
import vcontroller
import key_emulation
import winsound
import re
import recording

START_PLAYING_SOUND = "./sounds/boop.wav"
END_PLAYING_SOUND = "./sounds/boop_low.wav"
RECORD_START_SOUND = "./sounds/recording_start.wav"
RECORD_END_SOUND = "./sounds/recording_end.wav"
# CUE_SOUND = "beep.wav"
WAIT_CONST = 'W'
NEXT_CONST = 'next'
COMMENT_SYMBOL = '#'
MIX_START = 'startmix'
OPTION = 'option'
MIX_END = 'endmix'
LOOP_START = 'loop'
LOOP_END = 'endloop'
FPS_DEFAULT = 60
EMPTY_PREFIX_FRAMES = 0
P1 = 0
P2 = 1
REPETITIONS_DEFAULT = 1
DIRECTION_MAP_INDEX_DEFAULT = P2  # default to P2 side

writer = None

fps = FPS_DEFAULT
resets = 0
clock = Clock(fps)
to_release = set()

is_playing = False
is_recording = False
mute = False
hot_reload = True
P1_directions_map = {}
P2_directions_map = {}
direction_maps = [P1_directions_map, P2_directions_map]
direction_map_index = DIRECTION_MAP_INDEX_DEFAULT

playbacks_file = ''
rec_config_file = ''
rec_config = {}
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
    try:
        winsound.PlaySound(sound, winsound.SND_ASYNC | winsound.SND_ALIAS)
    except Exception as e:
        print("Error playing sound", sound, ":", e, file=writer)


def set_button_value(button, value):
    log_queue.append((button, value, time.perf_counter()*60))
    try:
        if button in key_emulation.key_code_map:
            key_emulation.update_button_value(button, value)
        else:
            controller_state.update_state(button, value)
        # print("pressed:", button, value, time.perf_counter()*60)
    except Exception as e:
        print("Error updating button value for ", button, "with value", value, ":", e, file=writer)

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
    global is_playing
    log_queue = []
    for frame in buttons_queue:
        if is_playing:
            clock.sleep()
            for button, val in frame:
                if button.endswith('.wav'):
                    if val == 1:
                        play_sound_async(button)
                else:
                    set_button_value(button, val)
            vcontroller.set_state(controller_state)
        else:
            release_all()
    is_playing = False
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
                res.extend([WAIT_CONST for _ in range(int(frame[1:]))])
    s = ' '.join(res)
    for macro in macros_map:
        s = s.replace(macro, macros_map[macro])
    frames = s.split()
    for frame in frames:
        frame_moves = []
        splits = frame.split('+')
        i = 0
        while i < len(splits):
            command = splits[i]
            i += 1
            if command.startswith('['):
                while not command.endswith(']'):
                    command += '+' + splits[i]
                    i += 1
            elif command.startswith(']'):
                while not command.endswith('['):
                    command += '+' + splits[i]
                    i += 1
            operation = 'tap'
            if command.startswith('[') or command.startswith(']'):
                if command.startswith('['):
                    operation = 'press'
                elif command.startswith(']'):
                    operation = 'release'
                command = command[1:-1]
            buttons = command.split('+')
            for button in buttons:
                if button.startswith(WAIT_CONST):
                    pass
                else:
                    frame_moves.append((symbols_map[button], operation))
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
    for button, operation in frame:
        value = 1
        if not isinstance(button, str):
            value = direction_value_map[button['Dpad']]
            button = 'Dpad'
        if operation == 'tap':
            frame_queue.append((button, value))
            to_release.update({button})
        elif operation == 'press':
            frame_queue.append((button, value))
            to_release.discard(button)
        elif operation == 'release':
            frame_queue.append((button, 0))
    buttons_queue.append(frame_queue)


def process_playback(playback):
    for frame in playback:
        process_frame(frame)


def run_scenario():
    # for option in sequences:
    #     print(option)
    global buttons_queue
    global is_playing
    is_playing = True
    buttons_queue = []

    # set scenario prefix
    buttons_queue.extend([[]]*EMPTY_PREFIX_FRAMES)

    for _ in range(repetitions):
        for i, playbacks in enumerate(sequences):
            if len(playbacks) != 0:
                # choose a random option with probability proportional to the weight of each option
                s = sum(weights[i])
                if s == 0:
                    continue
                r = random.random()*s
                accumulated = 0
                c = None
                for j in range(len(playbacks)):
                    accumulated += weights[i][j]
                    if r < accumulated:
                        c = j
                        break
                process_playback(playbacks[c])
    print("Playing sequence", file=writer)
    clock.reset()
    if not mute:
        play_sound_async(START_PLAYING_SOUND)
    play_queue()
    if not mute:
        play_sound_async(END_PLAYING_SOUND)
    print("Sequence complete", file=writer)

def record(output_path):
    global is_recording
    is_recording = True
    print('Recording started, press select on your controller to stop', file=writer)
    play_sound_async(RECORD_START_SOUND)
    recording_output = recording.record(rec_config, direction_map_index)
    is_recording = False
    play_sound_async(RECORD_END_SOUND)
    if recording_output is not None:
        config = rec_config['config']
        writer.set_color('green')
        print('Writing recording to:', output_path, file=writer)
        writer.set_color('white')
        try:
            with open(output_path, 'w') as f:
                f.write(config + '\n')
                f.write(recording_output)
        except OSError as e:
            writer.set_color('red')
            print('Writing recording file failed:', e, file=writer)
            writer.set_color('white')


# Returns true iff the playbacks file is valid
def validate_playbacks() -> bool:
    with open(playbacks_file, 'r') as f:
        mixmode_preloop_status = False
        mix_mode = False
        awaiting_option_declaration = False
        awaiting_option_definition = False
        loop_mode = False
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
            elif line.startswith(LOOP_START):
                if loop_mode:
                    print('Line', i + 1, ': Entering loop mode while in loop mode', file=writer)
                    return False
                else:
                    loop_mode = True
                    mixmode_preloop_status = mix_mode
                    temp = line.split()
                    if len(temp) != 2:
                        print('Line', i + 1, ': Invalid loop line', file=writer)
                        return False
                    else:
                        if not (temp[1].isnumeric() and int(temp[1]) > 0):
                            print('Line', i + 1, ': Invalid loop line, loop count must be a positive integer', file=writer)
                            return False
            elif line == LOOP_END:
                if not loop_mode:
                    print('Line', i + 1, ': Exiting loop mode while not in loop mode', file=writer)
                    return False
                elif not mix_mode == mixmode_preloop_status:
                    print('Line', i + 1, ': Exiting loop mode with mismatching mix mode', file=writer)
                    return False
                else:
                    loop_mode = False
            elif line == MIX_START:
                if not mix_mode:
                    mix_mode = True
                    awaiting_option_declaration = True
                else:
                    print('Line', i+1, ': Entering mix mode while in mix mode', file=writer)
                    return False
            elif line.startswith(OPTION):
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
            elif line == MIX_END:
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
                        splits = frame.split('+')
                        j = 0
                        while j < len(splits):
                            command = splits[j]
                            # Handle [] and ][
                            j += 1
                            if command.startswith('['):
                                while j < len(splits) and not command.endswith(']'):
                                    command += '+' + splits[j]
                                    j += 1
                                if not command.endswith(']'):
                                    print('Line', i + 1, ': Did not find matching ]', file=writer)
                                    print(command)
                                    return False
                            elif command.startswith(']'):
                                while j < len(splits) and not command.endswith('['):
                                    command += '+' + splits[j]
                                    j += 1
                                if not command.endswith('['):
                                    print('Line', i + 1, ': Did not find matching [', file=writer)
                                    return False
                            if command.startswith('[') or command.startswith(']'):
                                command = command[1:-1]
                            # Split again to handle cases such as [A+B] in script
                            symbols = command.split('+')
                            for symbol in symbols:
                                if symbol.startswith('W') and symbol[1:].isnumeric():
                                    pass
                                elif symbol not in symbols_map and symbol not in direction_maps and symbol not in macros_map:
                                    print('Line', i + 1, ': Invalid symbol:', symbol, file=writer)
                                    return False
                else:
                    print('Line', i + 1, ': expecting an option definition', file=writer)
                    return False
    if mix_mode:
        print('Did not properly exit mix mode', file=writer)
        return False
    if loop_mode:
        print('Did not properly exit loop mode', file=writer)
        return False
    return True


def load_playbacks():
    global sequences
    global weights
    global resets
    writer.set_color('red')
    if not load_config():
        print('Failed to load playbacks from', playbacks_file, file=writer)
        writer.set_color('white')
        return False
    if not validate_playbacks():
        print('Failed to load playbacks from', playbacks_file, file=writer)
        writer.set_color('white')
        return False
    writer.set_color('white')

    # sequences[i][j] is the j'th option of the i'th part of the whole sequences
    sequences = []
    weights = []
    f = open(playbacks_file, 'r')
    i = 0
    j = 0
    loop_iterations = 0
    loop_counter = 0
    lines = [line for line in f]
    line_number = 1  # skip first line (config file location)
    loop_line_number = 0
    while line_number < len(lines):
        line = lines[line_number]
        line = line.strip()
        # ignore empty lines
        if len(line) == 0:
            pass
        # ignore comment lines
        elif line.startswith(COMMENT_SYMBOL):
            pass
        elif line.startswith(LOOP_START):
            # record loop line, number of iterations, reset loop counter
            loop_iterations = int(re.findall(r'\d+', line)[0])
            loop_line_number = line_number
            loop_counter = 1
        elif line.startswith(LOOP_END):
            if loop_counter < loop_iterations:
                # increase loop counter, go to first line after loop line
                loop_counter += 1
                line_number = loop_line_number + 1
                continue
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
            # append to current playback
            sequences[i][j] = sequences[i][j] + ' ' + line
        line_number += 1

    for i in range(len(sequences)):
        for j in range(len(sequences[i])):
            sequences[i][j] = string_to_frames(sequences[i][j])
    f.close()
    writer.set_color('green')
    print("Loaded playbacks from", playbacks_file, file=writer)
    resets += 1
    print('Eddie is ready ('+str(resets)+')', file=writer)
    writer.set_color('white')
    return True


def load_rec_config():
    global rec_config
    try:
        with open(rec_config_file, 'r') as f:
            rec_config = json.load(f)
    except OSError as e:
        writer.set_color('red')
        print('Failed to load recording config from', rec_config_file, ':', e, file=writer)
        writer.set_color('white')
        return False
    writer.set_color('green')
    print('Loaded recording config from', rec_config_file, file=writer)
    writer.set_color('white')
    return True


def load_config():
    global symbols_map
    global P1_directions_map
    global P2_directions_map
    global direction_maps
    global macros_map
    global repetitions
    global playbacks_file
    global fps
    global clock
    try:
        with open(playbacks_file, 'r') as f:
            config_file = f.readline().strip()
    except OSError as e:
        print("Could not read file:", playbacks_file, ':', e, file=writer)
        return False
    try:
        f = open(config_file, 'r')
    except OSError as e:
        print("Could not read file:", config_file, ':', e, file=writer)
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
    print("Loaded playback config from", config_file)
    return True


def reset():
    load_playbacks()
