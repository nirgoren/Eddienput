import ctypes
from ctypes import wintypes
import time
user32 = ctypes.WinDLL('user32', use_last_error=True)
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
MAPVK_VK_TO_VSC = 0
# msdn.microsoft.com/en-us/library/dd375731
wintypes.ULONG_PTR = wintypes.WPARAM
class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))
class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))
    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)
class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))
class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))
LPINPUT = ctypes.POINTER(INPUT)
def press_key(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=hexKeyCode))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
def release_key(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=hexKeyCode, dwFlags=KEYEVENTF_KEYUP))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def to_key_code(c):
    keyCode = key_code_map[c]
    return keyCode

# https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN
key_code_map = {
    'shift'             : 0x10,
    '0'                 : 0x30,
    '1'                 : 0x31,
    '2'                 : 0x32,
    '3'                 : 0x33,
    '4'                 : 0x34,
    '5'                 : 0x35,
    '6'                 : 0x36,
    '7'                 : 0x37,
    '8'                 : 0x38,
    '9'                 : 0x39,
    'a'                 : 0x41,
    'b'                 : 0x42,
    'c'                 : 0x43,
    'd'                 : 0x44,
    'e'                 : 0x45,
    'f'                 : 0x46,
    'g'                 : 0x47,
    'h'                 : 0x48,
    'i'                 : 0x49,
    'j'                 : 0x4A,
    'k'                 : 0x4B,
    'l'                 : 0x4C,
    'm'                 : 0x4D,
    'n'                 : 0x4E,
    'o'                 : 0x4F,
    'p'                 : 0x50,
    'q'                 : 0x51,
    'r'                 : 0x52,
    's'                 : 0x53,
    't'                 : 0x54,
    'u'                 : 0x55,
    'v'                 : 0x56,
    'w'                 : 0x57,
    'x'                 : 0x58,
    'y'                 : 0x59,
    'z'                 : 0x5A,
    'numpad_enter'      : 0x9C + 1024,
    'numpad_1'          : 0x61,
    'numpad_2'          : 0x62,
    'numpad_3'          : 0x63,
    'numpad_4'          : 0x64,
    'numpad_5'          : 0x65,
    'numpad_6'          : 0x66,
    'numpad_7'          : 0x67,
    'numpad_8'          : 0x68,
    'numpad_9'          : 0x69,
    'numpad_0'          : 0x60,
    '-'                 : 0x6D,
    '+'                 : 0x6B,
    'left'              : 0x25,
    'up'                : 0x26,
    'right'             : 0x27,
    'down'              : 0x28,
    'space'             : 0x08,
    'enter'             : 0x0D
}
