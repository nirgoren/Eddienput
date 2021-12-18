from XInput import State, get_state, get_button_values, get_trigger_values, get_connected
from clock import Clock
import sys
import json

writer = None
directions = ["P1_directions", "P2_directions"]
STOP_BUTTON = "BACK"

DIRECTIONS = {
    'DPAD_UP': False,
    'DPAD_DOWN': False,
    'DPAD_LEFT': False,
    'DPAD_RIGHT': False,
    'DPAD_DOWN_LEFT': False,
    'DPAD_DOWN_RIGHT': False,
    'DPAD_UP_LEFT': False,
    'DPAD_UP_RIGHT': False
}

def record(symbol_map: dict, direction_index: int):
    c = Clock(fps=60)
    c.reset
    frames_raw = []
    connected = get_connected()
    if not connected[0]:
        print('Controller disconnected')
        return None
    while 1:
        c.sleep()
        state: State = get_state(0)
        button_values = get_button_values(state)
        # print(button_values)
        trigger_values = get_trigger_values(state)
        button_values.update({
         'LEFT_TRIGGER': False,
         'RIGHT_TRIGGER': False,
         'DPAD_DOWN_LEFT': False,
         'DPAD_DOWN_RIGHT': False,
         'DPAD_UP_LEFT': False,
         'DPAD_UP_RIGHT': False
         })
        # print(trigger_values)
        if trigger_values[0] == 1.0:
            button_values['LEFT_TRIGGER'] = True
        if trigger_values[1] == 1.0:
            button_values['RIGHT_TRIGGER'] = True
        if button_values['DPAD_DOWN'] and button_values['DPAD_LEFT']:
            button_values['DPAD_DOWN'] = False
            button_values['DPAD_LEFT'] = False
            button_values['DPAD_DOWN_LEFT'] = True
        if button_values['DPAD_DOWN'] and button_values['DPAD_RIGHT']:
            button_values['DPAD_DOWN'] = False
            button_values['DPAD_RIGHT'] = False
            button_values['DPAD_DOWN_RIGHT'] = True
        if button_values['DPAD_UP'] and button_values['DPAD_LEFT']:
            button_values['DPAD_UP'] = False
            button_values['DPAD_LEFT'] = False
            button_values['DPAD_UP_LEFT'] = True
        if button_values['DPAD_UP'] and button_values['DPAD_RIGHT']:
            button_values['DPAD_UP'] = False
            button_values['DPAD_RIGHT'] = False
            button_values['DPAD_UP_RIGHT'] = True

        if button_values[STOP_BUTTON]:
            break
        frames_raw.append(button_values)     
    
    # Parsing
    pressed = {
     'DPAD_UP': False,
     'DPAD_DOWN': False,
     'DPAD_LEFT': False,
     'DPAD_RIGHT': False,
     'DPAD_DOWN_LEFT': False,
     'DPAD_DOWN_RIGHT': False,
     'DPAD_UP_LEFT': False,
     'DPAD_UP_RIGHT': False,
     'START': False,
     'BACK': False,
     'LEFT_THUMB': False,
     'RIGHT_THUMB': False,
     'LEFT_SHOULDER': False,
     'RIGHT_SHOULDER': False,
     'LEFT_TRIGGER': False,
     'RIGHT_TRIGGER': False,
     'A': False,
     'B': False,
     'X': False,
     'Y': False
     } 

    parsed_frames = [{}]
    for frame in frames_raw:
        parsed_frame = {}
        has_direction = any(frame[direction] for direction in DIRECTIONS)
        for button in frame:
            if button in symbol_map["Symbols"] or button in symbol_map[directions[direction_index]]:
                if pressed[button] and not frame[button]:
                    pressed[button] = False
                    # If a new direction is held, do not explicitly release the previous one
                    if button not in DIRECTIONS or not has_direction:
                        parsed_frame[button] = False
                if not pressed[button] and frame[button]:
                    pressed[button] = True
                    parsed_frame[button] = True
        parsed_frames.append(parsed_frame)


    #Remove empty prefix frames
    while parsed_frames and not parsed_frames[0]:
        parsed_frames = parsed_frames[1:]

    # Compress empty frames
    compressed_frames = []
    empty_frames_count = 0
    for frame in parsed_frames:
        if frame:
            if empty_frames_count:
                compressed_frames.append({'W': empty_frames_count})
            empty_frames_count = 0
            compressed_frames.append(frame)
        else:
            empty_frames_count += 1

    # Convert to eddienput script
    result = []
    for frame in compressed_frames:
        if 'W' in frame:
            result.append('W' + str(frame['W']))
        else:
            for button in frame:
                if button in DIRECTIONS:
                    symbol = symbol_map[directions[direction_index]][button]
                else:
                    symbol = symbol_map["Symbols"][button]
                if frame[button]:
                    result.append('[' + symbol + ']')
                else:
                    result.append(']' + symbol + '[')
                result.append('+')
            result.pop()
        result.append(' ')
    s = "".join(result)

    return s


if __name__ == "__main__":
    writer = sys.stdout
    if len(sys.argv) < 2:
        exit()
    rec_config_path = sys.argv[1]
    output_path = sys.argv[2]
    with open(rec_config_path) as f:
        symbol_map = json.load(f)
    s = record(symbol_map, 0)
    config = symbol_map['config']
    print('Writing recording to:', output_path, file=writer)
    with open(output_path, 'w') as f:
        f.write(config + '\n')
        f.write(s)