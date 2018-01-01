from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from game_2048 import *
import copy as cp
import random
import sys


class Game2048Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.InitUI()

    def InitUI(self):
        menubar = self.menuBar()
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        recordsAction = QAction('&Records', self)
        recordsAction.setShortcut('Ctrl+R')
        recordsAction.setStatusTip('Show your records')
        recordsAction.triggered.connect(self.close)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(recordsAction)
        fileMenu.addAction(exitAction)

        start_number_menu = QMenu('StartNumber', self)
        sn0 = QAction('original', self)
        sn1024 = QAction('1024', self)
        sn2048 = QAction('2048', self)
        sn4096 = QAction('4096', self)
        sn8192 = QAction('8192', self)
        start_number_menu.addAction(sn1024)
        start_number_menu.addAction(sn2048)
        start_number_menu.addAction(sn4096)
        start_number_menu.addAction(sn8192)

        level_menu = QMenu('Level', self)
        for i in range(1,7):
            level_tmp = QAction(str(i), self)
            level_menu.addAction(level_tmp)

        settingMenu = menubar.addMenu('&Settings')
        settingMenu.addMenu(start_number_menu)
        settingMenu.addMenu(level_menu)
        menubar.setNativeMenuBar(False)

        game = Game2048(self)
        self.setCentralWidget(game)
        self.center()
        self.setFixedSize(540, 600)
        self.show()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width()-size.width())/2),
            int((screen.height()-size.height())/2))



class Game2048(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.score = 0
        self.dead = False
        self.numbers = []
        self.level = 0
        self.start_number = 0
        self.initUI()
        self.parent = parent

    def initUI(self):
        hbox = QHBoxLayout(self)
        vbox = QVBoxLayout(self)

        self.topleft = QLabel('当前分数：', self)
        # self.topleft.setFrameShape(QFrame.StyledPanel)
        self.topleft.move(30, 5)
        self.topleft.setFixedSize(210, 50)

        self.topright = QLabel('最高分数：20000', self)
        # self.topright.setFrameShape(QFrame.StyledPanel)
        self.topright.setFixedSize(210, 50)
        self.topright.move(300, 5)

        self.bottom = GameCanvas(self)
        self.bottom.setFixedSize(500, 500)
        self.bottom.move(20, 80)

        self.setWindowTitle("2048")
        self.resize(540, 600)
        # self.center()
        self.show()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width()-size.width())/2),
            int((screen.height()-size.height())/2))

    def keyPressEvent(self, QKeyEvent):
        self.bottom.keyPressEvent(QKeyEvent)


