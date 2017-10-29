from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from random import randint
from doudizhu import poker_distribute, pattern_spot, cards_validate, strategy, compare, ai_jiaofen, rearrange, print_cards
import json, socket, threading, struct, sys, os, doudizhu, logging, sqlite3

logger_name = 'doudizhu_log'
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('log')
fh.setLevel(logging.WARNING)
fh.setFormatter(formatter)
logger.addHandler(fh)
# logging.basicConfig(filename='log', level=logging.DEBUG)


class DouDiZhu(QMainWindow):
    def __init__(self, n=1, sockets=(0, 0, 0), host='jarrod'):
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
        self.gender = ['Man', 'Woman', 'Man']
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
        recordsAction.triggered.connect(self.show_records)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(recordsAction)
        fileMenu.addAction(exitAction)

        playAction = QAction('Play', self)
        playAction.triggered.connect(self.initiate_game)
        menubar.addAction(playAction)

        tuoguanAction = QAction('Tuoguan', self)
        tuoguanAction.triggered.connect(self.tuoguan)
        menubar.addAction(tuoguanAction)

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
        self.out_cards_area_two = PukeThree([], True, 2, self)
        self.out_cards_area_three = PukeThree([], True, 3, self)
        self.card_area_dipai = PukeOne(self.cards[3], True, 4, self)
        self.cards_areas = [self.cards_area_one, self.cards_area_two, self.cards_area_three, self.card_area_dipai]
        self.out_cards_areas = [self.out_cards_area_one, self.out_cards_area_two, self.out_cards_area_three]
        send_button = QPushButton('出牌')
        send_button.clicked.connect(self.send_cards)
        tips_button = QPushButton('提示')
        tips_button.clicked.connect(self.tips)
        skip_button = QPushButton('跳过')
        skip_button.clicked.connect(self.skip)
        grid = QGridLayout()
        # 顶部放置玩家2、3的名称头像，提示条，横向、纵向均划为15份
        grid.addWidget(self.lbl_names[2], 0, 0, 1, 1)
        grid.addWidget(self.avatars[2], 1, 0, 2, 1)
        grid.addWidget(self.lbl_top, 0, 1, 1, 4)
        grid.addWidget(self.lcd_time, 0, 11, 1, 1)
        grid.addWidget(self.lbl_names[1], 0, 12, 1, 1)
        grid.addWidget(self.avatars[1], 1, 12, 2, 1)

        # 中间从左往右依次是玩家2的牌展示区，出牌区，底牌区，玩家3出牌区，玩家3牌展示区，中间下方为玩家1出牌区
        grid.addWidget(self.cards_area_three, 3, 0, 9, 1)
        grid.addWidget(self.out_cards_area_three, 3, 1, 6, 5)
        grid.addWidget(self.card_area_dipai, 0, 5, 2, 3)
        grid.addWidget(self.out_cards_area_two, 3, 7, 6, 5)
        grid.addWidget(self.out_cards_area_one, 9, 1, 3, 11)
        grid.addWidget(self.cards_area_two, 3, 12, 9, 1)

        # 下方从左往右依次为玩家1的头像、名称、牌展示区，三个按钮：出牌、提示、跳过
        grid.addWidget(self.avatars[0], 13, 0, 2, 1)
        grid.addWidget(self.lbl_names[0], 15, 0, 1, 1)
        grid.addWidget(self.cards_area_one, 12, 1, 4, 11)
        grid.addWidget(send_button, 13, 12, 1, 1)
        grid.addWidget(tips_button, 14, 12, 1, 1)
        grid.addWidget(skip_button, 15, 12, 1, 1)
        self.widget.setLayout(grid)

        self.setCentralWidget(self.widget)
        self.setFixedSize(1000, 800)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint)
        self.setWindowTitle('Doudizhu --' + self.names[0])
        self.setWindowIcon(QIcon(os.path.join('pics', 'doudizhu.png')))
        self.show()
        self.play_music()

    def get_default_out_card_height(self):
        return self.out_cards_area_one.height()

    # 将头像缩小至对应区域的大小，同时保持比例
    def scaled_pixmap(self, pic):
        avatar = QPixmap(pic)
        height = 0
        width = 0
        max_width = 1 * self.width()/13
        max_height = 1 * self.height()/13
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
        if self.person[0] == 0:
            self.tuoguan()
        index = randint(1,2)
        self.change_music(index)
        ai_names = ['Harry', 'Ron', 'Hermione', 'Albus', 'Severus', 'Minerva', 'Hagrid', 'Lupin', 'Moody', 'Horace',
                    'Filius', 'Dom', 'Brian', 'Mia', 'Letty']
        self.scores = [0, 0, 0]
        self.finished = False
        self.pass_me = [1, 1, 1]
        self.can_pass = False
        self.time_count = 10000
        self.fake_ai_think_time = 100000000  #将这个时间设置一个很大的超过倒计时的值
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
        # 语音提示
        if self.time_count in [6000, 5000, 4000, 3000, 2000]:
            self.play_sound('Special_Remind.mp3')
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
                logger.info(str(self.player_now+1) + '不能跳过')
            else:
                self.can_pass = True

            if self.person[self.player_now]:
                self.fake_ai_think_time = 10000000
                self.user_acted = 2
            else:
                out_nums = strategy(self.cards[self.player_now], self.last_result)
                if out_nums:
                    self.fake_ai_think_time = randint(1000, 2000)
                else:
                    self.fake_ai_think_time = 1000
            self.reset_timer()
            self.timer.start(1)  # 之后就交给add_time函数去判断应该是等待用户出牌还是ai出牌
            self.update_cards_area(self.out_cards_areas[self.player_now], [])
            break

    def reset_timer(self):
        # 这段代码不知道为什么会引起重玩的时候第一把不能开始计时
        # if self.timer.isActive():
        #     self.timer.stop()
        self.lcd_time.display(0)
        self.time_count = 20000
        logger.info(str(self.player_now+1)+',时间重设为20秒')

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
                if self.dizhu == 0:
                    jifen = self.scores[0] * 2
                else:
                    jifen = -self.scores[0]
            else:
                if self.dizhu == 0:
                    jifen = -self.scores[0] * 2
                else:
                    jifen = self.scores[0]
                self.winner = '农民'
                self.lbl_top.setText('游戏结束，农民胜！')
            if jifen>0:
                sound_file = 'MusicEx_Win.mp3'
            else:
                sound_file = 'MusicEx_Lose.mp3'
            self.mediaplayer.stop()
            self.play_sound(sound_file)
            # 将玩家2和3的牌展示出来
            for i in range(1, 3):
                self.cards_areas[i].diplay_num = True
                self.cards_areas[i].update()
            if 'data.db' in os.listdir():
                write_db(self.names[0], jifen)
            replay_window = ReplayWindow(self.winner, self)
            replay_window.exec_()
            self.replay = replay_window.get_replay()
            replay_window.destroy()
            if self.replay:
                self.initiate_game()
            else:
                pass
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
        records_window = RecordsWindow(self.names[0], self)
        records_window.exec_()

    def creat_room(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s2用于获取IP地址
        s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s2.connect(('114.114.114.114', 80))
        addr, port = s2.getsockname()
        s2.close()
        num_ip = socket.ntohl(struct.unpack("I", socket.inet_aton(addr))[0])
        text = ('开房成功，您的房间号是：' + str(num_ip) + ', 快把房间号告诉玩伴吧')
        info_window = InfosWindow(text, parent=self)
        info_window.exec_()
        s.bind((addr, 9125))
        s.listen(2)
        self.lbl_top.setText('Waiting for connection...')

    def join_room(self):
        pass

    # 更新相应区域的牌
    def update_cards_area(self, cards_area, cards):
        cards_area.cards = cards
        cards_area.update()
        if cards_area in self.out_cards_areas and cards:
            file = self.decide_sounds(cards)
            if 'zha' in file:
                self.play_sound_2('Special_Bomb.mp3')
                self.change_music(3)
            elif 'feiji' in file:
                self.play_sound_2('Special_plane.mp3')
            self.play_sound(file)
        elif cards_area in self.cards_areas and len(cards)<3 and cards:
            file = self.gender[self.player_now] + '_baojing' + str(len(cards)) + '.mp3'
            self.play_sound_2(file)

    def decide_sounds(self, cards):
        gender = self.gender[self.player_now]
        if cards[0] == 161:
            i = randint(1, 3)
            file = gender + '_buyao' + str(i) + '.mp3'
        else:
            validate_result = cards_validate(cards)
            result = validate_result['result']
            num = validate_result['nums'][0]
            if not validate_result['validate']:
                file = 'Special_Escape.mp3'
            else:
                if num >= 14:
                    pass
                elif num >= 12:
                    num -= 11
                else:
                    num += 2
                related_files = {'ones': gender + '_' + str(num) + '.mp3',
                         'twos': gender + '_dui' + str(num) + '.mp3',
                         'two_jokers': gender + '_wangzha.mp3',
                         'threes': gender + '_tuple' + str(num) + '.mp3',
                         'fours': gender + '_zhadan.mp3',
                         'three_ones': gender + '_sandaiyi.mp3',
                         'three_twos': gender + '_sandaiyidui.mp3',
                         'straights': gender + '_shunzi.mp3',
                         'straights_double': gender + '_liandui.mp3',
                         'straights_triple': gender + '_feiji.mp3',
                         'four_two_ones': gender + '_sidaier.mp3',
                         'four_two_twos': gender + '_sidailiangdui.mp3',
                         'st_with_ones': gender + '_feiji.mp3',
                         'st_with_twos': gender + '_feiji.mp3',
                         'st3_with_ones': gender + '_feiji.mp3',
                         'st3_with_twos': gender + '_feiji.mp3',
                         }
                file = related_files[result]
                # 如果这时候能跳过而不跳过，那么就是比别人大了
                if self.can_pass and result not in ['ones', 'twos', 'threes'] and 'zha' not in file:
                    i = randint(1, 3)
                    file = gender + '_dani' + str(i) + '.mp3'
        return file


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

    def tuoguan(self):
        if self.person[0] == 1:
            self.lbl_names[0].setText(self.names[0] + '(托管中……)')
            self.person[0] = 0
            if self.player_now == 0 and self.user_acted == 2:
                self.ai_already_acted()
                self.reset_timer()
                self.play_cycle()
        else:
            self.lbl_names[0].setText(self.names[0])
            self.person[0] = 1

    def play_music(self):
        background_musics = ['Welcome', 'Normal', 'Normal2', 'Exciting']
        self.mediaplayer = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        for music in background_musics:
            url = os.path.join('sound', 'MusicEx_'+music+'.mp3')
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(url))))
        self.playlist.setCurrentIndex(0)
        self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        self.mediaplayer.setPlaylist(self.playlist)
        self.mediaplayer.play()

    def change_music(self, index):
        self.mediaplayer.pause()
        self.playlist.setCurrentIndex(index)
        self.mediaplayer.play()

    def play_sound(self, file):
        url = os.path.join('sound', file)
        self.tmp_player = QMediaPlayer()
        self.tmp_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(url))))
        self.tmp_player.play()

    def play_sound_2(self, file):
        url = os.path.join('sound', file)
        self.tmp_player_2 = QMediaPlayer()
        self.tmp_player_2.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(url))))
        self.tmp_player_2.play()


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
                    card_height = int(self.height()*2/3)
                    card_width = int(pix_card.width() * card_height / pix_card.height())
                else:
                    card_height = int(self.height())
                    card_width = int(pix_card.width() * card_height / pix_card.height())
                cur_y = 0
            else:    # 因为需要点击，牌的高度为模块高度的2/3
                card_height = int(self.height() * 2 / 3)
                card_width = int(pix_card.width() * card_height / pix_card.height())
                cur_y = int(self.height() / 3)

            pix_card = pix_card.scaledToHeight(card_height)
            # 两张牌之间重叠1/3，因此中间点牌占的总宽度就是2/3*w*n+1/3*w
            # 判断重叠率是否能展示全，如果不能则增大重叠率，最大5/6
            stack_ratio = 1/3
            all_cards_width = ((1-stack_ratio) * len(self.cards) + stack_ratio) *card_width
            while all_cards_width > self.width():
                stack_ratio += 0.01
                all_cards_width = ((1 - stack_ratio) * len(self.cards) + stack_ratio) * card_width
                if stack_ratio > 5/6:
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
            # 玩家2和玩家3的出牌区域也横向展示，已废弃
            if self.diplay_num:
                card_width = int(self.width() / 3)
                card_height = int(pix_card.height() * card_width / pix_card.width())
                # 如果是玩家3，应该靠左展示
                if self.player == 3:
                    cur_x = 0
                elif self.player == 2:
                    cur_x = int(self.width() * 2 / 3)
            else:
                # 将存牌区和出牌区隔出1/6的空间
                card_width = int(self.width()*5/6)
                card_height = int(pix_card.height() * card_width / pix_card.width())
                if self.player == 3:
                    cur_x = 0
                elif self.player == 2:
                    cur_x = int(self.width()/6)
            # 两张牌之间重叠1/3，因此中间点牌占的总宽度就是2/3*h*n+1/3*h
            stack_ratio = 1 / 3
            all_cards_height = ((1 - stack_ratio) * len(self.cards) + stack_ratio) * card_height
            while all_cards_height > self.height():
                stack_ratio += 0.01
                all_cards_height = ((1 - stack_ratio) * len(self.cards) + stack_ratio) * card_height
                if stack_ratio > 5 / 6:
                    # 此处写如果重叠率到了3/4还不行的情况，应该折行，懒得写了
                    break
            cur_y = int((self.height() - all_cards_height) / 2 + i * card_height*(1-stack_ratio))
            pix_card = pix_card.scaledToHeight(card_height)
            tmp_card_info = {'index': i, 'pix': pix_card, 'x': cur_x, 'y': cur_y}
            self.card_infos.append(tmp_card_info)
            painter.drawPixmap(cur_x, cur_y, pix_card)


