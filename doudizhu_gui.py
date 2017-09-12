from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from random import randint
from doudizhu import poker_distribute, pattern_spot, cards_validate, strategy, compare, ai_jiaofen, rearrange, print_cards
import json, socket, threading, struct, sys, os, doudizhu, logging

logger_name = 'doudizhu_log'
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)
# logging.basicConfig(filename='log', level=logging.DEBUG)


class DouDiZhu(QMainWindow):
    def __init__(self, n, sockets=(0, 0, 0), host='jarrod'):
        super().__init__()
        self.cards = [[], [], [], []]
        self.out_cards = [[], [], []]
        self.scores = [0, 0, 0]
        self.dizhu = 0
        self.player_now = self.dizhu
        self.tips_cards = []
        self.finished = False
        self.pass_me = [1, 1, 1]
        self.can_pass = False
        self.person = [1, 0, 0]
        self.names = [host, '', '']
        self.time_count = 5000
        self.fake_ai_think_time = 200000000
        self.winner = '地主'
        self.user_acted = 0  # 0 等待叫分， 1 已经叫分，  2 等待出牌， 3 已出牌
        self.replay = False
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

        playAction = QAction('Play', self)
        playAction.triggered.connect(self.initiate_game)
        menubar.addAction(playAction)

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.add_time)

        self.widget = QWidget()
        self.avatars = []
        self.lbl_names = []
        for i in range(3):
            self.lbl_names.append(QLabel(self.names[i]))
            lbl_tmp = QLabel()
            lbl_tmp.setPixmap(self.scaled_pixmap(os.path.join('pics', 'doudizhu.png')))
            self.avatars.append(lbl_tmp)
        self.lbl_top = QLabel('This is for messages!')
        self.lcd_time = QLCDNumber()
        self.lcd_time.setDigitCount(7)
        self.lcd_time.setSegmentStyle(QLCDNumber.Flat)
        self.cards_area_one = PukeOne(self.cards[0], False, 1, self)
        self.cards_area_two = PukeTwo(self.cards[1], False, 2, self)
        self.cards_area_three = PukeTwo(self.cards[2], False, 3, self)
        self.out_cards_area_one = PukeOne([], True, 1, self)
        self.out_cards_area_two = PukeTwo([], True, 2, self)
        self.out_cards_area_three = PukeTwo([], True, 3, self)
        self.card_area_dipai = PukeOne(self.cards[3], True, 4, self)
        self.cards_areas = [self.cards_area_one, self.cards_area_two, self.cards_area_three, self.card_area_dipai]
        self.out_cards_areas = [self.out_cards_area_one, self.out_cards_area_two, self.out_cards_area_three]
        send_button = QPushButton('send')
        send_button.clicked.connect(self.send_cards)
        tips_button = QPushButton('tips')
        tips_button.clicked.connect(self.tips)
        skip_button = QPushButton('skip')
        skip_button.clicked.connect(self.skip)
        grid = QGridLayout()
        # 顶部放置玩家2、3的名称头像，提示条，横向、纵向均划为15份
        grid.addWidget(self.lbl_names[2], 0, 0, 1, 2)
        grid.addWidget(self.avatars[2], 1, 0, 2, 1)
        grid.addWidget(self.lbl_top, 0, 2, 1, 10)
        grid.addWidget(self.lcd_time, 0, 12, 1, 1)
        grid.addWidget(self.lbl_names[1], 0, 14, 1, 1)
        grid.addWidget(self.avatars[1], 1, 14, 2, 1)

        # 中间从左往右依次是玩家2的牌展示区，出牌区，底牌区，玩家3出牌区，玩家3牌展示区，中间下方为玩家1出牌区
        grid.addWidget(self.cards_area_three, 3, 0, 9, 2)
        grid.addWidget(self.out_cards_area_three, 3, 2, 6, 4)
        grid.addWidget(self.card_area_dipai, 3, 6, 6, 3)
        grid.addWidget(self.out_cards_area_two, 3, 9, 6, 4)
        grid.addWidget(self.out_cards_area_one, 9, 2, 3, 11)
        grid.addWidget(self.cards_area_two, 3, 13, 9, 2)

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

    def set_avatar(self):
        for i in range(3):
            if i == 1:
                direction = 'left'
            else:
                direction = 'right'
            dizhu_avatar = self.scaled_pixmap(os.path.join('pics', os.path.join('pukeimage', 'dizhu-' + direction + '.jpg')))
            nongmin_avatar = self.scaled_pixmap(os.path.join('pics', os.path.join('pukeimage', 'nongmin-' + direction + '.jpg')))
            if i == self.dizhu:
                self.avatars[i].setPixmap(dizhu_avatar)
            else:
                self.avatars[i].setPixmap(nongmin_avatar)

    def initiate_game(self):
        ai_names = ['Harry', 'Ron', 'Hermione', 'Albus', 'Severus', 'Minerva', 'Hagrid', 'Lupin', 'Moody', 'Horace',
                    'Filius', 'Dom', 'Brian', 'Mia', 'Letty']
        self.scores = [0, 0, 0]
        self.finished = False
        self.pass_me = [1, 1, 1]
        self.can_pass = False
        self.time_count = 5000
        self.fake_ai_think_time = 100000000
        self.user_acted = 0  # 0 等待叫分， 1 已经叫分，  2 等待出牌， 3 已出牌
        self.cards_areas[3].can_display_dipai = False
        for i in range(3):
            if i > 0:
                self.cards_areas[i].diplay_num = False
            self.update_cards_area(self.out_cards_areas[i], [])
            self.avatars[i].setPixmap(self.scaled_pixmap(os.path.join('pics', 'doudizhu.png')))
        if not self.replay:
            for i in range(1,3):
                t = randint(0, len(ai_names)-1)
                self.names[i] = ai_names[t]
                self.lbl_names[i].setText(ai_names[t])
                ai_names.remove(ai_names[t])
        self.cards = poker_distribute()
        logger.info("all player cards:" + str(self.cards))
        for i in range(4):
            self.update_cards_area(self.cards_areas[i], self.cards[i])
        self.lbl_top.setText('开始叫分(1-3分)')
        self.jiaofen()

    def jiaofen(self):
        self.timer.start(1)
        self.jiaofen_window = JiaoFenWindow(parent=self)
        self.jiaofen_window.exec_()
        self.scores[0] = self.jiaofen_window.get_score()
        logger.info("1号玩家叫分: " + str(self.scores[0]))
        self.user_acted = 1
        self.reset_timer()
        self.jiaofen_window.destroy()
        self.after_jiaofen()

    def add_time(self):
        self.lcd_time.display(int(self.time_count/1000))
        self.time_count -= 1
        self.fake_ai_think_time -= 1
        if self.time_count < 0:
            self.timer.stop()
            self.reset_timer()
            if self.user_acted == 2:
                self.lbl_top.setText('时间到，将自动出牌！')
                self.ai_already_acted()
                self.user_already_acted()
        if self.fake_ai_think_time < 0:
            self.ai_already_acted()
            self.reset_timer()
            self.play_cycle()

    def after_jiaofen(self):
        for i in range(1, 3):
            self.scores[i] = ai_jiaofen(self.cards[i])
        logger.info('all jiaofen: ' + str(self.scores))
        self.dizhu = self.scores.index(max(self.scores))
        self.set_avatar()
        self.player_now = self.dizhu
        logger.info('dizhu: ' + str(self.player_now+1))
        self.lbl_top.setText('地主是' + str(self.player_now+1) + '号玩家：' + self.names[self.player_now])
        self.cards[self.player_now] += self.cards[3]
        self.cards[self.player_now].sort()
        self.update_cards_area(self.cards_areas[self.player_now], self.cards[self.player_now])
        self.cards_areas[3].can_display_dipai = True
        self.cards_areas[3].update()
        self.play_cycle()

    def play_cycle(self):
        while not self.finished:
            if self.cards[self.player_now] == []:
                self.lbl_top.setText('游戏结束，赢家是' + self.names[self.player_now])
            # 如果上家和上上家都没有出牌，则将对比的last_result初始化
            if self.pass_me[(self.player_now - 1) % 3] and self.pass_me[(self.player_now - 2) % 3]:
                self.last_result = {'validate': True, 'nums': [0], 'result': 'null'}
                self.can_pass = False
                self.pass_me[self.player_now] = 0
            else:
                self.can_pass = True

            if self.person[self.player_now]:
                self.fake_ai_think_time = 10000000
                self.user_acted = 2
            else:
                out_nums = strategy(self.cards[self.player_now], self.last_result)
                if out_nums:
                    self.fake_ai_think_time = randint(100, 2000)
                else:
                    self.fake_ai_think_time = 200
            self.reset_timer()
            self.timer.start(1)
            self.update_cards_area(self.out_cards_areas[self.player_now], [])
            break

    def reset_timer(self):
        if self.timer.isActive():
            self.timer.stop()
        self.lcd_time.display(0)
        self.time_count = 20000

    def ai_already_acted(self, real_ai=True):
        self.pass_me[self.player_now] = 0
        out_nums = strategy(self.cards[self.player_now], self.last_result)
        logger.info('上家出牌是：' + str(self.last_result) + '\n' + str(self.player_now+1) + '号玩家的牌是：' + str(
            self.cards[self.player_now]) + '\n电脑算出的' + str(self.player_now+1) + '号玩家出牌号码是： ' + str(out_nums))
        if not out_nums:
            self.pass_me[self.player_now] = 1
            logger.info(str(self.player_now+1) + '号玩家没有牌可以大的了，过！')
        if real_ai:
                # 如果上家是地主，对家出牌的时候不压
            if (self.player_now - 1) % 3 == self.dizhu and self.pass_me[self.dizhu] and not self.pass_me[(self.player_now - 2) % 3] and not self.person[self.player_now]:
                out_nums = []
                self.pass_me[self.player_now] = 1
                logger.info(str(self.player_now+1) + '号玩家，电脑算出上家是地主，对家出牌的时候不压')
            # 如果上家是对家，且出了大牌，那么不压
            if self.player_now != self.dizhu and (self.player_now - 1) % 3 != self.dizhu and self.last_result['nums'][0] in [13, 14] and not self.pass_me[
                        (self.player_now - 1) % 3] and not self.person[self.player_now]:
                out_nums = []
                self.pass_me[self.player_now] = 1
                logger.info(str(self.player_now+1) + '号玩家，电脑算出上家是对家，且出了大牌，那么不压')

        out_cards = rearrange(self.cards[self.player_now], out_nums)
        logger.info('电脑算出的' + str(self.player_now+1) + '号玩家出牌是： ' + str(out_cards))

        if self.pass_me[self.player_now] == 0:
            logger.info(str(self.player_now+1) + '号玩家出牌： ' + str(out_cards))
        else:
            logger.info(str(self.player_now+1) + '号玩家过！')

        if real_ai:
            self.play_out_cards(out_cards)
        return out_cards

    def finished_or_not(self):
        if len(self.cards[self.player_now]) == 0:
            if self.player_now == self.dizhu:
                self.winner = '地主'
                self.lbl_top.setText('游戏结束，地主胜！')
            else:
                self.winner = '农民'
                self.lbl_top.setText('游戏结束，农民胜！')
            # 将玩家2和3的牌展示出来
            for i in range(1, 3):
                self.cards_areas[i].diplay_num = True
                self.cards_areas[i].update()
            replay_window = ReplayWindow(self.winner)
            replay_window.exec_()
            self.replay = replay_window.get_replay()
            replay_window.destroy()
            if self.replay:
                self.initiate_game()
            else:
                self.close()
            return True
        else:
            return False

    # 把牌打出去的动作
    def play_out_cards(self, outcards):
        self.reset_timer()
        if outcards and 161 not in outcards:
            for card in outcards:
                self.cards[self.player_now].remove(card)
            if self.player_now == 0:
                self.cards_areas[self.player_now].chosen_cards = []
            self.last_result = cards_validate(outcards)
            self.update_cards_area(self.cards_areas[self.player_now], self.cards[self.player_now])
            self.update_cards_area(self.out_cards_areas[self.player_now], outcards)
        else:
            self.lbl_top.setText(str(self.player_now + 1) + '号玩家过！')
            self.update_cards_area(self.out_cards_areas[self.player_now], [161])
        self.finished = self.finished_or_not()
        if self.finished:
            return
        self.player_now = (self.player_now + 1) % 3

    def show_records(self):
        pass

    def creat_room(self):
        pass

    def join_room(self):
        pass

    # 更新相应区域的牌
    def update_cards_area(self, cards_area, cards):
        cards_area.cards = cards
        cards_area.update()

    # 发送按钮
    def send_cards(self):
        if not self.cards[0]:
            return
        out_cards = self.cards_areas[0].chosen_cards
        out_cards.sort()
        logger.info('上家出牌是：' + str(self.last_result) + "1号玩家选择的牌是：" + str(out_cards))
        out_result = cards_validate(out_cards)
        logger.info('系统校验牌是否符合规则，结果是：' + str(out_result))
        bigger = compare(self.last_result, out_result)
        logger.info('系统校验是否比上家大：' + str(bigger))
        if bigger and out_result['validate']:
            self.pass_me[self.player_now] = 0
            self.play_out_cards(out_cards)
            if not self.finished:
                self.user_already_acted()
        else:
            self.lbl_top.setText('出牌不合法，请检查！')

    # 跳过按钮
    def skip(self):
        if not self.cards[0] or self.finished:
            return
        if not self.can_pass:
            self.lbl_top.setText('您不能跳过出牌！')
        else:
            self.pass_me[self.player_now] = 1
            logger.info("1号玩家过")
            self.play_out_cards([])
            self.user_already_acted()
            self.cards_areas[0].chosen_cards = []
            self.cards_areas[0].update()


    def tips(self):
        outcards = self.ai_already_acted(real_ai=False)
        self.cards_areas[0].chosen_cards = outcards
        self.cards_areas[0].update()
        if not outcards:
            self.lbl_top.setText('没有牌能大过对方，自动跳过！')
            self.skip()

    def user_already_acted(self):
        self.reset_timer()
        self.user_acted = 3
        self.play_cycle()


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
        self.can_display_dipai = False

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
            if self.player == 4 and not self.can_display_dipai:
                card_file = os.path.join('pics', os.path.join('pukeimage', 'back.jpg'))
            else:
                card_file = find_card_image(self.cards[i])
            pix_card = QPixmap(card_file)
            if self.display_only:   # 如果只是展示，牌的高度为模块的高度
                # 底牌展示区高度放小一点,player=4代表底牌
                if self.player == 4:
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
            # 判断重叠率是否能展示全，如果不能则增大重叠率，最大3/4
            stack_ratio = 1/3
            all_cards_width = ((1-stack_ratio) * len(self.cards) + stack_ratio) *card_width
            while all_cards_width > self.width():
                stack_ratio += 0.01
                all_cards_width = ((1 - stack_ratio) * len(self.cards) + stack_ratio) * card_width
                if stack_ratio > 3/4:
                    # 此处写如果重叠率到了3/4还不行的情况，应该折行，懒得写了
                    break
            cur_x = int((self.width() - all_cards_width) / 2 + i * card_width * (1-stack_ratio))

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
            if self.player == 3:
                tranform.rotate(90)
            else:
                tranform.rotate(270)
            pix_card = QPixmap(card_file)
            pix_card = pix_card.transformed(tranform)
            if self.diplay_num:
                card_height = int(pix_card.height() * (self.width() / 3) / pix_card.width())
                card_width = int(self.width() / 3)
                # 如果是玩家3，应该靠左展示
                if self.player == 3:
                    cur_x = 0
                elif self.player == 2:
                    cur_x = int(self.width() * 2 / 3)
            else:
                card_height = int(pix_card.height() * (self.width()/2) / pix_card.width())
                card_width = int(self.width()/2)
                if self.player == 3:
                    cur_x = 0
                elif self.player == 2:
                    cur_x = int(self.width() / 2)
            # 两张牌之间重叠1/3，因此中间点牌占的总宽度就是2/3*h*n+1/3*h
            stack_ratio = 1 / 3
            all_cards_height = ((1 - stack_ratio) * len(self.cards) + stack_ratio) * card_height
            while all_cards_height > self.height():
                stack_ratio += 0.01
                all_cards_height = ((1 - stack_ratio) * len(self.cards) + stack_ratio) * card_height
                if stack_ratio > 3 / 4:
                    # 此处写如果重叠率到了3/4还不行的情况，应该折行，懒得写了
                    break
            cur_y = int((self.height() - all_cards_height) / 2 + i * card_height*(1-stack_ratio))
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
        self.timer = QTimer()
        self.timer.singleShot(5000, self.close)

    def button_clicked(self):
        sender = self.sender()
        text = sender.text()
        self.score = int(text[:1])
        self.close()

    def get_score(self):
        return self.score


