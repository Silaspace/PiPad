import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QIODevice, QBuffer
from PyQt5.QtGui import QIcon, QImage, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QTextEdit, QMainWindow, QAction, QApplication, QToolBar, QSizePolicy

##import pytesseract
from PIL import Image
from io import BytesIO

# Global Variables

path = os.getcwd() + "/saved/"

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
    def __init__(self, display, rackStack, shift=False):
        super().__init__()
        self.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.keys = {}
        self.display = display
        self.rackStack = rackStack
        keysToAdd = (['!','"','£','$','%','^','&&','*','(',')','_','+'],
                                   'QWERTYUIOP{}',
                                   'ASDFGHJKL:@~',
                                   '|ZXCVBNM<>?¬'
                     ) if shift else ('1234567890-=',
                                  'qwertyuiop[]',
                                  "asdfghjkl;'#",
                                  '\zxcvbnm,./`')

        for rowNum, keyRow in enumerate(keysToAdd):
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
        self.display.currentWidget().insertPlainText('~€')
        text = self.display.currentWidget().toPlainText()
        delpos = text.find('~€')
        if delpos != 0:
            self.display.currentWidget().setPlainText(text[delpos+2:])
            self.display.currentWidget().insertPlainText(text[:delpos-1])
        else:
            self.display.currentWidget().setPlainText(text[2:])

    def Shift(self):
        if self.rackStack.currentIndex() == 1:
            self.rackStack.setCurrentIndex(2)
        else:
            self.rackStack.setCurrentIndex(1)

class savedNote:

    def __init__(self, title, parent):
        self.display = QAction(title, parent)
        self.path = "path/to/file"
        self.parent = parent

    def clicked(self, a):
        pass

class TextInputDialog(QtWidgets.QDialog):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self.setWindowTitle('Text Input')
        buttons = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.inputField = QtWidgets.QTextEdit()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.inputField)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def sendData(self):
        self.parent().dataSlot = self.inputField.toPlainText()
        self.accept()


