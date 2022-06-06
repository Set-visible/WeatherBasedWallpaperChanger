import sys
import os
from PyQt5.QtCore import pyqtSignal, QObject, QEvent, Qt, QPoint
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5 import QtGui

import ctypes
from time import *
import threading
import WeatherAPI  # call inner project WeatherAPI.py
import absPath  # call inner project absPath.py
from PIL import Image

"""weather condition refresh interval"""
global timer
timer = 5  # default timer settings
global timer_reset
timer_reset = False  # this variable tells to thread which time is return or start
form_class = uic.loadUiType("./LayoutPlus_02.ui")[0]
global countThread
global BG  # this variable connected to daemon, if it has False state, background task will run
BG = True
global MinMaxState  # maximized=>1 other wize =>0
MinMaxState = 0
global CurrentImgData
CurrentImgData = ""

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
[w, h] = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]

class WindowClass(QMainWindow, form_class):
    resized = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.dragPos = None
        self.offset = None
        self.oldPosition = None
        self.setWindowIcon(QtGui.QIcon("./icons/umbrella.png"))
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setupUi(self)
        self.wallpaperList.clear()
        self.getWallpaperList()
        self.wallpaperList.itemDoubleClicked.connect(self.showPreview)
        self.initConTextMenu()
        self.intervalSlider.valueChanged.connect(self.setInterval)
        self.intervalSliderValue.setText("1")
        self.intervalBtn.clicked.connect(self.resetTimer)
        self.currentWeatherInfoLabel.setText("weather")
        self.backgroundCheckBox.clicked.connect(self.setBackgroundState)
        # 디테일 컨디션 테이블 사이즈에 맞게 항목 채우기
        self.detailedConditionTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.detailedConditionTable.setHorizontalHeaderLabels(WeatherAPI.getWeatherInfo_Detailed_Header())
        self.detailedConditionTable.setRowCount(0)  # 행 개수 0으로 초기화
        self.icon2 = QtGui.QIcon()
        self.icon2.addPixmap(QtGui.QPixmap("./icons/x_white.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_max = QtGui.QIcon()
        self.icon_max.addPixmap(QtGui.QPixmap("./icons/maximize_white.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_min = QtGui.QIcon()
        self.icon_min.addPixmap(QtGui.QPixmap("./icons/minimize_white.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_under = QtGui.QIcon()
        self.icon_under.addPixmap(QtGui.QPixmap("./icons/minus.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.exitBtn.setIcon(self.icon2)
        self.maximizeBtn.setIcon(self.icon_max)
        self.underBtn.setIcon(self.icon_under)
        self.TitleBarFrame.installEventFilter(self)
        self.resized.connect(self.changePreviewRatio)
        self.webEngineView.load(QtCore.QUrl("https://weather.naver.com/"))

        def changeMinMaxBtnState():
            global MinMaxState
            if MinMaxState == 0:
                self.maximizeBtn.setIcon(self.icon_min)
                self.resize(w, h)
                self.move(0, 0)
                print("currentStateMaximized")
                MinMaxState = 1
            else:
                self.maximizeBtn.setIcon(self.icon_max)
                self.resize(1198, 753)
                self.move(int(w/2-self.frame.width()/2), int(h/2-self.frame.height()/2))
                print("currentStateMinimized")
                MinMaxState = 0

        self.maximizeBtn.clicked.connect(changeMinMaxBtnState)

        def hideUnder():
            self.showMinimized()

        self.underBtn.clicked.connect(hideUnder)

        def closeScreen():
            self.close()

        self.exitBtn.clicked.connect(closeScreen)
        self.startInterval()
        # end of init

    def resizeEvent(self, event):
        self.resized.emit()
        return super().resizeEvent(event)

    def changePreviewRatio(self):
        global CurrentImgData
        if CurrentImgData != "":
            print(CurrentImgData)
            pixmap = QPixmap(CurrentImgData).scaled(self.imgLabel.width(), self.imgLabel.height())  # 이미지 비율
            self.imgLabel.setPixmap(pixmap)

    def eventFilter(self, source, event):
        global MinMaxState
        if source == self.TitleBarFrame:
            if event.type() == QEvent.MouseButtonPress:
                self.offset = event.pos()
                if MinMaxState == 1:
                    MinMaxState = 0
                    self.resize(1200, 755)
                    self.move(self.pos() - self.offset + event.pos())
                    self.maximizeBtn.setIcon(self.icon_max)
            elif event.type() == QEvent.MouseMove and self.offset is not None:
                # no need for complex computations: just use the offset to compute
                # "delta" position, and add that to the current one
                self.move(self.pos() - self.offset + event.pos())
                # return True to tell Qt that the event has been accepted and
                # should not be processed any further
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.offset = None
        # let Qt process any other event
        return super().eventFilter(source, event)

    def initConTextMenu(self):
        self.wallpaperList.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        action1 = QAction("이미지 바꾸기", self.wallpaperList)
        self.wallpaperList.addAction(action1)
        action1.triggered.connect(self.tmpAction)

    def overWriteImage(self, target, subject):
        target_ = Image.open(target)
        subject_ = Image.open(subject)
        target_ = subject_
        target_.save(target)

    def tmpAction(self):
        currentSelection = self.wallpaperList.currentItem().text()
        currentSelection = absPath.getAbsolutePath() + "/wallpapers/" + currentSelection
        data = QFileDialog.getOpenFileName(self, 'Open file', './', "Image Files (*.jpg)")

        if data[0]:
            target = data[0]
            self.overWriteImage(currentSelection, target)
        else:
            return 0

    def addWeatherDataToTable(self):
        datas = WeatherAPI.getWeatherInfo_Detailed_List()  # get list of Detailed weather data
        self.detailedConditionTable.insertRow(0)
        for x in range(len(datas)):
            self.detailedConditionTable.setItem(0, x, QTableWidgetItem(str(datas[x])))

    def setBackgroundState(self):
        global BG
        global timer_reset
        global countThread
        state = self.backgroundCheckBox.isChecked()
        if state is True:
            timer_reset = True
            print("daemon is False")
            countThread.join()
            BG = False
            timer_reset = False
            self.startInterval()
        else:
            timer_reset = True
            print("daemon is True")
            countThread.join()
            BG = True  # BG = False if state is True else BG = True
            timer_reset = False
            self.startInterval()
            # 이 함수로 UI창을 닫아도 백그라운드에서 계속 실행할지 아니면 종료할지 설정할 수 있습니다.

    def setWallpaperRefreshInterval(self):
        global timer
        global timer_reset
        while timer_reset is False:
            self.changeWeatherInfo()
            self.addWeatherDataToTable()
            for x in range(timer, 0, -1):
                if timer_reset is False:
                    """if ui slider btn have clicked, stop this thread and rerun with new timer value"""
                    sleep(1)
                    """at debug mode, developer have to see screen properly changed, 
                    so interval value is about 1~60sec when sleep value is 1 """
        print("타이머 객체 반환됨")

    def changeWeatherInfo(self):
        global CurrentImgData
        data = WeatherAPI.getWeatherInfo_Min()
        CurrentImgData = f"./wallpapers/{data}.jpg"
        pixmap = QPixmap(CurrentImgData).scaled(self.imgLabel.width(), self.imgLabel.height())
        loc = f"{absPath.getAbsolutePath()}/wallpapers/{data}.jpg"
        self.imgLabel.setPixmap(pixmap)
        self.currentWeatherInfoLabel.setText(data)
        self.changeWallpaper(loc)
        print(self.imgLabel.width())

    def changeWallpaper(self, data):
        ctypes.windll.user32.SystemParametersInfoW(20, 0, data, 3)

    def startInterval(self):
        global countThread
        global BG
        countThread = threading.Thread(target=self.setWallpaperRefreshInterval, daemon=BG)
        countThread.start()

    def setInterval(self):
        global timer
        self.intervalSliderValue.setText(str(self.intervalSlider.value()))
        timer = self.intervalSlider.value()
        '''set interval timer based on intervalSlider'''

    def resetTimer(self):
        global timer_reset
        global countThread
        timer_reset = True
        countThread.join()
        timer_reset = False
        self.startInterval()
        print("카운트 스레드 시작됨")

    """get wallpaperList from ./wallpapers"""

    def getWallpaperList(self):
        img_lists = os.listdir("./wallpapers")
        for img_list in img_lists:
            self.wallpaperList.addItem(img_list)

    def showPreview(self):
        """get img location from ListWidget"""
        global CurrentImgData
        img_location = self.wallpaperList.currentItem().text()
        CurrentImgData = f"./wallpapers/{img_location}"
        pixmap = QPixmap(CurrentImgData).scaled(self.imgLabel.width(), self.imgLabel.height())  # 이미지 비율
        self.imgLabel.setPixmap(pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WindowClass()
    ex.show()
    app.exec_()
