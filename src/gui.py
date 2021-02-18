from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtGui import QPixmap
from pynput.keyboard import Listener
import sys
import traceback
import eddiebot

# GUI stuff

#https://www.learnpyqt.com/tutorials/multithreading-pyqt-applications-qthreadpool/

HOTKEYS_TEXT =\
    '''Hotkeys:
    Reload script - ctrl+r
    P1 side - ctrl+1
    P2 side - ctrl+2
    Increase number of repetitions - (ctrl+"=")
    Decrease number of repetitions - (ctrl+"-")
    Play sequence - numkey0 or ctrl+p \n\n'''

threadpool = QThreadPool()


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
        eddiebot.repetitions = min(20, eddiebot.repetitions + 1)
        print("Number of repetitions set to", eddiebot.repetitions)
    if str(key) == r"<96>" or str(key) == r"'\x10'":  # numpad0 or ctrl+p
        worker = Worker(eddiebot.run_scenario)
        threadpool.start(worker)

        #eddiebot.run_scenario()
    # if str(key) == "Key.home":  # home
    #     set_button_value('BtnStart', 1)
    #     clock.reset()
    #     clock.sleep()
    #     set_button_value('BtnStart', 0)
    #     print("Pressed start")


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setText('\n\n Drop a Config or Recording File Here \n\n' + HOTKEYS_TEXT)
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
        mainLayout = QVBoxLayout()

        self.photoViewer = ImageLabel()
        mainLayout.addWidget(self.photoViewer)
        self.setLayout(mainLayout)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasText:
            event.setDropAction(Qt.CopyAction)
            file_path: str = event.mimeData().urls()[0].toLocalFile()
            if file_path.endswith('.json'):
                eddiebot.config_file = file_path
                eddiebot.reset()
            elif file_path.endswith('.txt'):
                eddiebot.recordings_file = file_path
                eddiebot.load_recordings()
            else:
                print("Invalid suffix (valid options are .json for a config file and .txt for recordings file")
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    eddiebot.vcontroller.connect()
    eddiebot.reset()
    app = QApplication(sys.argv)
    w = GUI()
    w.show()
    with Listener(on_press=on_press) as listener:
        app.exec_()
        listener.stop()
        eddiebot.vcontroller.disconnect()
        listener.join()