class PukeThree(QFrame):
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
            card_file = find_card_image(self.cards[i])
            pix_card = QPixmap(card_file)

            # 横向的两张牌之间重叠3/4，纵向的牌重叠stack_ratio
            card_height = self.parent.get_default_out_card_height()  #让2号和3号玩家出牌的高度和1号玩家一致
            card_width = int(pix_card.width() * card_height / pix_card.height())

            #计算一下一行可以放多少张牌,((n-1)/4+1)*width = self.width, n=4*self.width/width-3
            if card_width == 0:
                cards_per_row == 1
            else:
                cards_per_row = int(4 * self.width() / card_width) - 3
            # 其实这时候已经放不下一张牌了，就强制放一张好了
            if cards_per_row == 0:
                cards_per_row = 1
            cur_x = (i % cards_per_row) * card_width / 4
            # 如果是2号玩家，应该靠右，画图起点在所有牌的
            if self.player == 2:
                if len(self.cards) < cards_per_row:
                    cur_x = cur_x + int(self.width() - card_width*(len(self.cards)+3)/4)
            # 两张牌之间重叠1/3，因此中间点牌占的总宽度就是2/3*h*n+1/3*h
            stack_ratio = 1 / 3
            all_cards_height = ((1 - stack_ratio) * len(self.cards) / cards_per_row + stack_ratio) * card_height
            while all_cards_height > self.height():
                stack_ratio += 0.01
                all_cards_height = ((1 - stack_ratio) * len(self.cards) + stack_ratio) * card_height
                if stack_ratio > 5 / 6:
                    # 此处写如果重叠率到了3/4还不行的情况，应该折行，懒得写了
                    break
            cur_y = (1-stack_ratio)*card_height*int(i/cards_per_row)
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


