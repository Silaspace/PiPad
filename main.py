import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QIODevice, QBuffer
from PyQt5.QtGui import QIcon, QImage, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QTextEdit, QMainWindow, QAction, QApplication, QToolBar

import pytesseract
from PIL import Image
from io import BytesIO

class Canvas(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setAttribute(Qt.WA_StaticContents)
        self.myPenWidth = 5
        self.myPenColor = Qt.black
        self.image = QImage(750, 300, QImage.Format_RGB32)
        self.path = QPainterPath()
        self.clearImage()

    def setPenColor(self, newColor):
        self.myPenColor = newColor

    def setPenWidth(self, newWidth):
        self.myPenWidth = newWidth

    def clearImage(self):
        self.path = QPainterPath()
        self.image.fill(Qt.white)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(event.rect(), self.image, self.rect())

    def mousePressEvent(self, event):
        self.path.moveTo(event.pos())

    def mouseMoveEvent(self, event):
        self.path.lineTo(event.pos())
        p = QPainter(self.image)
        p.setPen(QPen(self.myPenColor, self.myPenWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(self.path)
        p.end()
        self.update()



class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.pages = [QTextEdit()]
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
    
    def initUI(self):
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
        self.lastPageButton.setIcon(QIcon('resources/LastPageIcon.PNG'))

    def LastPage(self):
        current = self.l.currentIndex()
        if current != 0:
            self.l.setCurrentIndex(current-1)
            self.nextPageButton.setIcon(QIcon('resources/NextPageIcon.PNG'))

    def BarDisplayUpdate(self):
        current = self.l.currentIndex()
        if current == 0:
            self.lastPageButton.setIcon(QIcon('resources/InvalidLastPageIcon.PNG'))
        newPageDisplay = str(current+1)+' / '+str(len(self.pages))
        self.pageDisplay.setText(newPageDisplay)
        
    def ReadText(self):

        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        self.canvas.image.save(buffer, "PNG")
        data = BytesIO(buffer.data())
        buffer.close()

        img = Image.open(data)
        thresh = 200
        fn = lambda x : 255 if x > thresh else 0
        n_img = img.convert('L').point(fn, mode='1')

        text = pytesseract.image_to_string(n_img, config ='--psm 10')
        self.pages[self.l.currentIndex()].insertPlainText(text.strip())
        self.canvas.clearImage()
        

    
def main():
    with open("styles.css", "r") as f:
        app = QApplication(sys.argv)
        ex = MainWindow()
        ex.setStyleSheet(f.read())
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
