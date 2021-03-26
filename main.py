import sys, os, math
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QIODevice, QBuffer
from PyQt5.QtGui import QIcon, QImage, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QTextEdit, QMainWindow, QAction, QApplication, QToolBar, QSizePolicy, QSpacerItem

#import pytesseract
from PIL import Image
from io import BytesIO

# Global Variables
#resourcepath = "Z:\PiPad-main\PiPad-main\\resources"
#csspath = "Z:\PiPad-main\PiPad-main\styles.css"
#path = "Z:\PiPad-main\PiPad-main\saved\\"

resourcepath = os.getcwd() + "/resources/"
csspath = os.getcwd() + "/styles.css"
path = os.getcwd() + "/saved/"

control = "~~~"

class Canvas(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setAttribute(Qt.WA_StaticContents)
        self.myPenWidth = 5
        self.myPenColor = Qt.white
        self.image = QImage(1200, 300, QImage.Format_RGB32)
        self.path = QPainterPath()
        self.clearImage()

    def setPenColor(self, newColor):
        self.myPenColor = newColor

    def setPenWidth(self, newWidth):
        self.myPenWidth = newWidth

    def clearImage(self):
        self.path = QPainterPath()
        self.image.fill(Qt.black)
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
        self.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.keys = {}
        self.display = display
        self.rackStack = rackStack

        for rowNum, keyRow in enumerate(args):
            self.makeKeyRow(rowNum, keyRow)

        for num, key in enumerate(['Shift','Space','Backspace']):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.keys[key].setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.addWidget(self.keys[key], 4, 4*(num), 1, 4)

        self.keys['Shift'].clicked.connect(self.Shift)
        self.keys['Space'].clicked.connect((self.makeKey(' ')))
        self.keys['Backspace'].clicked.connect(self.Backspace)
        

    def makeKey(self, key):
        return lambda: self.display.currentWidget().insertPlainText(key)

    def makeKeyRow(self, rowNum, keyRow):
        for colNum, key in enumerate(keyRow):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.keys[key].setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.addWidget(self.keys[key], rowNum, colNum)
            if key == '&&':       #This is completely necessary
                self.keys['&&'].clicked.connect((self.makeKey('&')))
            else:
                self.keys[key].clicked.connect((self.makeKey(key)))

    def Backspace(self):
        self.display.currentWidget().insertPlainText(control)
        text = self.display.currentWidget().toPlainText()
        delpos = text.find(control)
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

class savedNote:

    def __init__(self, title, parent):
        self.parent = parent
        self.display = QAction(title.split(".")[0], parent)
        self.path = path + title
    
    def delete(self):
        self.display.deleteLater()

    def clicked(self, a):
        with open(self.path, "r") as f:
            for i, c in enumerate(f.read().split(control)):
                self.parent.pages[i].insertPlainText(c)



class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.pages = [QTextEdit()]
        self.toolbar = QToolBar()
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
        
    def addNotes(self):
        all_saved = [] 
        for f in os.listdir(path):
            all_saved.append(f)

        self.saved_note_buttons = []
        for i in all_saved[:5]:
            self.saved_note_buttons.append(savedNote(i, self))
            self.saved_note_buttons[::-1][0].display.triggered.connect(self.saved_note_buttons[::-1][0].clicked)
            self.toolbar.addAction(self.saved_note_buttons[::-1][0].display)

    def initUI(self):
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea,self.toolbar)


        # Pages heading
        # ------------------------------------------------------------------------------------- #
        self.pages_head = QtWidgets.QLabel('        Pages',self)
        self.toolbar.addWidget(self.pages_head)
        self.toolbar.addSeparator()

        self.nextPageButton = QAction(QIcon(resourcepath+ '/NewPageIconInv.png'),'Next/New page',self)
        self.nextPageButton.triggered.connect(self.NextPage)
        self.toolbar.addAction(self.nextPageButton)

        self.lastPageButton = QAction(QIcon(resourcepath+'/InvalidLastPageIconInv.png'),'Previous page',self)
        self.lastPageButton.triggered.connect(self.LastPage)
        self.toolbar.addAction(self.lastPageButton)

        self.saveButton = QAction('Save',self)
        self.saveButton.triggered.connect(self.SaveNotes)
        self.toolbar.addAction(self.saveButton)

        self.pageDisplay = QtWidgets.QLabel('1 / 1', self)#.setAlignment(Qt.AlignCenter) Trying to center it (horizontally), not working rn.
        self.toolbar.addWidget(self.pageDisplay)


        # Special controls heading
        # ------------------------------------------------------------------------------------- #
        self.controls_head = QtWidgets.QLabel('      Controls',self)
        self.controls_head.setStyleSheet("padding-top: 50px")
        self.toolbar.addWidget(self.controls_head)
        self.toolbar.addSeparator()

        self.interpretButton = QAction(QIcon(resourcepath+'/InterpretIconInv.png'),'Interpret',self)
        self.interpretButton.triggered.connect(self.ReadText)
        self.toolbar.addAction(self.interpretButton)

        self.boardSwitchButton = QAction('Swap Input', self)
        self.boardSwitchButton.triggered.connect(self.BoardSwitch)
        self.toolbar.addAction(self.boardSwitchButton)

        self.newLineButton = QAction('New line', self)
        self.newLineButton.triggered.connect(self.NewLine)
        self.toolbar.addAction(self.newLineButton)
                                       
        self.setGeometry(200,200,750,600)
        self.setWindowTitle('PiPad')
        self.show()


        # Saved Notes
        # ------------------------------------------------------------------------------------- #
        self.notes_heading = QtWidgets.QLabel('    Saved Notes',self)
        self.notes_heading.setStyleSheet("padding-top: 50px")
        self.toolbar.addWidget(self.notes_heading)
        self.toolbar.addSeparator()
        
        self.addNotes()

        

    def NewLine(self):
        current = self.display.currentIndex()
        self.pages[current].insertPlainText('\n')

    def NextPage(self):
        current = self.display.currentIndex()
        nextPage = current +1
        if current != len(self.pages)-1:
            if nextPage == len(self.pages)-1:
                self.nextPageButton.setIcon(QIcon(resourcepath+'/NewPageIconInv.png'))
            self.display.setCurrentIndex(nextPage)
        else:
            newPage = QTextEdit()
            self.display.addWidget(newPage)
            self.pages.append(newPage)
            self.display.setCurrentIndex(nextPage)
        self.lastPageButton.setIcon(QIcon(resourcepath+'/LastPageIconInv.png'))

    def LastPage(self):
        current = self.display.currentIndex()
        if current != 0:
            self.display.setCurrentIndex(current-1)
            self.nextPageButton.setIcon(QIcon(resourcepath+'/NextPageIconInv.png'))

    def BarDisplayUpdate(self):
        current = self.display.currentIndex()
        if current == 0:
            self.lastPageButton.setIcon(QIcon(resourcepath+'/InvalidLastPageIconInv.png'))
        newPageDisplay = str(current+1)+' / '+str(len(self.pages))
        self.pageDisplay.setText(newPageDisplay)
        
    def ReadText(self):
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        self.canvas.image.save(buffer, "png")
        data = BytesIO(buffer.data())
        buffer.close()
        
        img = Image.open(data)
        thresh = 200
        fn = lambda x : 255 if x > thresh else 0
        img = img.convert('L').point(fn, mode='1')

        colour = (255, 255, 255)
        x_elements=[]
        y_elements=[]

        rgb_img = img.convert('RGB')
        for x in range(rgb_img.size[0]):
            for y in range(rgb_img.size[1]):
                r, g, b = rgb_img.getpixel((x, y))
                if (r,g,b) == colour:
                    x_elements.append(x)
                    y_elements.append(y)

        x3 = min(x_elements) - 20
        y3 = min(y_elements) - 20
        x4 = max(x_elements) + 20
        y4 = max(y_elements) + 20
        crop = img.crop((x3,y3,x4,y4))

        text = pytesseract.image_to_string(crop, config ='--psm 10')
        text = text.replace(control, "")
        self.pages[self.display.currentIndex()].insertPlainText(text.strip())
        self.canvas.clearImage()

    def BoardSwitch(self):
        if self.h2.currentIndex() == 0:
            self.h2.setCurrentIndex(1)
        else:
            self.h2.setCurrentIndex(0)
            


    def SaveNotes(self, a):
        content = [i.toPlainText() for i in self.pages]
        name = "".join(content[0].replace("\n", " ").split(" ")[:2]) + ".txt"

        with open(path + name, "a") as f:
            f.write(control.join(content))

        for note in self.saved_note_buttons:
            note.delete()

        self.addNotes()
    
def main():
    with open(csspath, "r") as f:
        app = QApplication(sys.argv)
        ex = MainWindow()
        ex.setStyleSheet(f.read())
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
