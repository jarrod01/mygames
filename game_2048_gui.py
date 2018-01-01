from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from game_2048 import *

class Game2048(QMainWindow):
    def __init__(self):
        super().__init__()
        self.score = 0
        self.dead = False
        self.numbers = []
        self.level = 0
        self.initUI()

    def initUI(self):
        pass