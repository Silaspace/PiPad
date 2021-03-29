import sys, os, math, time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QIODevice, QBuffer
from PyQt5.QtGui import QIcon, QImage, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QTextEdit, QMainWindow, QAction, QApplication, QToolBar, QSizePolicy

##import pytesseract
##from PIL import Image
from io import BytesIO

# Global Variables

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
    def __init__(self, display, rackStack, Shift = False, Stacked = True):
        super().__init__()
        self.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.stacked = Stacked
        self.keys = {}
        self.display = display
        self.rackStack = rackStack
        if Shift:
            KeysToAdd = (['!','"','£','$','%','^','&&','*','(',')','_','+'],
                        'QWERTYUIOP{}',
                        'ASDFGHJKL:@~',
                        '|ZXCVBNM<>?¬')
        else:
            KeysToAdd = ('1234567890-=',
                         'qwertyuiop[]',
                         "asdfghjkl;'#",
                         '\zxcvbnm,./`')

        for rowNum, keyRow in enumerate(KeysToAdd):
            self.makeKeyRow(rowNum, keyRow)

        for num, key in enumerate(['Shift','Space','Backspace']):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.keys[key].setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.addWidget(self.keys[key], 4, 4*(num), 1, 4)

        self.keys['Shift'].clicked.connect(self.Shift)
        self.keys['Space'].clicked.connect((self.makeKey(' ')))
        self.keys['Backspace'].clicked.connect(self.Backspace)
        

    def makeKey(self, key):

        if self.stacked:
            return lambda: self.display.currentWidget().insertPlainText(key)
        else:
            return lambda: self.display.insertPlainText(key)
    

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
        DanOrange = self.display.currentWidget() if self.stacked else self.display
        DanOrange.insertPlainText(control)
        text = DanOrange.toPlainText()
        delpos = text.find(control)
        if delpos != 0:
            DanOrange.setPlainText(text[delpos+len(control):])
            DanOrange.insertPlainText(text[:delpos-1])
        else:
            DanOrange.setPlainText(text[len(control):])

    def Shift(self):
        if self.rackStack.currentIndex() == 1:
            self.rackStack.setCurrentIndex(2 if self.stacked else 0)
        else:
            self.rackStack.setCurrentIndex(1)

