from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import random
import sys
import sqlite3

# 借用了yangankang（https://github.com/yangankang/examples/tree/master/2048）的代码，按需求改动了一下

class Game2048Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.InitUI()

    def InitUI(self):
        self.game = Game2048(self)
        self.setCentralWidget(self.game)

        menubar = self.menuBar()
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        recordsAction = QAction('&Replay', self)
        recordsAction.setShortcut('Ctrl+R')
        recordsAction.setStatusTip('Replay')
        recordsAction.triggered.connect(self.game.bottom.game_initializer)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        menubar.addAction(recordsAction)

        start_number_menu = QMenu('StartNumber', self)
        sn0 = QAction('original', self)
        sn0.triggered.connect(self.set_start_number)
        start_number_menu.addAction(sn0)
        for i in range(10, 14):
            sntmp = QAction(str(2**i), self)
            sntmp.triggered.connect(self.set_start_number)
            start_number_menu.addAction(sntmp)

        level_menu = QMenu('Level', self)
        for i in range(1,7):
            level_tmp = QAction(str(i), self)
            level_tmp.triggered.connect(self.set_level)
            level_menu.addAction(level_tmp)

        settingMenu = menubar.addMenu('&Settings')
        settingMenu.addMenu(start_number_menu)
        settingMenu.addMenu(level_menu)
        menubar.setNativeMenuBar(False)

        self.center()
        self.setFixedSize(540, 600)

        # 获取一下第一级的记录
        records = read_db()
        if records and 0 in records.keys():
            record = records[0]
        else:
            record = 0
        self.game.set_record(record)

        self.show()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width()-size.width())/2),
            int((screen.height()-size.height())/2))

    def set_level(self):
        sender = self.sender()
        level = int(sender.text()) - 1
        self.game.bottom.level = level
        self.game.bottom.game_initializer()
        self.game.level_lbl.setText('当前级别：%s级'%str(level+1))

        # 获取这一级别的record
        records = read_db()
        if records and level in records.keys():
            record = records[level]
        else:
            record = 0
        self.game.set_record(record)


    def set_start_number(self):
        sender = self.sender()
        start_number = int(sender.text())
        self.game.bottom.start_number = start_number
        self.game.bottom.game_initializer()


class Game2048(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.parent = parent

    def initUI(self):
        self.level_lbl = QLabel('当前级别：1级', self)
        self.level_lbl.move(30, 5)
        self.level_lbl.setFixedSize(120, 50)

        self.topleft = QLabel('当前分数：0', self)
        # self.topleft.setFrameShape(QFrame.StyledPanel)
        self.topleft.move(210, 5)
        self.topleft.setFixedSize(120, 50)

        self.topright = QLabel('最高分数：20000', self)
        # self.topright.setFrameShape(QFrame.StyledPanel)
        self.topright.setFixedSize(120, 50)
        self.topright.move(390, 5)

        self.bottom = GameCanvas(self)
        self.bottom.setFixedSize(500, 500)
        self.bottom.move(20, 60)

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

    def set_score(self, score):
        self.topleft.setText('当前分数：' + str(score))

    def set_record(self, record):
        self.topright.setText('最高分数：' + str(record))



class GameCanvas(QLabel):
    # 只读的背景16个方格
    item_bgs = []
    # 背景16个方格的xy位置也是只读的
    item_bg_pos = []
    item_data = []
    score = 0

    parent_x = 20
    parent_y = 60
    split_width = 16
    rect_width = 105

    def __init__(self, parent):
        super(GameCanvas, self).__init__(parent)
        self.parent = parent

        # self.resize(500, 500)
        self.move(self.parent_x, self.parent_y)
        self.setStyleSheet("QLabel{background-color:#bbada0;color:#bbada0;border-radius:6}")
        self.setFocusPolicy(Qt.StrongFocus)

        self.level = 0
        self.start_number = 0

        # self.set_item_bg()
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
            # level 决定每次随机出现的数字的概率以及最大的数字是多少
            # level 0: 随机出现2和4，4的概率是20%
            # level 1：随机出现2、4、8，8的概率是5%
            # level 2：随机出现2、4、8、16，8和16的概率分别是5%
            # level 3: 随机出现2、4、8、16、32
            level = self.level
            tmp = random.randint(1, 100)
            if tmp <= 100-level*5:
                k = random.randint(0, 9)
                number = 2
                if k <= 1:
                    number = 4
            else:
                number = 2 ** (int((100-tmp)/5) + 3)

            rnd = random.randint(0, len(zero_ds)-1)
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
        # 所有初始化为0
        self.score = 0
        self.parent.set_score(self.score)

        # 所有item重置，画面重置
        items = []
        if self.item_data:
            for i in range(0, 4):
                for j in range(0, 4):
                    item = self.item_data[i][j]["Item"]
                    if item:
                        items.append(item)
            self.item_data = []
        self.set_item_bg()
        self.redraw_rect(items)

        # 选择初始化数字
        start_number = self.start_number
        indexes = []
        for i in range(4):
            for j in range(4):
                indexes.append({'i': i, 'j': j})
        d = random.sample(indexes, 1)[0]
        # 根据初始数字和级别随机生成2个数字
        if start_number:
            d['num'] = start_number
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
        self.score += calculate.get_score()
        self.parent.set_score(self.score)

        self.redraw_rect(items)
        # self.check_is_win()
        dead = self.check_is_dead()
        if dead:
            # 更新记录
            # 获取这一级别的record
            records = read_db()
            if records:
                if self.level in records.keys():
                    if self.score > records[self.level]:
                        write_db(self.level, self.score, update_type='update')
                        self.parent.set_record(self.score)
                    else:
                        pass
                else:
                    write_db(self.level, self.score)
                    self.parent.set_record(self.score)
            else:
                write_db(self.level, self.score)
                self.parent.set_record(self.score)

            reply = QMessageBox.question(self.parent, '提示信息',
                                         "您已经输了，是否重新开始?", QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.game_initializer()
                # print("OK")
            else:
                print("NO")
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
        #先拷贝一遍item里面的数字，
        tmp_numbers = []
        for i in range(4):
            tmp_line = []
            for j in range(4):
                tmp_line.append(self.item_data[i][j]["Number"])
            if 0 in tmp_line:
                return False
            else:
                tmp_numbers.append(tmp_line)

        for i in range(4):
            for j in range(3):
                if tmp_numbers[i][j] == tmp_numbers[i][j+1]:
                    return False
                if tmp_numbers[j][i] == tmp_numbers[j+1][i]:
                    return False
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
        self.score = 0

    def calculate(self, direction):
        self.score = 0
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
                        self.score += 2 * l["Number"]
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
                        self.score += 2*l["Number"]
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
                        self.score += 2 * l["Number"]
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
                        self.score += 2 * l["Number"]
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
                                break

    def get_score(self):
        return self.score

def read_db(name='jarrod'):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('select * from game_2048 where name=?', (name, ))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if not result:
        return {}
    records = {}
    for record in result:
        level = record[2]
        score = record[3]
        records[level] = score
    return records

def write_db(level, score, name='jarrod', update_type='insert'):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    if update_type == 'insert':
        cursor.execute('insert into game_2048 (name, level, score) VALUES ("%s", %d, %d)'%(name, level, score))
    else:
        cursor.execute('update game_2048 set score=? where (name=? and level=?)', (score, name, level, ))
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # replay = ReplayWindow('地主')
    doudizhu = Game2048Main()
    app.exec_()
