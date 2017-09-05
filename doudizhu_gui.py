from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys, os, doudizhu

class DouDiZhu(QMainWindow):
    def __init__(self, n, sockets=(0, 0, 0), host='jarrod'):
        super().__init__()
        self.cards = [[], [], [], []]
        self.out_cards = [[], [], []]
        self.patterns = []
        self.scores = [0, 0, 0]
        self.tips_cards = []
        self.names = [host, '', '']
        self.InitUI()


    def InitUI(self):
        screen = QDesktopWidget().screenGeometry()
        self.statusBar().showMessage('Ready to play!')

        menubar = self.menuBar()

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        recordsAction = QAction('&Records', self)
        recordsAction.setShortcut('Ctrl+R')
        recordsAction.setStatusTip('Show your records')
        recordsAction.triggered.connect(self.jiaofen)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(recordsAction)
        fileMenu.addAction(exitAction)

        hostAction = QAction('Create Room', self)
        hostAction.setStatusTip('Create a room and tell other players the room number!')
        hostAction.triggered.connect(self.creat_room)

        joinAction = QAction('Join Room', self)
        joinAction.setStatusTip('Got a room number and join a game!')
        joinAction.triggered.connect(self.join_room)

        multiplayerMenu = menubar.addMenu('&Multiplayer')
        multiplayerMenu.addAction(hostAction)
        multiplayerMenu.addAction(joinAction)
        # 用来创建窗口内的菜单栏
        menubar.setNativeMenuBar(False)


        self.widget = QWidget()
        self.avatars = []
        self.lbl_names = []
        for i in range(3):
            self.lbl_names.append(QLabel(self.names[i]))
            lbl_tmp = QLabel()
            lbl_tmp.setPixmap(self.scaled_pixmap('pics/doudizhu.png'))
            self.avatars.append(lbl_tmp)
        self.lbl_top = QLabel('This is for messages!')
        self.cards_area_one = PukeOne(self.cards[0], False, 1, self)
        self.cards_area_two = PukeTwo(self.cards[1], False, 2, self)
        self.cards_area_three = PukeTwo(self.cards[2], False, 3, self)
        self.out_cards_area_one = PukeOne([], True, 1, self)
        self.out_cards_area_two = PukeTwo([], True, 2, self)
        self.out_cards_area_three = PukeTwo([], True, 3, self)
        self.card_area_dipai = PukeOne(self.cards[3], True, 0, self)
        self.cards_areas = [self.cards_area_one, self.cards_area_two, self.cards_area_three, self.card_area_dipai]
        self.out_cards_areas = [self.out_cards_area_one, self.out_cards_area_two, self.out_cards_area_three]
        send_button = QPushButton('send')
        tips_button = QPushButton('tips')
        skip_button = QPushButton('skip')
        grid = QGridLayout()
        # 顶部放置玩家2、3的名称头像，提示条，横向、纵向均划为15份
        grid.addWidget(self.lbl_names[1], 0, 0, 1, 2)
        grid.addWidget(self.avatars[1], 1, 0, 2, 1)
        grid.addWidget(self.lbl_top, 0, 2, 3, 11)
        grid.addWidget(self.lbl_names[2], 0, 14, 1, 1)
        grid.addWidget(self.avatars[2], 1, 14, 2, 1)

        # 中间从左往右依次是玩家2的牌展示区，出牌区，底牌区，玩家3出牌区，玩家3牌展示区，中间下方为玩家1出牌区
        grid.addWidget(self.cards_area_two, 3, 0, 9, 2)
        grid.addWidget(self.out_cards_area_two, 3, 2, 6, 4)
        grid.addWidget(self.card_area_dipai, 3, 6, 6, 3)
        grid.addWidget(self.out_cards_area_three, 3, 9, 6, 4)
        grid.addWidget(self.out_cards_area_one, 9, 2, 3, 11)
        grid.addWidget(self.cards_area_three, 3, 13, 9, 2)

        # 下方从左往右依次为玩家1的头像、名称、牌展示区，三个按钮：出牌、提示、跳过
        grid.addWidget(self.avatars[0], 12, 0, 2, 2)
        grid.addWidget(self.lbl_names[0], 14, 0, 1, 2)
        grid.addWidget(self.cards_area_one, 12, 2, 3, 11)
        grid.addWidget(send_button, 12, 14, 1, 1)
        grid.addWidget(tips_button, 13, 14, 1, 1)
        grid.addWidget(skip_button, 14, 14, 1, 1)
        self.widget.setLayout(grid)

        self.setCentralWidget(self.widget)
        self.setGeometry(0, 0, screen.width(), screen.height())
        self.setWindowTitle('Doudizhu --' + self.names[0])
        self.setWindowIcon(QIcon(os.path.join('pics', 'doudizhu.png')))
        self.show()

    # 将头像缩小至对应区域的大小，同时保持比例
    def scaled_pixmap(self, pic):
        avatar = QPixmap(pic)
        height = 0
        width = 0
        max_width = 2 * self.width()/15
        max_height = 2 * self.height()/15
        avatar_width = avatar.width()
        avatar_heigth = avatar.height()
        if max_width/max_height > avatar_width/avatar_heigth:
            height = int(max_height)
            width = int(avatar_width * avatar_heigth/max_height)
        else:
            width = int(max_width)
            height = int(avatar_heigth * avatar_width/max_width)
        return avatar.scaled(width, height, aspectRatioMode=Qt.KeepAspectRatio)

    # 更换头像
    def set_avatar(self, pic_path, player):
        avatar = self.scaled_pixmap(pic_path)
        self.avatars[player].setPixmap(avatar)

    def set_player_name(self, name, player):
        self.lbl_names[player].setText(name)

    def show_records(self):
        pass

    def jiaofen(self):
        jiaofen = JiaoFenWindow(parent=self)
        jiaofen.exec_()
        score = jiaofen.get_score()
        jiaofen.destroy()
        self.lbl_top.setText(str(score))
        return score

    def creat_room(self):
        pass

    def join_room(self):
        pass

    # 更新相应区域的牌
    def update_cards_area(self, cards_area, cards):
        cards_area.cards = cards
        cards_area.update()

    # 将提示的牌弹起来
    def tips_action(self):
        self.cards_area_one.chosen_cards = self.tips_cards
        self.cards_area_one.update()

    def card_distribute(self, cards):
        for i in range(4):
            self.update_cards_area(self.cards_areas[i], cards[i])

