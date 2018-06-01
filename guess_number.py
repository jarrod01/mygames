import sys, sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from random import randint

class GuessNumber(QMainWindow):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.try_times = 0
        self.level = 4
        self.answer = num_generator(self.level)
        self.time_count = 0
        self.records = read_db(self.name)

        self.initUI()

    def initUI(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.add_time)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        recordsAction = QAction('&Records', self)
        recordsAction.setShortcut('Ctrl+R')
        recordsAction.setStatusTip('Show your records')
        recordsAction.triggered.connect(self.show_records)

        self.statusBar()
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(recordsAction)
        fileMenu.addAction(exitAction)
        # 用来创建窗口内的菜单栏
        menubar.setNativeMenuBar(False)

        widget = QWidget()
        lbl_level = QLabel('Level: ')
        self.comb_level = QComboBox()
        for i in range(1,5):
            self.comb_level.addItem(str(i))
        self.comb_level.setCurrentText('2')
        self.comb_level.activated[str].connect(self.level_choosed)
        self.lcd_time = QLCDNumber()
        self.lcd_time.setDigitCount(7)
        self.lcd_time.setSegmentStyle(QLCDNumber.Flat)
        self.lbl_tips = QLabel('Now enter 4 different numbers between 0~9')

        self.qle_nums = QLineEdit()
        self.qle_nums.setAlignment(Qt.AlignCenter)
        self.qle_nums.setMaxLength(self.level)
        self.qle_nums.setValidator(QIntValidator(0, 1000000))

        self.lbl_result = QLabel()
        self.lbl_result.setAlignment(Qt.AlignTop)
        btn_check = QPushButton('Check')
        btn_check.clicked.connect(self.button_clicked)
        grid = QGridLayout()
        grid.addWidget(lbl_level, 0, 0)
        grid.addWidget(self.comb_level, 0, 1)
        grid.addWidget(self.lcd_time, 0, 2)
        grid.addWidget(self.lbl_tips, 1, 0, 1, 3)
        grid.addWidget(self.qle_nums, 2, 0)
        grid.addWidget(btn_check, 2, 2)
        grid.addWidget(self.lbl_result, 3, 0, 5, 3)

        widget.setLayout(grid)
        self.setCentralWidget(widget)
        if self.name == '':
            self.setWindowTitle('Guess Number')
        else:
            self.setWindowTitle('Guess Number --' + self.name)
        self.resize(400, 300)
        self.center()
        self.show()
        self.qle_nums.editingFinished.connect(self.button_clicked)
        self.qle_nums.setFocus()

    def level_choosed(self, text):
        self.level = int(text) + 2
        self.statusBar().showMessage('you have chosen level ' + text)
        self.reset(True)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
            (screen.height()-size.height())/2)

    def button_clicked(self):
        if self.try_times == 0:
            self.lbl_result.setText('')
            self.timer.start(1)
        # self.statusBar().showMessage(self.answer)
        input_num = self.qle_nums.text()
        self.qle_nums.clear()
        result = check_answer(input_num, self.answer, self.level)
        lbl_message = self.lbl_result.text()
        if result['validate']:
            self.try_times += 1
            if result['message'] != 'right':
                if self.try_times == 10:
                    message = 'the right answer is ' + self.answer
                    self.reset(False)
                else:
                    times_remain = 10 - self.try_times
                    message = 'times remain: ' + str(times_remain) + '. ' + result['message']
            else:
                message = input_num + ', congratulations, you got it in ' + str(self.time_count/1000) + ' seconds!'
                self.records = read_db(self.name)
                if self.level in self.records.keys():
                    if self.time_count < self.records[self.level]['time'] or self.try_times < self.records[self.level]['steps']:
                        write_db(self.name, self.level, self.try_times, self.time_count/1000, 'update')
                        message += '\nNew records!'
                else:
                    write_db(self.name, self.level, self.try_times, self.time_count/1000)
                self.reset(False)
        else:
            message = result['message']
        self.lbl_result.setText(lbl_message + message + '\n')
        self.qle_nums.setFocus()

    def reset(self, clear_result):
        self.answer = num_generator(self.level)
        self.lbl_tips.setText('Now enter %s different numbers between 0~9' % str(self.level))
        self.qle_nums.setMaxLength(self.level)
        self.try_times = 0
        if clear_result:
            self.lbl_result.setText('')
        self.timer.stop()
        self.time_count = 0
        self.lcd_time.display(0.0)

    def add_time(self):
        self.time_count += 1
        self.lcd_time.display('%.3f'%(self.time_count/1000))

    def show_records(self):
        text = ''
        for level in self.records.keys():
            text = text + 'level ' + str(level-2) + ': ' + ", steps: " + str(self.records[level]['steps']) + ', time: ' + str(self.records[level]['time'])
        self.lbl_result.setText(text)


def num_generator(level):
    nums = []
    i = 0
    num_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    while (i < level):
        t = randint(0, 9 - i)
        nums.append(num_list[t])
        nums[i] = str(nums[i])
        num_list.remove(num_list[t])
        i += 1
    num = "".join(nums)
    return num

def check_answer(in_num, answer, level):
    validate = True
    message = 'right'
    if in_num == answer:
        return {'validate': validate, 'message': message}
    answer = list(answer)
    in_nums = list(in_num)

    if len(in_nums) != level:
        validate = False
        message = 'Please enter ' + str(level) + ' numbers!'
    elif len(set(in_nums)) < len(in_nums):
        validate = False
        message = 'Please enter ' + str(level) + ' different numbers'
    else:
        a_cnt = 0
        b_cnt = 0
        for i in range(level):
            if in_nums[i] == answer[i]:
                a_cnt += 1
            elif in_nums[i] in answer:
                b_cnt += 1
        message = 'your answer: ' + in_num + ', result: A' + str(a_cnt) + 'B' + str(b_cnt)
    return {'validate': validate, 'message': message}

def read_db(name):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('select * from number_guess where name=?', (name, ))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if not result:
        return {}
    records = {}
    for record in result:
        level = record[2]
        steps = record[3]
        time = record[4]
        records[level] = {'steps': steps, 'time': time}
    return records

def write_db(name, level, steps, time, update_type='insert'):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    if update_type == 'insert':
        cursor.execute('insert into number_guess (name, level, steps, time) VALUES (?, ?, ?, ?)',(name, level, steps, time, ))
    else:
        cursor.execute('update number_guess set steps=?, time=? where (name=? and level=?)', (steps, time, name, level, ))
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GuessNumber('jarrod')
    app.exec_()