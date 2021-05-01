import json

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPlainTextEdit, QTextEdit, QHBoxLayout, \
    QPushButton, QFileDialog
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QProcess
from PyQt5.QtGui import QPixmap, QTextCursor, QFont, QColor, QTextCharFormat, QBrush, QImage
from pynput.keyboard import Listener
import XInput
import sys
import traceback
from worker import Worker
import eddiecontroller


CONFIG_FILE = './config.json'
writer = None
controller_detected = False
capture_activation_key = None
sides_representation = ['Player 1', 'Player 2']

on_off_map = {
    True: 'Off',
    False: 'On'
}

manual_action_map = {
    'Key.left': ('Dpad', eddiecontroller.direction_value_map['left']),
    'Key.right': ('Dpad', eddiecontroller.direction_value_map['right']),
    'Key.up': ('Dpad', eddiecontroller.direction_value_map['up']),
    'Key.down': ('Dpad', eddiecontroller.direction_value_map['down']),
    "'q'": ('BtnShoulderL', 1),
    "'s'": ('BtnX', 1),
    "'e'": ('BtnY', 1),
    "'r'": ('BtnShoulderR', 1),
    "'a'": ('TriggerL', 1),
    "'x'": ('BtnA', 1),
    "'d'": ('BtnB', 1),
    "'f'": ('TriggerR', 1)
}

HOTKEYS_TEXT =\
    '''
  Hotkeys:

  Player 1 Side                           F1
  Player 2 Side                           F2
  Play Sequence                           F3 / Custom
  Stop Sequence                           F4
  Reload Script                           F5
  Decrease Number of Repetitions          F6
  Increase Number of Repetitions          F7
  Toggle Sequence Start/End Sound         F8
  Map Play Button                         F9
  Press Start on P2 Controller            Home Key
  Press Select on P2 Controller           End Key
  Toggle Manual P2 Control (for Mapping)  Insert Key \n\n'''

# XInput.get_connected()
LT_VALUE = -1
RT_VALUE = -2
activation_key = None
manual_mode = False
listen_to_hotkeys = True

def load_config():
    try:
        f = open(CONFIG_FILE, 'r')
        config = json.load(f)
        if 'default_recording' in config:
            default_rec = config['default_recording'].lower()
            eddiecontroller.recordings_file = default_rec
            set_recording_file(default_rec)
        if 'side' in config:
            side = config['side'].lower()
            if side == 'p1':
                set_side(0)
        if 'rec_start_end_sound' in config:
            sound = config['rec_start_end_sound'].lower()
            if sound == 'false':
                eddiecontroller.toggle_mute()
    except IOError as e:
        print('Failed to open config file:', e, file=writer)


# 0 for left side, 1 for right side
def set_side(side: int):
    eddiecontroller.direction_map_index = side
    print("Switching to " + sides_representation[side] + " side", file=writer)
    w.active_side_label.setText('Active side: ' +
                                sides_representation[side])
    eddiecontroller.reset()


def set_repetitions(reps: int):
    eddiecontroller.repetitions = reps
    print("Number of repetitions set to", eddiecontroller.repetitions, file=writer)
    w.num_repetitions_label.setText('Number of repetitions: ' + str(eddiecontroller.repetitions))


def toggle_suppress_hotkeys():
    global listen_to_hotkeys
    listen_to_hotkeys = not listen_to_hotkeys


