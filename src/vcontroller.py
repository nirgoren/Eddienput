from ctypes import *

_vcontroller = WinDLL('vcontroller.dll')

buttons = {
'Dpad'                  : 0x0001,
'BtnStart'              : 0x0010,
'BtnBack'               : 0x0020,
'BtnThumbL'             : 0x0040,
'BtnThumbR'             : 0x0080,
'BtnShoulderL'          : 0x0100,
'BtnShoulderR'          : 0x0200,
'Home'                  : 0x0400,
'BtnA'                  : 0x1000,
'BtnB'                  : 0x2000,
'BtnX'                  : 0x4000,
'BtnY'                  : 0x8000
}


class State:
    state_value = 0x0000

    def update_state(self, button, value):
        base = buttons[button]
        if base == 0x0001:  # Dpad case
            mask = 0xfff0
        else:
            mask = 0xffff ^ base
        rest = self.state_value & mask
        self.state_value = rest + base * value


def connect():
    return _vcontroller.connect()


def set_state(state):
    return _vcontroller.set_state(state.state_value)


def disconnect():
    return _vcontroller.disconnect()
