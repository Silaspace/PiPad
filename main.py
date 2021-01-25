import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QFile, QIODevice
from PyQt5.QtWidgets import QTextEdit, QMainWindow, QAction, QMenu, QApplication, QToolBar
from PyQt5.QtGui import QIcon, QPixmap
from PIL import ImageGrab, ImageShow

import ocr

class Canvas(QtWidgets.QLabel):

    def __init__(self):
        super().__init__()
        pixmap = QPixmap(750,300)
        pixmap.fill(QtGui.QColor('white'))
        self.setPixmap(pixmap)
        self.penWidth = 4

        self.last_x, self.last_y = None, None
        self.pen_color = QtGui.QColor('black')

    def reset(self):
        painter = QtGui.QPainter(self.pixmap())
        p = painter.pen()  #Makes a pen
        p.setWidth(2)
        p.setColor(QtGui.QColor('white'))
        painter.setPen(p)
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor('white'))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)
        painter.drawRect(0,0,750,300)
        painter.end()
        self.update()


    def set_pen_color(self, c):
        self.pen_color = QtGui.QColor(c)

    def mouseMoveEvent(self, e):
        if self.last_x is None: # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return # Ignore the first time.

        painter = QtGui.QPainter(self.pixmap())
        p = painter.pen()  #Makes a pen
        p.setWidth(self.penWidth)
        p.setColor(self.pen_color)
        painter.setPen(p)
        painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        painter.end()
        self.update()

        # Update the origin for next time.
        self.last_x = e.x()
        self.last_y = e.y()

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.pages = [QTextEdit('Text')]
        self.initUI()
        self.penWidth = 4
        self.canvas = Canvas()
        
        self.w = QtWidgets.QWidget()
        self.h = QtWidgets.QVBoxLayout()
        self.w.setLayout(self.h)
        self.l = QtWidgets.QStackedLayout()
        self.h.addLayout(self.l)
        self.l.addWidget(self.pages[0])
        self.h2 = QtWidgets.QStackedLayout()
        self.h.addLayout(self.h2)
        self.h2.addWidget(self.canvas)

        self.setCentralWidget(self.w)
        self.l.currentChanged.connect(self.BarDisplayUpdate)
        print("1")

        print("2")
    
    def initUI(self):
        print("3")
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.RightToolBarArea,toolbar)
        toolbar.addSeparator()

        self.nextPageButton = QAction(QIcon('resources/NewPageIcon.PNG'),'Next/New page',self)
        self.nextPageButton.triggered.connect(self.NextPage)
        toolbar.addAction(self.nextPageButton)
        toolbar.addSeparator()

        self.lastPageButton = QAction(QIcon('resources/InvalidLastPageIcon.PNG'),'Previous page',self)
        self.lastPageButton.triggered.connect(self.LastPage)
        toolbar.addAction(self.lastPageButton)
        toolbar.addSeparator()

        self.pageDisplay = QtWidgets.QLabel('1 / 1', self)
        toolbar.addWidget(self.pageDisplay)
        toolbar.addSeparator()

        self.interpretButton = QAction(QIcon('resources/InterpretIcon.PNG'),'Interpret',self)
        self.interpretButton.triggered.connect(self.ReadText)
        toolbar.addAction(self.interpretButton)
                                       
        self.setGeometry(200,200,750,600)
        self.setWindowTitle('Demo')
        self.show()

        

    def NextPage(self):
        current = self.l.currentIndex()
        nextPage = current +1
        if current != len(self.pages)-1:
            if nextPage == len(self.pages)-1:
                self.nextPageButton.setIcon(QIcon('resources/NewPageIcon.PNG'))
            self.l.setCurrentIndex(nextPage)
        else:
            newPage = QTextEdit()
            self.l.addWidget(newPage)
            self.pages.append(newPage)
            self.l.setCurrentIndex(nextPage)
        #self.pageDisplay.setText(nextPage+1,'/',len(self.pages))
        self.lastPageButton.setIcon(QIcon('resources/LastPageIcon.PNG'))

    def LastPage(self):
        current = self.l.currentIndex()
        if current != 0:
            self.l.setCurrentIndex(current-1)
            self.nextPageButton.setIcon(QIcon('resources/NextPageIcon.PNG'))
            #self.pageDisplay.setText(current,'/',len(self.pages))
            #if lastPage-1 == 0:
                #self.lastPageButton.setIcon(QIcon('resources/InvalidLastPageIcon.PNG'))

    def BarDisplayUpdate(self):
        current = self.l.currentIndex()
        if current == 0:
            self.lastPageButton.setIcon(QIcon('resources/InvalidLastPageIcon.PNG'))
        newPageDisplay = str(current+1)+' / '+str(len(self.pages))
        self.pageDisplay.setText(newPageDisplay)
        
    def ReadText(self):
        global data
        data = ImageGrab.grab(bbox=(200,480,970,800))
        text = ocr.process(data)
        print(data)
        print(text)
        self.canvas.reset()
        

    
def main():
    with open("styles.css", "r") as f:
        app = QApplication(sys.argv)
        ex = MainWindow()
        ex.setStyleSheet(f.read())
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
    ImageShow.show(a)

    
##app = QtWidgets.QApplication(sys.argv)
##window = MainWindow()
##window.show()
##app.exec_()