class RecordsWindow(QDialog):
    def __init__(self, name, parent=None):
        super().__init__()
        self.name = name
        self.InitUI()

    def InitUI(self):
        if 'data.db' in os.listdir():
            records = read_db(self.name)
        else:
            records = {}
        if not records:
            text = 'No records of ' + self.name + ' found!'
        else:
            text = self.name + '\的记录：\n 游戏总次数: ' + str(records['total']) + '次\n' + '胜局次数：' +\
                   str(records['win']) + '次\n' + '获胜率：' + str(100*records['win']/records['total']) + '%\n' + \
                   '总积分：' + str(records['jifen']) + '分\n\n\n' + '积分规则：胜了则赢取叫分的分值，输了则减掉叫分的分值\n地主加倍'
        lbl_records = QLabel(text)
        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.close)
        vbox = QVBoxLayout()
        vbox.addWidget(lbl_records)
        vbox.addWidget(ok_button)
        self.setLayout(vbox)
        self.setWindowTitle('Records')
        self.show()

class InfosWindow(QDialog):
    def __init__(self, text, parent=None):
        super().__init__()
        self.text = text
        self.InitUI()

    def InitUI(self):
        text = self.text
        lbl_records = QLabel(text)
        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.close)
        vbox = QVBoxLayout()
        vbox.addWidget(lbl_records)
        vbox.addWidget(ok_button)
        self.setLayout(vbox)
        self.setWindowTitle('Records')
        self.show()

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

def read_db(name):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('select * from doudizhu where name=?', (name, ))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if not result:
        return {}
    records = {}
    records['total'] = result[0][2]
    records['win'] = result[0][3]
    records['jifen'] = result[0][4]
    return records

def write_db(name, jifen):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    records_now = read_db(name)
    if jifen:
        win = 1
    else:
        win = 0
    if not records_now:
        cursor.execute('insert into doudizhu (name, total, win, jifen) VALUES ("%s", %d, %d, %d)'%(name, 1, win, jifen))
    else:
        total = records_now['total'] + 1
        win += records_now['win']
        jifen += records_now['jifen']
        cursor.execute('update doudizhu set total=?, win=?, jifen=? where name=?', (total, win, jifen, name, ))
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # replay = ReplayWindow('地主')
    doudizhu = DouDiZhu(1)
    app.exec_()