class GameCanvas(QLabel):
    # 只读的背景16个方格
    item_bgs = []
    # 背景16个方格的xy位置也是只读的
    item_bg_pos = []
    item_data = []

    parent_x = 20
    parent_y = 80
    split_width = 16
    rect_width = 105

    def __init__(self, parent):
        super(GameCanvas, self).__init__(parent)
        self.parent = parent

        # self.resize(500, 500)
        self.move(self.parent_x, self.parent_y)
        self.setStyleSheet("QLabel{background-color:#bbada0;color:#bbada0;border-radius:6}")

        self.setFocusPolicy(Qt.StrongFocus)
        self.set_item_bg()
        self.set_init_rect()

    def set_init_rect(self):
        self.game_initializer()

    # 设置背景，将所有的item设置为{'item':None ,'number':0}
    def set_item_bg(self):
        for i in range(1, 5):
            bgs = []
            pos = []
            ds = []
            for j in range(1, 5):
                x = self.parent_x + self.split_width * j + self.rect_width * (j - 1)
                y = self.parent_y + self.split_width * i + self.rect_width * (i - 1)
                label = QLabel(self.parent)
                label.resize(self.rect_width, self.rect_width)
                label.move(x, y)
                label.setStyleSheet("QLabel{background-color:#cdc1b4;color:#cdc1b4;border-radius:3}")
                bgs.append(label)
                pos.append({"x": x, "y": y})
                ds.append({"Item": None, "Number": 0})
            self.item_bgs.append(bgs)
            self.item_bg_pos.append(pos)
            self.item_data.append(ds)

    def random_rect_item(self):
        zero_ds = []
        for i in range(0, 4):
            for j in range(0, 4):
                if self.item_data[i][j]["Number"] == 0:
                    zero_ds.append({"i": i, "j": j})

        if len(zero_ds) > 0:
            rnd = int(random.uniform(0, len(zero_ds)))
            k = int(random.uniform(0, 10))
            number = 2
            if k == 2 or k == 10:
                number = 4
            d = zero_ds[rnd]
            d["num"] = number
            d["x"] = self.item_bg_pos[d["i"]][d["j"]]["x"]
            d["y"] = self.item_bg_pos[d["i"]][d["j"]]["y"]

            rect = NumberRect(self.parent, self.rect_width, d)
            self.item_data[d["i"]][d["j"]]["Number"] = number
            self.item_data[d["i"]][d["j"]]["Item"] = rect
            rect.show()

            return self.item_data[d["i"]][d["j"]]
        else:
            pass
        return None

    def game_initializer(self):
        level = self.parent.level
        start_number = self.parent.start_number
        indexes = []
        for i in range(4):
            for j in range(4):
                indexes.append({'i': i, 'j': j})
        d = random.sample(indexes, 1)
        # 根据初始数字和级别随机生成2个数字
        if start_number:
            d = {'num': start_number}
            d["x"] = self.item_bg_pos[d["i"]][d["j"]]["x"]
            d["y"] = self.item_bg_pos[d["i"]][d["j"]]["y"]

            rect = NumberRect(self.parent, self.rect_width, d)
            self.item_data[d["i"]][d["j"]]["Number"] = start_number
            self.item_data[d["i"]][d["j"]]["Item"] = rect
            rect.show()
        else:
            self.random_rect_item()
        self.random_rect_item()

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Up:
            self.reset_rect(1)
        elif QKeyEvent.key() == Qt.Key_Down:
            self.reset_rect(2)
        elif QKeyEvent.key() == Qt.Key_Left:
            self.reset_rect(3)
        elif QKeyEvent.key() == Qt.Key_Right:
            self.reset_rect(4)

    def reset_rect(self, direction):
        # print("方向:" + str(direction))
        items = []
        for i in range(0, 4):
            for j in range(0, 4):
                item = self.item_data[i][j]["Item"]
                if item:
                    items.append(item)

        calculate = GameCalculate(self.item_data)
        calculate.calculate(direction)
        self.item_data = calculate.get_data()

        # for d in self.item_data:
        #     print(d)
        # for p in self.item_bg_pos:
        #     print(p)

        self.redraw_rect(items)
        # self.check_is_win()
        # dead = self.check_is_dead()
        dead = False
        if dead:
            reply = QMessageBox.question(self.parent, '提示信息',
                                         "您已经输了，是否重新开始?", QMessageBox.Yes, QMessageBox.No)
            # if reply == QMessageBox.Yes:
            #     print("OK")
            # else:
            #     print("NO")
        self.random_rect_item()

    def redraw_rect(self, items):
        for i in range(0, 4):
            for j in range(0, 4):
                item = self.item_data[i][j]["Item"]
                if item:
                    items.remove(item)
                    x = self.item_bg_pos[i][j]["x"]
                    y = self.item_bg_pos[i][j]["y"]
                    ds = item.ds
                    ds["x"] = x
                    ds["y"] = y
                    ds["num"] = self.item_data[i][j]["Number"]
                    item.refresh_ds(ds)
        for k in items:
            if k: k.hide()
        del items

    def check_is_win(self):
        for i in range(0, 4):
            for j in range(0, 4):
                item = self.item_data[i][j]["Item"]
                if item and item.ds["num"] == 2048:
                    reply = QMessageBox.question(self.parent, '提示信息',
                                                 "真牛逼，你已经赢了是否继续往上挑战？", QMessageBox.Yes, QMessageBox.No)
                    # if reply == QMessageBox.Yes:
                    #     print("OK")
                    # else:
                    #     print("NO")

    def check_is_dead(self):
        dead = True
        for i in range(1, 5):
            tmp_data = cp.deepcopy(self.item_data)
            calculate = GameCalculate(tmp_data)
            calculate.calculate(direction=i)
            dead = calculate.get_dead_status()
            if not dead:
                break
        return dead