# 底部横向的扑克排列，display_only代表不能点击，cards为牌的数字
class PukeOne(QFrame):
    def __init__(self, cards, display_only, player, parent):
        super().__init__(parent)
        self.cards = cards
        self.display_only = display_only
        self.player = player
        self.parent = parent
        self.chosen_cards = []
        self.card_infos = []

        self.InitUI()

    def InitUI(self):
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        # painter.begin(self)
        self.draw_cards(event, painter)
        # painter.end()

    def draw_cards(self, event, painter):
        self.card_infos = [] #每次画图前要把上次的info清空一遍
        for i in range(len(self.cards)):
            card_file = find_card_image(self.cards[i])
            pix_card = QPixmap(card_file)
            if self.display_only:   # 如果只是展示，牌的高度为模块的高度
                # 底牌展示区高度放小一点,player=0代表底牌
                if self.player == 0:
                    card_width = int(pix_card.width() * (self.height() / 3) / pix_card.height())
                    card_height = int(self.height()/3)
                else:
                    card_width = int(pix_card.width() * (self.height()) / pix_card.height())
                    card_height = int(self.height())
                cur_y = 0
            else:    # 因为需要点击，牌的高度为模块高度的2/3
                card_width = int(pix_card.width() * (self.height() * 2 / 3) / pix_card.height())
                card_height = int(self.height() * 2 / 3)
                cur_y = int(self.height() / 3)

            pix_card = pix_card.scaledToHeight(card_height)
            # 两张牌之间重叠1/3，因此中间点牌占的总宽度就是2/3*w*n+1/3*w
            cur_x = int((self.width() - (2 * len(self.cards) + 1) * card_width / 3) / 2 + i * card_width * 2 / 3)
            tmp_card_info = {'index': i, 'pix': pix_card, 'x': cur_x, 'y': cur_y}
            self.card_infos.append(tmp_card_info)
            if self.cards[i] in self.chosen_cards:
                painter.drawPixmap(self.card_infos[i]['x'], 0, self.card_infos[i]['pix'])
            else:
                painter.drawPixmap(cur_x, cur_y, pix_card)

    def update_cards(self, cards):
        self.cards = cards
        self.update()

    def mousePressEvent(self, event):
        if self.display_only:
            return
        cur_x = event.x()
        cur_y = event.y()
        tmp = -1
        if len(self.cards) == 0 or cur_x < self.card_infos[0]['x'] or cur_x > (self.card_infos[len(self.card_infos)-1]['x']+self.card_infos[len(self.card_infos)-1]['pix'].width()):
            return
        for i in range(len(self.card_infos)-1):
            if cur_x >= self.card_infos[i]['x'] and cur_x < self.card_infos[i+1]['x']:
                tmp = i
                break
        if tmp == -1:
            tmp = len(self.card_infos)-1
        if self.cards[tmp] not in self.chosen_cards:
            if cur_y < self.height()/3:
                return
            self.chosen_cards.append(self.cards[tmp])
        else:
            if cur_y > self.height()*2/3:
                return
            self.chosen_cards.remove(self.cards[tmp])
        self.update()

    def cards_sent(self):
        for card in self.chosen_cards:
            self.cards.remove(card)
        self.chosen_cards = []
        self.update()


