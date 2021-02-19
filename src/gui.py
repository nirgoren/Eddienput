from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtGui import QPixmap
from pynput.keyboard import Listener
import XInput
import sys
import traceback
from worker import Worker
import eddiebot


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
    Toggle sequence start/end sound \n\n'''

XInput.get_connected()


def on_press(key):
    print("received", str(key))
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
    # if str(key) == "Key.right":
    #     eddiebot.tap_button('Dpad', 8)


class MyHandler(XInput.EventHandler):
    def process_button_event(self, event: XInput.Event):
        # if not eddiebot.playing:
        #     worker = Worker(eddiebot.run_scenario)
        #     eddiebot.threadpool.start(worker)
        pass

    def process_trigger_event(self, event):
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
        my_handler.set_filter(XInput.BUTTON_RIGHT_SHOULDER + XInput.FILTER_PRESSED_ONLY)
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