class ReplayWindow(QDialog):
    def __init__(self, winner, parent=None):
        super().__init__()
        self.winner = winner
        self.replay = 0

        self.InitUI()

    def InitUI(self):
        hbox = QHBoxLayout()
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.button_clicked)
        replay_button = QPushButton('Replay')
        replay_button.clicked.connect(self.button_clicked)
        hbox.addWidget(cancel_button)
        hbox.addWidget(replay_button)
        vbox = QVBoxLayout()
        lbl_winner = QLabel(self.winner + '胜！')
        vbox.addWidget(lbl_winner)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.setWindowTitle('再玩一局？')
        self.show()

    def button_clicked(self):
        sender = self.sender()
        text = sender.text()
        if text == 'Replay':
            self.replay = True
        else:
            self.replay = False
        self.close()

    def get_replay(self):
        return self.replay


def find_card_image(num):
    n =int(num / 10)
    color = num % 10
    puke_path = os.path.join('pics', 'pukeimage')
    if n == 16:
        pass_pics_dir = os.path.join(puke_path, 'pass')
        pass_pics = os.listdir(pass_pics_dir)
        for pic in pass_pics:
            suffix = os.path.splitext(pic)
            if suffix not in ['jpg', 'png', 'jpeg']:
                pass_pics.remove(pic)
        pic_path = os.path.join(pass_pics_dir, pass_pics[randint(0, len(pass_pics)-1)])
        return pic_path
    elif n >= 14:
        return os.path.join(puke_path, str(num) + '.jpg')
    elif n >= 12:
        return os.path.join(puke_path, os.path.join(str(color), str(n-11)+'.jpg'))
    else:
        return os.path.join(puke_path, os.path.join(str(color), str(n+2) + '.jpg'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # replay = ReplayWindow('地主')
    doudizhu = DouDiZhu(1)
    app.exec_()