class PukeTwo(QFrame):
    def __init__(self, cards, display_num, player, parent):
        super().__init__(parent)
        self.cards = cards
        self.diplay_num = display_num
        self.player = player
        self.parent = parent

        self.InitUI()

    def InitUI(self):
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        # painter.begin(self)
        self.draw_cards(event, painter)
        # painter.end()

    def draw_cards(self, event, painter):
        self.card_infos = []  # 每次画图前要把上次的info清空一遍
        for i in range(len(self.cards)):
            if self.diplay_num:
                card_file = find_card_image(self.cards[i])
            else:
                card_file = os.path.join('pics', os.path.join('pukeimage', 'back.jpg'))
            tranform = QTransform()
            tranform.rotate(90)
            pix_card = QPixmap(card_file)
            pix_card = pix_card.transformed(tranform)
            if self.diplay_num:
                card_height = int(pix_card.height() * (self.width() / 3) / pix_card.width())
                card_width = int(self.width() / 3)
                # 如果是玩家3，应该靠右展示
                if self.player == 2:
                    cur_x = 0
                elif self.player == 3:
                    cur_x = int(self.width() * 2 / 3)
            else:
                card_height = int(pix_card.height() * (self.width()/2) / pix_card.width())
                card_width = int(self.width()/2)
                if self.player == 2:
                    cur_x = 0
                elif self.player == 3:
                    cur_x = int(self.width() / 2)
            # 两张牌之间重叠1/3，因此中间点牌占的总宽度就是2/3*h*n+1/3*h
            cur_y = int((self.height() - (len(self.cards) + 2) * card_height / 3) / 2 + i * card_height / 3)
            pix_card = pix_card.scaledToHeight(card_height)
            tmp_card_info = {'index': i, 'pix': pix_card, 'x': cur_x, 'y': cur_y}
            self.card_infos.append(tmp_card_info)
            painter.drawPixmap(cur_x, cur_y, pix_card)


class JiaoFenWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.score = 0

        self.InitUI()

    def InitUI(self):
        hbox = QHBoxLayout()
        for i in range(3):
            button = QPushButton(str(i+1) + '分')
            button.clicked.connect(self.button_clicked)
            hbox.addWidget(button)
        self.setLayout(hbox)
        self.setWindowTitle('请叫分：')
        self.show()

    def button_clicked(self):
        sender = self.sender()
        text = sender.text()
        self.score = int(text[:1])
        self.close()

    def get_score(self):
        return self.score


def find_card_image(num):
    n =int(num / 10)
    color = num % 10
    puke_path = os.path.join('pics', 'pukeimage')
    if n >= 14:
        return os.path.join(puke_path, str(num) + '.jpg')
    elif n >= 12:
        return os.path.join(puke_path, os.path.join(str(color), str(n-11)+'.jpg'))
    else:
        return os.path.join(puke_path, os.path.join(str(color), str(n+2) + '.jpg'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    doudizhu = DouDiZhu(1)
    app.exec_()