def on_press(key):
    global capture_activation_key
    global activation_key
    if not listen_to_hotkeys:
        return
    key_val = str(key)
    #print("received", key_val)
    if key_val == "Key.f4":  # F4
        eddiecontroller.playing = False
    elif eddiecontroller.playing:
        return
    if capture_activation_key:
        capture_activation_key = False
        activation_key = key_val
        print('Playback button set to', key_val, file=writer)
        w.playback_button_label.setText('Playback button: \n' + activation_key)
    elif key_val == activation_key:
        worker = Worker(eddiecontroller.run_scenario)
        eddiecontroller.threadpool.start(worker)
        return
    if eddiecontroller.recordings_file:
        if key_val == "Key.f5":  # F5
            print("Reloading script", file=writer)
            eddiecontroller.reset()
        if key_val == "Key.f1":  # F1
            set_side(0)
        if key_val == "Key.f2":  # F2
            set_side(1)
        if key_val == "Key.f3":  # F3
            worker = Worker(eddiecontroller.run_scenario)
            eddiecontroller.threadpool.start(worker)
    if key_val == "Key.f6":  # F6
        set_repetitions(max(1, eddiecontroller.repetitions - 1))
    if key_val == "Key.f7":  # F7
        set_repetitions(min(100, eddiecontroller.repetitions + 1))
    if key_val == "Key.home":  # home
        eddiecontroller.tap_button('BtnStart', 1)
    if key_val == "Key.end":  # end
        eddiecontroller.tap_button('BtnBack', 1)
    if key_val == "Key.f8":  # F8
        eddiecontroller.toggle_mute()
        w.mute_label.setText('Start/End Sequence Sound: ' + on_off_map[eddiecontroller.mute])
    if key_val == "Key.f9":  # F9
        activation_key = None
        capture_activation_key = True
        print('Capturing playback button...', file=writer)
    if key_val == "Key.insert":  # insert
        global manual_mode
        if not manual_mode:
            print('Manual mode activated (Manual mode is not fit for playing)', file=writer)
            w.controller_image.show()
        else:
            print('Manual mode deactivated', file=writer)
            w.controller_image.hide()
            w.adjustSize()
        manual_mode = not manual_mode
    # manual control with the keyboard
    if manual_mode and not eddiecontroller.playing:
        if key_val in manual_action_map:
            eddiecontroller.tap_button(*manual_action_map[key_val])


class MyHandler(XInput.EventHandler):
    def process_button_event(self, event: XInput.Event):
        global capture_activation_key
        global activation_key
        if event.type == XInput.EVENT_BUTTON_PRESSED:
            if capture_activation_key:
                capture_activation_key = False
                activation_key = event.button_id
                print('Playback button set to', event.button, file=writer)
                w.playback_button_label.setText('Playback button: \n' + event.button)
            elif event.button_id == activation_key and eddiecontroller.recordings_file:
                if not eddiecontroller.playing:
                    worker = Worker(eddiecontroller.run_scenario)
                    eddiecontroller.threadpool.start(worker)
        pass

    def process_trigger_event(self, event):
        global capture_activation_key
        global activation_key
        LT, RT = XInput.get_trigger_values(XInput.get_state(0))
        if LT == 1.0 or RT == 1.0:
            if capture_activation_key:
                capture_activation_key = False
                activation_key = LT_VALUE if LT == 1.0 else RT_VALUE
                print('Playback button set to', 'Left Trigger' if LT == 1.0 else 'Right Trigger', file=writer)
                w.playback_button_label.setText('Playback button: \n' + ('Left Trigger' if LT == 1.0 else 'Right Trigger'))
            elif (LT == 1.0 and activation_key == -1) or (RT == 1.0 and activation_key == -2):
                if not eddiecontroller.playing:
                    worker = Worker(eddiecontroller.run_scenario)
                    eddiecontroller.threadpool.start(worker)
        pass

    def process_stick_event(self, event):
        pass

    def process_connection_event(self, event):
        pass


def set_recording_file(file_path):
    if eddiecontroller.playing:
        print("Recording currently playing, can't load new recording", file=writer)
        return
    if file_path and file_path.endswith('.txt'):
        temp = eddiecontroller.recordings_file
        eddiecontroller.recordings_file = file_path
        if eddiecontroller.load_recordings():
            w.recordings_file_label.setText('Active Recording File: \n' + eddiecontroller.recordings_file)
        else:
            eddiecontroller.recordings_file = temp

#GUI


def choose_recording_file():
    file_path = choose_file()
    set_recording_file(file_path)


def choose_file():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    dlg.setDirectory('')
    if dlg.exec_():
        filenames = dlg.selectedFiles()
        return filenames[0]


class DropFileLabel(QLabel):
    def __init__(self):
        super().__init__()
        #self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Consolas", 11, QFont.Bold))
        self.setText('\n\n\t      Drop a Recording File Here \n\n' + HOTKEYS_TEXT)
        self.setStyleSheet('''
            QLabel{
                border: 3px dashed #aaa
            }
        ''')


class TextEdit(QTextEdit):
    color = QBrush(QColor('white'))

    def set_color(self, color):
        self.color = QBrush(QColor(color))

    def append_text(self, string):
        super().moveCursor(QTextCursor.End)
        cursor = QTextCursor(super().textCursor())

        format_ = QTextCharFormat()
        format_.setForeground(QBrush(QColor(self.color)))
        cursor.setCharFormat(format_)
        cursor.insertText(string)


