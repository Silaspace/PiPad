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
        self.image = QImage(1200, 300, QImage.Format_RGB32)
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


class Keyboard(QtWidgets.QGridLayout):
    def __init__(self, display, rackStack, *args):
        super().__init__()
        self.keys = {}
        self.display = display
        self.rackStack = rackStack

        for rowNum, keyRow in enumerate(args):
            self.makeKeyRow(rowNum, keyRow)

        for num, key in enumerate(['Shift','Space','Backspace']):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.addWidget(self.keys[key], 4, 4*(num), 1, 4)

        self.keys['Shift'].clicked.connect(self.Shift)
        self.keys['Space'].clicked.connect((self.makeKey(' ')))
        self.keys['Backspace'].clicked.connect(self.Backspace)
        

    def makeKey(self, key):
        return lambda: self.display.currentWidget().insertPlainText(key)

    def makeKeyRow(self, rowNum, keyRow):
        for colNum, key in enumerate(keyRow):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.addWidget(self.keys[key], rowNum, colNum)
            if key == '&&':       #This is completely necessary
                self.keys['&&'].clicked.connect((self.makeKey('&')))
            else:
                self.keys[key].clicked.connect((self.makeKey(key)))

    def Backspace(self):
        self.display.currentWidget().insertPlainText('|')
        text = self.display.currentWidget().toPlainText()
        delpos = text.find('|')
        if delpos != 0:
            self.display.currentWidget().setPlainText(text[delpos+1:])
            self.display.currentWidget().insertPlainText(text[:delpos-1])
        else:
            self.display.currentWidget().setPlainText(text[1:])

    def Shift(self):
        if self.rackStack.currentIndex() == 1:
            self.rackStack.setCurrentIndex(2)
        else:
            self.rackStack.setCurrentIndex(1)

# Still a prototype, for some reason it dislikes me :(
class savedNote:

    def __init__(title, self):
        return QAction(title)

    def clicked():
        pass



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
        self.display = QtWidgets.QStackedLayout()
        self.h.addLayout(self.display)
        self.display.addWidget(self.pages[0])
        self.h2 = QtWidgets.QStackedLayout()
        self.h.addLayout(self.h2)
        self.h2.addWidget(self.canvas)
        
        kb1 = QtWidgets.QWidget()
        self.normboard = Keyboard(self.display, self.h2,
                                  '1234567890-=',
                                  'qwertyuiop[]',
                                  "asdfghjkl;'#",
                                  '\zxcvbnm,./`')
        kb1.setLayout(self.normboard)
        kb2 = QtWidgets.QWidget()
        self.shiftboard = Keyboard(self.display, self.h2,
                                   ['!','"','£','$','%','^','&&','*','(',')','_','+'],
                                   'QWERTYUIOP{}',
                                   'ASDFGHJKL:@~',
                                   '|ZXCVBNM<>?¬')
        kb2.setLayout(self.shiftboard)
        self.h2.addWidget(kb1)
        self.h2.addWidget(kb2)

        self.setCentralWidget(self.w)
        self.display.currentChanged.connect(self.BarDisplayUpdate)
    
    def initUI(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea,toolbar) # Switched toolbar to left cause it looked cool

        # ------------------------------------------------------------------#
        # Prototype code for GUI save/load
        # ------------------------------------------------------------------#

        self.toolbar_head = QtWidgets.QLabel('Pages',self)
        toolbar.addWidget(self.toolbar_head)
        toolbar.addSeparator()

        all_saved = ["title", "test", "example"]
        self.saved_note_buttons = []

        #for i in all_saved:
        #    self.saved_note_buttons.append(savedNote(i))
        #    self.saved_note_buttons[::-1].triggered.connect(self.saved_note_buttons[::-1].clicked)
        #    toolbar.addAction(self.self.saved_note_buttons[::-1])
        #    toolbar.addSeparator()


        # ------------------------------------------------------------------#

        self.nextPageButton = QAction(QIcon('resources/NewPageIcon.PNG'),'Next/New page',self)
        self.nextPageButton.triggered.connect(self.NextPage)
        toolbar.addAction(self.nextPageButton)
        toolbar.addSeparator()

        self.lastPageButton = QAction(QIcon('resources/InvalidLastPageIcon.PNG'),'Previous page',self)
        self.lastPageButton.triggered.connect(self.LastPage)
        toolbar.addAction(self.lastPageButton)
        toolbar.addSeparator()

        self.pageDisplay = QtWidgets.QLabel('1 / 1', self)#.setAlignment(Qt.AlignCenter) Trying to center it, not working rn.
        toolbar.addWidget(self.pageDisplay)
        toolbar.addSeparator()

        self.interpretButton = QAction(QIcon('resources/InterpretIcon.PNG'),'Interpret',self)
        self.interpretButton.triggered.connect(self.ReadText)
        toolbar.addAction(self.interpretButton)
        toolbar.addSeparator()

        self.boardSwitchButton = QAction('Swap Input', self)
        self.boardSwitchButton.triggered.connect(self.BoardSwitch)
        toolbar.addAction(self.boardSwitchButton)
        toolbar.addSeparator()

        self.newLineButton = QAction('New line', self)
        self.newLineButton.triggered.connect(self.NewLine)
        toolbar.addAction(self.newLineButton)
                                       
        self.setGeometry(200,200,750,600)
        self.setWindowTitle('PiPad')
        self.show()

        

    def NewLine(self):
        current = self.display.currentIndex()
        self.pages[current].insertPlainText('\n')

    def NextPage(self):
        current = self.display.currentIndex()
        nextPage = current +1
        if current != len(self.pages)-1:
            if nextPage == len(self.pages)-1:
                self.nextPageButton.setIcon(QIcon('resources/NewPageIcon.PNG'))
            self.display.setCurrentIndex(nextPage)
        else:
            newPage = QTextEdit()
            self.display.addWidget(newPage)
            self.pages.append(newPage)
            self.display.setCurrentIndex(nextPage)
        self.lastPageButton.setIcon(QIcon('resources/LastPageIcon.PNG'))

    def LastPage(self):
        current = self.display.currentIndex()
        if current != 0:
            self.display.setCurrentIndex(current-1)
            self.nextPageButton.setIcon(QIcon('resources/NextPageIcon.PNG'))

    def BarDisplayUpdate(self):
        current = self.display.currentIndex()
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
        mod = img.convert('L').point(fn, mode='1')

        text = pytesseract.image_to_string(mod, config ='--psm 10')
        self.pages[self.display.currentIndex()].insertPlainText(text.strip())
        self.canvas.clearImage()

    def BoardSwitch(self):
        if self.h2.currentIndex() == 0:
            self.h2.setCurrentIndex(1)
        else:
            self.h2.setCurrentIndex(0)

    
def main():
    with open("styles.css", "r") as f:
        app = QApplication(sys.argv)
        ex = MainWindow()
        ex.setStyleSheet(f.read())
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
