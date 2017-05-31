import sys
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QApplication, QGridLayout, QPushButton, QMainWindow, QDesktopWidget
from PyQt5 import QtCore

class LogIn(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initui()

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
            elif name == 'jarrod' and pwd == 'jarrod':
                self.close()
            elif name == 'new':
                self.grid.addWidget(self.lbl_pwd2, 3, 0)
                self.grid.addWidget(self.qle_pwd2, 3, 1, 1, 4)
                self.statusBar().showMessage('New account, please reenter your password!')
                pwd2 = self.qle_pwd2.text()
                if pwd != pwd2:
                    self.statusBar().showMessage('two different passwords, please check!')
                elif pwd2 == '':
                    self.statusBar().showMessage('New account, please reenter your password!')
                    self.qle_pwd2.setFocus()
                    self.login_button.setText('Register')
                else:
                    self.statusBar().showMessage('please remember your password!')
                    self.close()
            else:
                self.statusBar().showMessage('password not right!')

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
            (screen.height()-size.height())/2)

    # 想按回车直接开始验证，这个函数没用，不知道为啥
    def keyPressEvent(self, QKeyEvent):
        key = QKeyEvent.key()
        if key == QtCore.Qt.Key_Enter:
            print('yes')
            self.login_button.clicked()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LogIn()
    sys.exit(app.exec_())