class NumberRect(QLabel):
    animation = None

    color_dict = {"2": "#eee4da", "4": "#ede0c8", "8": "#f2b179", "16": "#f59563", "32": "#f67c5f",
                  "64": "#f65e3b", "128": "#edcf72", "256": "#edcc61", "512": "#EFCB52",
                  "1024": "#EFC739", "2048": "#EFC329", "4096": "#FF3C39", "8192": "#800080"}

    font_color_dict = {"2": "#776e65", "4": "#776e65", "8": "#ffffff", "16": "#ffffff", "32": "#ffffff",
                       "64": "#ffffff", "128": "#ffffff", "256": "#776e65", "512": "#776e65",
                       "1024": "#776e65", "2048": "#776e65", "4096": "#ffffff", "8192": "#ffffff"}

    def __init__(self, parent, width, ds):
        super(NumberRect, self).__init__(parent)
        self.ds = ds
        self.w = width

        self.resize(width, width)
        self.setFont(QFont("\"Clear Sans\", \"Helvetica Neue\", Arial, sans-serif", 55, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)
        self.refresh_ds(ds)

    def refresh_ds(self, ds):
        self.ds = ds
        self.setText(str(ds["num"]))
        self.move(ds["x"], ds["y"])
        color = self.color_dict[str(ds["num"])]
        font_color = self.font_color_dict[str(ds["num"])]
        self.setStyleSheet("QLabel{background-color:" + color + ";color:" + font_color + ";border-radius:3}")
        font_size = 55
        if 100 <= ds["num"] <= 999: font_size = 40
        if 1000 <= ds["num"] <= 9999: font_size = 30
        if 10000 <= ds["num"] <= 99999: font_size = 20
        self.setFont(QFont("\"Clear Sans\", \"Helvetica Neue\", Arial, sans-serif", font_size, QFont.Bold))

    def move_animation(self):
        self.animation = QPropertyAnimation(self, "pos".encode())
        self.animation.setDuration(150)
        self.animation.setStartValue(QPoint(0, 0))
        self.animation.setEndValue(QPoint(300, 300))
        self.animation.setEasingCurve(QEasingCurve.Linear)
        self.animation.start(QAbstractAnimation.DeleteWhenStopped)

    def combine_animation(self):
        self.animation = QPropertyAnimation(self, "size".encode())
        self.animation.setDuration(150)
        self.animation.setStartValue(QSize(107, 107))
        self.animation.setEndValue(QSize(300, 300))
        self.animation.setEasingCurve(QEasingCurve.Linear)
        self.animation.finished.connect(self.finish_com_anim)
        self.animation.start(QAbstractAnimation.DeleteWhenStopped)

    def finish_com_anim(self):
        self.animation = QPropertyAnimation(self, "size".encode())
        self.animation.setDuration(150)
        self.animation.setStartValue(QSize(300, 300))
        self.animation.setEndValue(QSize(107, 107))
        self.animation.setEasingCurve(QEasingCurve.Linear)
        self.animation.start(QAbstractAnimation.DeleteWhenStopped)


class GameCalculate():
    def __init__(self, item_data):
        self.data = item_data
        self.dead = True

    def calculate(self, direction):
        if len(self.data) <= 0:
            return 0
        if direction == 1:
            self.up_run()
        if direction == 2:
            self.down_run()
        if direction == 3:
            self.left_run()
        if direction == 4:
            self.right_run()

    def get_data(self):
        return self.data

    def up_run(self):
        for i in range(0, 4):
            k = None
            for j in range(0, 4):
                l = self.data[j][i]
                if k and l["Number"] != 0:
                    k_v = self.data[k["j"]][k["i"]]
                    if k_v["Number"] == l["Number"]:
                        self.data[k["j"]][k["i"]]["Number"] = k_v["Number"] + l["Number"]
                        self.data[j][i] = {"Item": None, "Number": 0}
                        k = None
                        self.dead = False
                    else:
                        if l["Number"] != 0: k = {"i": i, "j": j}
                else:
                    k = {"i": i, "j": j}
        for i in range(0, 4):
            for j in range(0, 4):
                if self.data[j][i]["Number"] != 0:
                    if j != 0:
                        for k in range(0, j):
                            if self.data[k][i]["Number"] == 0:
                                swap = self.data[k][i]
                                self.data[k][i] = self.data[j][i]
                                self.data[j][i] = swap
                                self.dead = False
                                break

    def down_run(self):
        for i in range(0, 4):
            k = None
            for j in range(3, -1, -1):
                l = self.data[j][i]
                if k and l["Number"] != 0:
                    k_v = self.data[k["j"]][k["i"]]
                    if k_v["Number"] == l["Number"]:
                        self.data[k["j"]][k["i"]]["Number"] = k_v["Number"] + l["Number"]
                        self.data[j][i] = {"Item": None, "Number": 0}
                        k = None
                        self.dead = False
                    else:
                        k = {"i": i, "j": j}
                else:
                    if l["Number"] != 0: k = {"i": i, "j": j}

        for i in range(0, 4):
            for j in range(0, 4):
                if self.data[3 - j][i]["Number"] != 0:
                    if 3 - j != 3:
                        for k in range(3, 3 - j - 1, -1):
                            if self.data[k][i]["Number"] == 0:
                                swap = self.data[k][i]
                                self.data[k][i] = self.data[3 - j][i]
                                self.data[3 - j][i] = swap
                                self.dead = False
                                break

    def left_run(self):
        for i in range(0, 4):
            k = None
            for j in range(0, 4):
                l = self.data[i][j]
                if k and l["Number"] != 0:
                    k_v = self.data[k["i"]][k["j"]]
                    if k_v["Number"] == l["Number"]:
                        self.data[k["i"]][k["j"]]["Number"] = k_v["Number"] + l["Number"]
                        self.data[i][j] = {"Item": None, "Number": 0}
                        k = None
                        self.dead = False
                    else:
                        k = {"i": i, "j": j}
                else:
                    if l["Number"] != 0: k = {"i": i, "j": j}
        for i in range(0, 4):
            for j in range(0, 4):
                if self.data[i][j]["Number"] != 0:
                    if j != 0:
                        for k in range(0, j):
                            if self.data[i][k]["Number"] == 0:
                                swap = self.data[i][k]
                                self.data[i][k] = self.data[i][j]
                                self.data[i][j] = swap
                                self.dead = False
                                break

    def right_run(self):
        for i in range(0, 4):
            k = None
            for j in range(3, -1, -1):
                l = self.data[i][j]
                if k and l["Number"] != 0:
                    k_v = self.data[k["i"]][k["j"]]
                    if k_v["Number"] == l["Number"]:
                        self.data[k["i"]][k["j"]]["Number"] = k_v["Number"] + l["Number"]
                        self.data[i][j] = {"Item": None, "Number": 0}
                        k = None
                        self.dead = False
                    else:
                        k = {"i": i, "j": j}
                else:
                    if l["Number"] != 0: k = {"i": i, "j": j}
        for i in range(0, 4):
            for j in range(0, 4):
                if self.data[i][3 - j]["Number"] != 0:
                    if 3 - j != 3:
                        for k in range(3, 3 - j - 1, -1):
                            if self.data[i][k]["Number"] == 0:
                                swap = self.data[i][k]
                                self.data[i][k] = self.data[i][3 - j]
                                self.data[i][3 - j] = swap
                                self.dead = False
                                break

    def get_dead_status(self):
        return self.dead


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # replay = ReplayWindow('地主')
    doudizhu = Game2048Main()
    app.exec_()
