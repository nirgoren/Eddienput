import os
from pathlib import Path
import sys
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    ROOT_DIR = Path(sys._MEIPASS).parent
else:
    ROOT_DIR = Path(__file__).parent
os.chdir(ROOT_DIR)