class savedNote:

    def __init__(self, title, parent):
        self.display = QAction(title, parent)
        self.path = "path/to/file"

    def clicked(self, a):
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
        self.normboard = Keyboard(self.display, self.h2, False)
        kb1.setLayout(self.normboard)
        kb2 = QtWidgets.QWidget()
        self.shiftboard = Keyboard(self.display, self.h2, True)
        kb2.setLayout(self.shiftboard)
        self.h2.addWidget(kb1)
        self.h2.addWidget(kb2)

        self.setCentralWidget(self.w)
        self.display.currentChanged.connect(self.BarDisplayUpdate)
    
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

        self.nextPageButton = QAction(QIcon('resources/NewPageIconInv.png'),'Next/New page',self)
        self.nextPageButton.triggered.connect(self.NextPage)
        toolbar.addAction(self.nextPageButton)

        self.lastPageButton = QAction(QIcon('resources/InvalidLastPageIconInv.png'),'Previous page',self)
        self.lastPageButton.triggered.connect(self.LastPage)
        toolbar.addAction(self.lastPageButton)

        self.saveButton = QAction('Save',self)
        self.saveButton.triggered.connect(self.SaveNotes)
        toolbar.addAction(self.saveButton)

        self.testButton = QAction('TestDialog',self)
        self.testButton.triggered.connect(self.Dialog)
        toolbar.addAction(self.testButton)

        self.pageDisplay = QtWidgets.QLabel('1 / 1', self)#.setAlignment(Qt.AlignCenter) Trying to center it (horizontally), not working rn.
        toolbar.addWidget(self.pageDisplay)


        # Special controls heading
        # ------------------------------------------------------------------------------------- #
        self.controls_head = QtWidgets.QLabel('Controls',self)
        toolbar.addWidget(self.controls_head)
        toolbar.addSeparator()

        self.interpretButton = QAction(QIcon('resources/InterpretIconInv.png'),'Interpret',self)
        self.interpretButton.triggered.connect(self.ReadText)
        toolbar.addAction(self.interpretButton)

        self.boardSwitchButton = QAction('Swap Input', self)
        self.boardSwitchButton.triggered.connect(self.BoardSwitch)
        toolbar.addAction(self.boardSwitchButton)

        self.newLineButton = QAction('New line', self)
        self.newLineButton.triggered.connect(self.NewLine)
        toolbar.addAction(self.newLineButton)
                                       
        self.setGeometry(200,200,750,600)
        self.setWindowTitle('PiPad')
        self.show()

        

    def NewLine(self):
        current = self.display.currentIndex()
        self.pages[current].insertPlainText('\n')

    def Dialog(self):
        dlg = SelectionDialog(self)
        if dlg.exec_():
            print(self.dataSlot)
        else:
            print('Cancelled')

    def NextPage(self):
        current = self.display.currentIndex()
        nextPage = current +1
        if current != len(self.pages)-1:
            if nextPage == len(self.pages)-1:
                self.nextPageButton.setIcon(QIcon('resources/NewPageIconInv.png'))
            self.display.setCurrentIndex(nextPage)
        else:
            newPage = QTextEdit()
            self.display.addWidget(newPage)
            self.pages.append(newPage)
            self.display.setCurrentIndex(nextPage)
        self.lastPageButton.setIcon(QIcon('resources/LastPageIconInv.png'))

    def LastPage(self):
        current = self.display.currentIndex()
        if current != 0:
            self.display.setCurrentIndex(current-1)
            self.nextPageButton.setIcon(QIcon('resources/NextPageIconInv.png'))

    def BarDisplayUpdate(self):
        current = self.display.currentIndex()
        if current == 0:
            self.lastPageButton.setIcon(QIcon('resources/InvalidLastPageIconInv.png'))
        newPageDisplay = str(current+1)+' / '+str(len(self.pages))
        self.pageDisplay.setText(newPageDisplay)
        
    def ReadText(self):
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        self.canvas.image.save(buffer, "png")
        data = BytesIO(buffer.data())
        buffer.close()
        text = 'Translated'
        
##        img = Image.open(data) # PIL image format
##        thresh = 200
##        fn = lambda x : 255 if x > thresh else 0
##        img = img.convert('L').point(fn, mode='1')
##
##        colour = (255, 255, 255)
##        x_elements=[]
##        y_elements=[]
##
##        rgb_img = img.convert('RGB')
##        for x in range(rgb_img.size[0]):
##            for y in range(rgb_img.size[1]):
##                r, g, b = rgb_img.getpixel((x, y))
##                if (r,g,b) == colour:
##                    x_elements.append(x)
##                    y_elements.append(y)
##
##        x3 = min(x_elements) - 20
##        y3 = min(y_elements) - 20
##        x4 = max(x_elements) + 20
##        y4 = max(y_elements) + 20
##        crop = img.crop((x3,y3,x4,y4))
##
##        text = pytesseract.image_to_string(crop, config ='--psm 10')
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
        name = "".join(content[0].split(" ")[:2])

        with open(path + name, "w") as f:
            f.write(control.join(content))

class KeyboardDialog(QtWidgets.QDialog):
    
    def __init__(self,title,*args):
        super().__init__(*args)
        self.setWindowTitle(title)

        layout = QtWidgets.QVBoxLayout()
        self.display = QtWidgets.QTextEdit()
        layout.addWidget(self.display)
        rackBase = QtWidgets.QWidget()
        boardRack = QtWidgets.QStackedLayout()
        rackBase.setLayout(boardRack)
        kb1 = QtWidgets.QWidget()
        normboard = Keyboard(self.display,boardRack, Stacked = False)
        kb1.setLayout(normboard)
        boardRack.addWidget(kb1)
        kb2 = QtWidgets.QWidget()
        shiftboard = Keyboard(self.display,boardRack,True,False)
        kb2.setLayout(shiftboard)
        boardRack.addWidget(kb2)
        layout.addWidget(rackBase)
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.Input)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)

    def Input(self):
        self.parent().dataSlot = self.display.toPlainText()
        self.accept()

