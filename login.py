import sys, sqlite3
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
import guess_number


class LogIn(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initui()
        self.loged_user = 'guest'

    def initui(self):
        self.widget = QWidget()
        lbl_tips = QLabel('Please Login')
        lbl_name = QLabel("Username: ")
        lbl_pwd = QLabel('Password: ')
        self.lbl_pwd2 = QLabel('Password: ')
        self.qle_name = QLineEdit()
        self.qle_pwd = QLineEdit()
        self.qle_pwd.setEchoMode(2)
        self.qle_pwd2 = QLineEdit()
        self.qle_pwd2.setEchoMode(2)
        self.skip_button = QPushButton('Skip')
        self.login_button = QPushButton('Login')
        self.skip_button.clicked.connect(self.buttonclicked)
        self.login_button.clicked.connect(self.buttonclicked)
        self.lbl_warning = QLabel()

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.grid.addWidget(lbl_tips, 0, 0, 1, 4)
        self.grid.addWidget(lbl_name, 1, 0)
        self.grid.addWidget(self.qle_name, 1, 1, 1, 4)
        self.grid.addWidget(lbl_pwd, 2, 0)
        self.grid.addWidget(self.qle_pwd, 2, 1, 1, 4)
        self.grid.addWidget(self.skip_button, 4, 0, 1, 1)
        self.grid.addWidget(self.login_button, 4, 3, 1, 2)

        self.widget.setLayout(self.grid)
        self.setCentralWidget(self.widget)
        self.setWindowTitle('Login')
        self.resize(300, 100)
        self.center()
        self.show()
        self.qle_name.editingFinished.connect(self.qle_pwd.setFocus)
        self.qle_pwd.editingFinished.connect(self.buttonclicked)
        self.qle_pwd2.editingFinished.connect(self.buttonclicked)

    def buttonclicked(self):
        sender = self.sender()
        button = sender.text()
        name = self.qle_name.text()
        pwd = self.qle_pwd.text()
        if button == 'Skip':
            self.close()
        else:
            if name == '':
                self.statusBar().showMessage('Please enter your name')
            else:
                key = read_db(name)
                if key:
                    pwd = md5(pwd)
                    if key == pwd:
                        self.loged_user = name
                        self.close()
                    else:
                        self.statusBar().showMessage('wrong password, please try again!')
                else:
                    self.grid.addWidget(self.lbl_pwd2, 3, 0)
                    self.grid.addWidget(self.qle_pwd2, 3, 1, 1, 4)
                    self.statusBar().showMessage('New account, please reenter your password!')
                    self.login_button.setText('Register')
                    # self.qle_pwd2.setFocus()
                    pwd2 = self.qle_pwd2.text()
                    if pwd == '':
                        self.statusBar().showMessage('Please enter your password')
                    else:
                        if pwd != pwd2:
                            self.statusBar().showMessage('two different passwords, please check!')
                        else:
                            pwd = md5(pwd)
                            write_db(name, pwd)
                            self.statusBar().showMessage('please remember your password!')
                            self.loged_user = name
                            self.close()
        app_pick = ChooseGame(self.loged_user)
        app_pick.show()
        # self.gn = guess_number.GuessNumber(name)
        # self.gn.show()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
            (screen.height()-size.height())/2)

    # def closeEvent(self, a0: QtGui.QCloseEvent):
        # loged_user = self.loged_user


class ChooseGame(QMainWindow):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.initUI()

    def initUI(self):
        widget = QWidget()
        btn_gn = PicButton(QtGui.QPixmap('pics/guess_number.png'), 'guess_number', self)
        btn_ddz = PicButton(QtGui.QPixmap('pics/doudizhu.png'), 'doudizhu', self)
        grid = QGridLayout()

        grid.addWidget(btn_gn, 0, 0)
        grid.addWidget(QLabel('Number Guess'), 1, 0)
        grid.addWidget(btn_ddz, 0, 1)
        grid.addWidget(QLabel('Dou Di Zhu'), 1, 1)
        widget.setLayout(grid)
        self.setCentralWidget(widget)
        self.setWindowTitle('Choose Game --' + self.name)
        self.show()
        self.center()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
            (screen.height()-size.height())/2)


class PicButton(QAbstractButton):
    def __init__(self, pixmap, app, parent_widget=None,):
        super(PicButton, self).__init__(parent_widget)
        self.pixmap = pixmap
        self.app = app
        self.parent_widget = parent_widget
        self.clicked.connect(self.choose_app)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()

    def choose_app(self):
        if self.app == 'guess_number':
            self.parent_widget.close()
            self.gn = guess_number.GuessNumber(self.parent_widget.name)
            self.gn.show()


def read_db(name):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('select key from users where name=?', (name, ))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if not result:
        return ''
    key = result[0][0]
    return key

def write_db(name, key):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('insert into users (name, key) VALUES ("%s", "%s")'%(name, key))
    conn.commit()
    cursor.close()
    conn.close()

def md5(key):
    import hashlib
    m = hashlib.md5()
    m.update(key.encode('utf-8'))
    return m.hexdigest()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LogIn()
    # ex = ChooseGame('jarrod')
    #sys.exit(app.exec_())
    app.exec_()