class MainWindow(QtWidgets.QMainWindow):

    ctrlChr = '~r'

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
        self.normboard = Keyboard(self.display, self.h2)
        kb1.setLayout(self.normboard)
        kb2 = QtWidgets.QWidget()
        self.shiftboard = Keyboard(self.display, self.h2, True)
        kb2.setLayout(self.shiftboard)
        self.h2.addWidget(kb1)
        self.h2.addWidget(kb2)

        self.setCentralWidget(self.w)
    
    def initUI(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea,toolbar) # Switched toolbar to left cause it looked cool
        
        # Saved Notes
        # ------------------------------------------------------------------------------------- #
        self.notes_heading = QtWidgets.QLabel('Saved Notes',self)
        toolbar.addWidget(self.notes_heading)
        toolbar.addSeparator()

        all_saved = ["title", "test", "example"]
        self.saved_note_buttons = []

        for i in all_saved:
            self.saved_note_buttons.append(savedNote(i, self))
            self.saved_note_buttons[::-1][0].display.triggered.connect(self.saved_note_buttons[::-1][0].clicked)
            toolbar.addAction(self.saved_note_buttons[::-1][0].display)


        # Pages heading
        # ------------------------------------------------------------------------------------- #
        self.pages_head = QtWidgets.QLabel('Pages',self)
        toolbar.addWidget(self.pages_head)
        toolbar.addSeparator()

        self.nextPageButton = QAction(QIcon('NewPageIcon.PNG'),'Next/New page',self)
        self.nextPageButton.triggered.connect(self.NextPage)
        toolbar.addAction(self.nextPageButton)

        self.lastPageButton = QAction(QIcon('InvalidLastPageIcon.PNG'),'Previous page',self)
        self.lastPageButton.triggered.connect(self.LastPage)
        toolbar.addAction(self.lastPageButton)

        self.saveButton = QAction('Save',self)
        self.saveButton.triggered.connect(self.SaveNotes)
        toolbar.addAction(self.saveButton)

        self.pageDisplay = QtWidgets.QLabel('1 / 1', self)#.setAlignment(Qt.AlignCenter) Trying to center it (horizontally), not working rn.
        toolbar.addWidget(self.pageDisplay)


        # Special controls heading
        # ------------------------------------------------------------------------------------- #
        self.controls_head = QtWidgets.QLabel('Controls',self)
        toolbar.addWidget(self.controls_head)
        toolbar.addSeparator()

        self.interpretButton = QAction(QIcon('InterpretIcon.PNG'),'Interpret',self)
        self.interpretButton.triggered.connect(self.ReadText)
        toolbar.addAction(self.interpretButton)

        self.boardSwitchButton = QAction('Swap Input', self)
        self.boardSwitchButton.triggered.connect(self.BoardSwitch)
        toolbar.addAction(self.boardSwitchButton)

        self.newLineButton = QAction('New line', self)
        self.newLineButton.triggered.connect(self.NewLine)
        toolbar.addAction(self.newLineButton)

        self.loadButton = QAction('Load file', self)
        self.loadButton.triggered.connect(self.LoadNotes)
        toolbar.addAction(self.loadButton)

        self.dialogTestButton = QAction('dialog test',self)
        self.dialogTestButton.triggered.connect(self.getTextDialog)
        toolbar.addAction(self.dialogTestButton)
                                       
        self.setGeometry(200,200,750,600)
        self.setWindowTitle('PiPad')
        self.show()

    #-----------------IMPORTANT STUFF TO USE----------------------------

    def NewLine(self):
        current = self.display.currentIndex()
        self.pages[current].insertPlainText('\n')

    def NextPage(self):
        current = self.display.currentIndex()
        nextPage = current +1
        if current != len(self.pages)-1:
            self.display.setCurrentIndex(nextPage)
        else:
            newPage = QTextEdit()
            self.display.addWidget(newPage)
            self.pages.append(newPage)
            self.display.setCurrentIndex(nextPage)
        self.BarDisplayUpdate()

    def LastPage(self):
        current = self.display.currentIndex()
        if current != 0:
            self.display.setCurrentIndex(current-1)
        self.BarDisplayUpdate()

    def BarDisplayUpdate(self):
        current = self.display.currentIndex()+1
        total = self.display.count()
        if current == 1:
            self.lastPageButton.setIcon(QIcon('InvalidLastPageIcon.PNG'))
        else:
            self.lastPageButton.setIcon(QIcon('LastPageIcon.PNG'))
        if current == total:
            self.nextPageButton.setIcon(QIcon('NewPageIcon.PNG'))
        else:
            self.nextPageButton.setIcon(QIcon('NextPageIcon.PNG'))
        newPageDisplay = str(current)+' / '+str(total)
        self.pageDisplay.setText(newPageDisplay)

    #------------------------END OF IMPORTANT STUFF-----------------------
        
    def ReadText(self):
        # -------------------------------------------------------------- #
        # Alex Walker have a look below! ------------------------------- #

        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        self.canvas.image.save(buffer, "PNG")
        data = BytesIO(buffer.data())
        buffer.close()
        img = Image.open(data) # PIL image format

        # -------------------------------------------------------------- #


        thresh = 200
        fn = lambda x : 255 if x > thresh else 0
        mod = img.convert('L').point(fn, mode='1')

        text = 'CONVERTED#¦ STUFF'

##        text = pytesseract.image_to_string(mod, config ='--psm 10')
        text = text.replace("~€", "")
        self.pages[self.display.currentIndex()].insertPlainText(text.strip())
        self.canvas.clearImage()

    def BoardSwitch(self):
        if self.h2.currentIndex() == 0:
            self.h2.setCurrentIndex(1)
        else:
            self.h2.setCurrentIndex(0)

    def getTextDialog(self):
        self.dataSlot = ''
        dlg = TextInputDialog(self)
        if dlg.exec_():
            print('success')
            #self.display.currentWidget().insertPlainText(self.dataSlot)
        

    def SaveNotes(self, a):
        content = [i.toPlainText() for i in self.pages]
        name = "".join(content[0].split(" ")[:2])

        with open(path + name, "w") as f:
            f.write("~¦".join(content))

    def LoadNotes(self):    #IMPORTANT STUFF AS WELL
        fileName = 'LoadTest.txt' #To be replaced with SelectionDialog
        with open(fileName, 'r') as file:
            contents = (file.read()).split(self.ctrlChr)
        newpages = [QTextEdit(pageText) for pageText in contents]
        self.pages.append(newpages[0])                  #Set up page 1 (for visuals)
        self.display.addWidget(newpages[0])             #
        self.display.setCurrentWidget(newpages.pop(0))  #
        for i in range(1,len(self.pages)):                #Remove previous pages
            self.display.removeWidget(self.pages.pop(0))  #
        if len(newpages) >= 1:                    #Add the rest of the new pages
            for page in newpages:                 #
                self.pages.append(page)           #
                self.display.addWidget(page)      #
        self.BarDisplayUpdate()                 #And fix the bar display


    
def main():
    #with open("styles.css", "r") as f:
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = MainWindow()
        #ex.setStyleSheet(f.read())
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
