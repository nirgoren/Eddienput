from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtGui import QPixmap
from pynput.keyboard import Listener
import XInput
import sys
import traceback
from worker import Worker
import eddiebot


capture_activation_key = False

HOTKEYS_TEXT =\
    '''Hotkeys:
    Reload script - ctrl+r
    P1 side - ctrl+1
    P2 side - ctrl+2
    Increase number of repetitions - (ctrl+"=")
    Decrease number of repetitions - (ctrl+"-")
    Press start on P2 controller - Home key
    Play sequence - numkey0 or ctrl+p
    Stop sequence - ctrl+x 
    Map play button - ctrl+a
    Toggle sequence start/end sound \n\n'''

XInput.get_connected()
LT_VALUE = -1
RT_VALUE = -2
activation_key = None


def on_press(key):
    #print("received", str(key))
    if str(key) == r"'\x18'":
        eddiebot.playing = False
    elif eddiebot.playing:
        return
    if str(key) == r"'\x12'":  # ctrl+r
        print("Reloading script")
        eddiebot.reset()
    if str(key) == r"<49>":  # ctrl+1
        eddiebot.direction_map_index = 0
        print("Switching to P" + str(eddiebot.direction_map_index + 1) + " side")
        eddiebot.reset()
    if str(key) == r"<50>":  # ctrl+2
        eddiebot.direction_map_index = 1
        eddiebot.reset()
        print("Switching to P" + str(eddiebot.direction_map_index + 1) + " side")
    if str(key) == r"<189>":  # minus
        eddiebot.repetitions = max(1, eddiebot.repetitions - 1)
        print("Number of repetitions set to", eddiebot.repetitions)
    if str(key) == r"<187>":  # plus
        eddiebot.repetitions = min(100, eddiebot.repetitions + 1)
        print("Number of repetitions set to", eddiebot.repetitions)
    if str(key) == r"<96>" or str(key) == r"'\x10'":  # numpad0 or ctrl+p
        worker = Worker(eddiebot.run_scenario)
        eddiebot.threadpool.start(worker)
    if str(key) == "Key.home":  # home
        eddiebot.tap_button('BtnStart', 1)
        print("Pressed start")
    if str(key) == r"'\r'":  # ctrl+m
        eddiebot.toggle_mute()
    if str(key) == r"'\x01'":  # ctrl+m
        global capture_activation_key
        global activation_key
        activation_key = None
        capture_activation_key = True
        print("Capturing activation key...")
    # if str(key) == "Key.right":
    #     eddiebot.tap_button('Dpad', 8)


class MyHandler(XInput.EventHandler):
    def process_button_event(self, event: XInput.Event):
        global capture_activation_key
        global activation_key
        if event.type == XInput.EVENT_BUTTON_PRESSED:
            print(event.button_id)
            if capture_activation_key:
                capture_activation_key = False
                activation_key = event.button_id
                print('Activation key set to', event.button)
            elif event.button_id == activation_key:
                if not eddiebot.playing:
                    worker = Worker(eddiebot.run_scenario)
                    eddiebot.threadpool.start(worker)
        pass

    def process_trigger_event(self, event):
        global capture_activation_key
        global activation_key
        LT, RT = XInput.get_trigger_values(XInput.get_state(0))
        #print(LT, RT)
        if LT == 1.0 or RT == 1.0:
            if capture_activation_key:
                capture_activation_key = False
                activation_key = LT_VALUE if LT == 1.0 else RT_VALUE
                print('Activation key set to', 'Left Trigger' if LT == 1.0 else 'Right Trigger')
            elif (LT == 1.0 and activation_key == -1) or (RT == 1.0 and activation_key == -2):
                if not eddiebot.playing:
                    worker = Worker(eddiebot.run_scenario)
                    eddiebot.threadpool.start(worker)
        pass

    def process_stick_event(self, event):
        pass

    def process_connection_event(self, event):
        pass


class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setText('\n\n Drop a Recording File Here \n\n' + HOTKEYS_TEXT)
        self.setStyleSheet('''
            QLabel{
                border: 4px dashed #aaa
            }
        ''')


class GUI(QWidget):

    def __init__(self):
        super().__init__()
        self.resize(500, 500)
        self.setAcceptDrops(True)
        self.setWindowTitle('EddieBot')
        main_layout = QVBoxLayout()

        self.photoViewer = ImageLabel()
        main_layout.addWidget(self.photoViewer)
        self.setLayout(main_layout)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        if eddiebot.playing:
            print("Recording currently playing, can't load new recording")
            return
        if event.mimeData().hasText:
            event.setDropAction(Qt.CopyAction)
            file_path: str = event.mimeData().urls()[0].toLocalFile()
            if file_path.endswith('.txt'):
                eddiebot.recordings_file = file_path
                eddiebot.load_recordings()
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    # redirect stdout https://gist.github.com/rbonvall/9982648
    if XInput.get_connected()[0]:
        print('XInput controller detected')
        my_handler: XInput.EventHandler = MyHandler(0)
        my_gamepad_thread = XInput.GamepadThread(my_handler)
    eddiebot.vcontroller.connect()
    app = QApplication(sys.argv)
    w = GUI()
    w.show()
    with Listener(on_press=on_press) as listener:
        app.exec_()
        listener.stop()
        eddiebot.vcontroller.disconnect()
        listener.join()
