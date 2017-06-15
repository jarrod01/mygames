from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys

class DouDiZhu(QMainWindow):
    def __init__(self, name_one='Guest', name_two='Harry', name_three='Ron'):
        super().__init__()
        self.name_one = name_one
        self.name_two = name_two
        self.name_three = name_three
        self.initUI()

    def initUI(self):
        screen = QDesktopWidget().screenGeometry()
        self.w = screen.width()
        self.h = screen.height()
        # player 1, on the bottom
        self.widget_player1 = PlayerBottom(self.name_one, [11, 12, 13, 14, 21, 22], self)
        self.widget_player1.setGeometry(0, int(self.h*2/3), self.w, int(self.h/3))
        self.setGeometry(0, 0, self.w, self.h)
        self.setWindowTitle('Doudizhu --' + self.name_one)
        self.show()


class PlayerBottom(QWidget):
    def __init__(self, name, cards, parent_widget):
        super(PlayerBottom, self).__init__(parent_widget)
        self.name = name
        self.cards = cards
        self.parent_widget = parent_widget
        self.chosen_cards = []
        self.cards_num = len(self.cards)
        self.initUI()

    def initUI(self):
        self.w = self.frameGeometry().width()
        self.h = self.frameGeometry().height()
        self.w = 1360
        self.h = 253
        pixmap_avatar = QPixmap('pics/doudizhu.png')
        lbl_avatar = QLabel(self)
        lbl_avatar.setPixmap(pixmap_avatar)
        lbl_avatar.setGeometry(int(0.0125*self.w), int(0.1*self.h), int(0.1*self.w), int(0.6*self.h))
        lbl_name_one = QLabel(self.name, self)
        lbl_name_one.setGeometry(int(0.0125*self.w), int(0.8*self.h), int(0.1*self.w), int(0.1*self.h))
        btn_send = QPushButton('Send', self)
        btn_send.move(int(0.9*self.w), int(self.h/3))
        btn_send.clicked.connect(self.send_cards)
        self.display_cards(self.cards)

    def display_cards(self, cards):
        n = self.cards_num
        # 两张牌的间隔宽度，计算公式（n-1）*xw + 0.7*0.8h = 0.75w
        self.xw = int((0.75*self.w - 0.7*0.8*self.h) / (n-1))
        self.btn_cards = []
        for i in range(n):
            card_file = 'pics/pukeimage/' + str(cards[i]%10) + '/' + str(int(cards[i]/10))
            pix_card = QPixmap(card_file)
            self.btn_cards.append(PicButton(i, pix_card, self))
            self.btn_cards[i].setGeometry(int(0.125*self.w) + i*self.xw, int(0.2*self.h), int(self.h*0.8*0.7), int(0.8*self.h))

    def change_position(self, order):
        if self.cards[order] in self.chosen_cards:
            self.chosen_cards.remove(self.cards[order])
            self.btn_cards[order].setGeometry(int(0.125 * self.w) + order * self.xw, int(0.2*self.h), int(self.h * 0.8 * 0.7),
                                              int(0.8 * self.h))
        else:
            self.chosen_cards.append(self.cards[order])
            self.btn_cards[order].setGeometry(int(0.125*self.w) + order*self.xw, 0, int(self.h*0.8*0.7), int(0.8*self.h))

    def send_cards(self):
        self.chosen_cards.sort()
        self.cards_num -= len(self.chosen_cards)
        for card in self.chosen_cards:
            self.btn_cards[self.cards.index(card)].setGeometry(0,0,0,0)
        self.xw = int((0.75*self.w - 0.7*0.8*self.h) / (self.cards_num-1))
        for i in range(self.cards_num):
            order = 0
        for card in self.chosen_cards:
            self.cards.remove(card)
        self.chosen_cards = []
        #self.display_cards(self.cards)


class PicButton(QAbstractButton):
    def __init__(self, order, pixmap, parent_widget):
        super(PicButton, self).__init__(parent_widget)
        self.pixmap = pixmap
        self.parent_widget = parent_widget
        self.order = order
        self.clicked.connect(self.change_position)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()

    def change_position(self):
        self.parent_widget.change_position(self.order)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    doudizhu = DouDiZhu()
    app.exec_()