class SelectionDialog(QtWidgets.QDialog):

    def __init__(self,*args):
        super().__init__(*args)
        self.setWindowTitle('Select a file')
        self.NormalMode = True

        layout = QtWidgets.QVBoxLayout()
        toolbar = QtWidgets.QToolBar()
        layout.addWidget(toolbar)
        ModeToggle = QAction('Delete',self)
        ModeToggle.triggered.connect(self.toggleMode)
        ModeToggle.setCheckable(True)
        toolbar.addAction(ModeToggle)
        BackButton = QAction('Back',self)
        BackButton.triggered.connect(self.backFile)
        toolbar.addAction(BackButton)
        scrollBase = QtWidgets.QScrollArea()
        self.listRack = QtWidgets.QStackedLayout()
        listRackWidget = QtWidgets.QWidget()
        listRackWidget.setLayout(self.listRack)
        listBase = QtWidgets.QVBoxLayout()
        listBaseWidget = QtWidgets.QWidget()
        listBaseWidget.setLayout(listBase)
        for i in ('one','twohhhhhhhhhhhhhhhhhhhhhhhhh','three','four','five',
                  'six','seben','wyth','nuevo','thirteen'):
            listBase.addWidget(QtWidgets.QLabel(i))
        self.listRack.addWidget(listBaseWidget)
        
        scrollBase.setWidget(listRackWidget)
        
            
        layout.addWidget(scrollBase)
        self.setLayout(layout)
        self.getList()

    def getList(self, dirname=''):
        if dirname != '':
            os.chdir(os.getcwd()+'\\'+dirname)
        current = os.getcwd()
        fileList = os.listdir(current)
        (dirList, txtList) = ([],[])
        scrollBase = QtWidgets.QScrollArea()
        listBase = QtWidgets.QVBoxLayout()
        listBaseWidget = QtWidgets.QWidget()
        listBaseWidget.setLayout(listBase)
        for i in fileList:
            if os.path.isdir(current+'\\'+i):
                pass
                dirList.append(i)
            else:
                txtList.append(i)
        if len(dirList) != 0:
            listBase.addWidget(QtWidgets.QLabel('----Folders----'))
            for i in dirList:
                newButton = QtWidgets.QPushButton(i)
                newButton.clicked.connect(self.makeDirButton(i))
                newButton.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Fixed)
                listBase.addWidget(newButton)
        if len(txtList) != 0:
            listBase.addWidget(QtWidgets.QLabel('-----Files-----'))
            for i in txtList:
                newButton = QtWidgets.QPushButton(i)
                newButton.clicked.connect(self.makeFileButton(i))
                newButton.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Fixed)
                listBase.addWidget(newButton)
        scrollBase.setWidget(listBaseWidget)
        self.listRack.addWidget(scrollBase)
        self.listRack.removeWidget(self.listRack.widget(0))

    def toggleMode(self):
        if self.NormalMode:
            self.NormalMode = False
        else:
            self.NormalMode = True

    def fileFunk(self,fileName):
        if self.NormalMode:
            self.parent().dataSlot = fileName
            self.accept()
        else:
            os.remove(os.getcwd()+'\\'+fileName)
            self.getList()

    def dirFunk(self,dirName):
        if self.NormalMode:
            self.getList(dirName)
        else:
            if len(os.listdir(os.getcwd()+'\\'+dirName)) == 0:
                os.rmdir(os.getcwd()+'\\'+dirName)
                self.getList()

    def makeDirButton(self,dirName):
        return lambda: self.dirFunk(dirName)

    def makeFileButton(self,fileName):
        return lambda: self.fileFunk(fileName)

    def backFile(self):
        cwd = os.getcwd()
        os.chdir(cwd[:cwd.rfind('\\')])
        self.getList()


    
def main():
    #with open("styles.css", "r") as f:
    app = QApplication(sys.argv)
    ex = MainWindow()
        #ex.setStyleSheet(f.read())
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