class Writer(QObject):
    append_text_signal = pyqtSignal(str)
    change_color_signal = pyqtSignal(str)

    def __init__(self, text_edit: TextEdit):
        super(Writer, self).__init__()
        self.text_edit = text_edit
        self.append_text_signal.connect(text_edit.append_text)
        self.change_color_signal.connect(text_edit.set_color)

    def write(self, string):
        print(string, end='')
        self.append_text_signal.emit(string)

    def set_color(self, color):
        self.change_color_signal.emit(color)


class GUI(QWidget):

    def __init__(self):
        super().__init__()
        self.resize(905, 500)
        self.setMinimumWidth(1050)
        self.setAcceptDrops(True)
        self.setWindowTitle('Eddienput v1.1')
        self.setWindowIcon(QtGui.QIcon('icon.ico'))
        self.setStyleSheet("QWidget { background-color : rgb(54, 57, 63); color : rgb(220, 221, 222); }")
        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        main_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        h_layout.addLayout(main_layout)

        # self.path_box = QTextEdit()
        # self.path_box.setMaximumHeight(25)
        # main_layout.addWidget(self.path_box)

        self.hotkeys_button = QPushButton()
        self.hotkeys_button.setText('Suppress Hotkeys')
        self.hotkeys_button.clicked.connect(toggle_suppress_hotkeys)
        self.hotkeys_button.setStyleSheet(
            "QPushButton { background-color : rgb(44, 47, 53); color : rgb(220, 221, 222); }")
        self.hotkeys_button.setCheckable(True)
        main_layout.addWidget(self.hotkeys_button)

        self.drop_file_label = DropFileLabel()
        self.drop_file_label.setMinimumWidth(455)
        main_layout.addWidget(self.drop_file_label)

        self.path_button = QPushButton()
        self.path_button.setText('Select Recording File')
        self.path_button.clicked.connect(choose_recording_file)
        self.path_button.setStyleSheet("QPushButton { background-color : rgb(44, 47, 53); color : rgb(220, 221, 222); }")
        main_layout.addWidget(self.path_button)

        self.recordings_file_label = QLabel()
        self.recordings_file_label.setText('Active Recording File: \n ---')
        main_layout.addWidget(self.recordings_file_label)

        self.playback_button_label = QLabel()
        self.playback_button_label.setText('Playback Button: \n ---')
        main_layout.addWidget(self.playback_button_label)

        self.active_side_label = QLabel()
        self.active_side_label.setText('Active Side: ' +
                                       sides_representation[eddiecontroller.direction_map_index])
        main_layout.addWidget(self.active_side_label)

        self.num_repetitions_label = QLabel()
        self.num_repetitions_label.setText('Number of Repetitions: ' + str(eddiecontroller.repetitions))
        main_layout.addWidget(self.num_repetitions_label)

        self.mute_label = QLabel()
        self.mute_label.setText('Start/End Sequence Sound: ' + on_off_map[eddiecontroller.mute])
        main_layout.addWidget(self.mute_label)

        self.text_edit = TextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMinimumWidth(450)
        self.text_edit.setStyleSheet("background-color: rgb(0, 0, 0); color: rgb(255, 255, 255);")
        h_layout.addWidget(self.text_edit)

        self.controller_image = QLabel()
        self.controller_image.setPixmap(QPixmap('eddienput_controller.png').scaledToWidth(910))
        self.controller_image.hide()
        v_layout.addWidget(self.controller_image)

        self.setLayout(v_layout)
        self.process = QProcess(self)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasText:
            event.setDropAction(Qt.CopyAction)
            file_path: str = event.mimeData().urls()[0].toLocalFile()
            set_recording_file(file_path)
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = GUI()
    writer = Writer(w.text_edit)
    eddiecontroller.writer = writer
    if XInput.get_connected()[0]:
        controller_detected = True
        print('XInput controller detected!', file=writer)
        my_handler: XInput.EventHandler = MyHandler(0)
        my_gamepad_thread = XInput.GamepadThread(my_handler)
    else:
        print('No XInput controller detected', file=writer)
    eddiecontroller.vcontroller.connect(False)
    load_config()
    w.show()
    with Listener(on_press=on_press) as listener:
        app.exec_()
        listener.stop()
        eddiecontroller.vcontroller.disconnect()
        listener.join()
