# ------------------------------------------------------------------------------------------------------------------------------------- #
# Imports and Global Variables
# ------------------------------------------------------------------------------------------------------------------------------------- #

# Useful stuff from the Python Standard Library
import sys, os, math


# PyQt5 - We haven't imported everything to keep overhead as low as possible
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QIODevice, QBuffer
from PyQt5.QtGui import QIcon, QImage, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QTextEdit, QMainWindow, QAction, QApplication, QToolBar, QSizePolicy, QSpacerItem


# Imports used for coverting handwriting to text
import pytesseract
from PIL import Image
from io import BytesIO


# Global Variables for Windows
#resourcepath = "Z:\PiPad-main\PiPad-main\\resources"
#csspath = "Z:\PiPad-main\PiPad-main\styles.css"
#path = "Z:\PiPad-main\PiPad-main\saved\\"


# Global Variables for Linux/UNIX
resourcepath = os.getcwd() + "/resources/"
csspath = os.getcwd() + "/styles.css"
path = os.getcwd() + "/saved/"


# OS independant globals
control = "~~~"
backgroundcolor = "#171717"










# ------------------------------------------------------------------------------------------------------------------------------------- #
# The Canvas
# ------------------------------------------------------------------------------------------------------------------------------------- #

# Used as the 'paper', canvas is the surface the user writes on.

class Canvas(QtWidgets.QWidget): # Inherit all the good stuff from QtWdgets
    def __init__(self, parent=None):
        super().__init__()
        self.setAttribute(Qt.WA_StaticContents)

        # Pen Attributes... Only useful if we need to change them later
        self.myPenWidth = 5
        self.myPenColor = Qt.white

        # The image to draw on and a path to add user input
        self.image = QImage(1200, 300, QImage.Format_RGB32)
        self.path = QPainterPath()

        # Reset/clear the canvas
        self.clearImage()


    # Use later for different colours if we need it
    def setPenColor(self, newColor):
        self.myPenColor = newColor


    # Ditto for widths
    def setPenWidth(self, newWidth):
        self.myPenWidth = newWidth
    

    # Erase the image after the handwriting is turned to text
    def clearImage(self):
        self.path = QPainterPath()
        self.image.fill(Qt.black)
        self.update()

    # TODO comment these 3 functions
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










# ------------------------------------------------------------------------------------------------------------------------------------- #
# The Keyboard
# ------------------------------------------------------------------------------------------------------------------------------------- #

# A custom keyboard as the device is assumed to be used without a keyboard
# Used so that the user can type comfortably if handwriting recognition isn't desired.
# Also used in dialog boxes later on

class Keyboard(QtWidgets.QGridLayout): # Inherit from QGRidLayout
    def __init__(self, display, rackStack, *args):
        super().__init__()
        self.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.keys = {}
        self.display = display
        self.rackStack = rackStack

        # Constructs the keyboard from a set of characters passed into the class instantiation function
        for rowNum, keyRow in enumerate(args):
            self.makeKeyRow(rowNum, keyRow)

        # Special keys expand to fill the bottom row.
        for num, key in enumerate(['Shift','Space','Backspace']):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.keys[key].setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.addWidget(self.keys[key], 4, 4*(num), 1, 4)

        # Special keys connected to keyboard functions, as they don't simply type a character
        self.keys['Shift'].clicked.connect(self.Shift)
        self.keys['Space'].clicked.connect((self.makeKey(' ')))
        self.keys['Backspace'].clicked.connect(self.Backspace)
        

    # Creates a generic key for the keyboard
    def makeKey(self, key):
        return lambda: self.display.currentWidget().insertPlainText(key)


    # Creates a row of keys for the keyboard that expands to fill the available space
    def makeKeyRow(self, rowNum, keyRow):
        for colNum, key in enumerate(keyRow):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.keys[key].setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.addWidget(self.keys[key], rowNum, colNum)
            if key == '&&':       #This is completely necessary
                self.keys['&&'].clicked.connect((self.makeKey('&')))
            else:
                self.keys[key].clicked.connect((self.makeKey(key)))


    # Deletes one character
    def Backspace(self):
        self.display.currentWidget().insertPlainText(control)
        text = self.display.currentWidget().toPlainText()
        delpos = text.find(control)
        if delpos != 0:
            self.display.currentWidget().setPlainText(text[delpos+1:])
            self.display.currentWidget().insertPlainText(text[:delpos-1])
        else:
            self.display.currentWidget().setPlainText(text[1:])

    # Switches the current keyboard to a shifted keyboard (plus other funky characters)
    def Shift(self):
        if self.rackStack.currentIndex() == 1:
            self.rackStack.setCurrentIndex(2)
        else:
            self.rackStack.setCurrentIndex(1)










# ------------------------------------------------------------------------------------------------------------------------------------- #
# A Saved Note button
# ------------------------------------------------------------------------------------------------------------------------------------- #

# Used to quickly load a recently used note
# Appears as a single button, no dialog box needed

class savedNote:
    def __init__(self, title, parent):
        self.parent = parent # Parent used later to replace the text in the Main Window
        self.display = QAction(title.split(".")[0], parent) # The button itself is a QAction
        self.path = path + title # Location the file is saved at - default is a directory called saved
    

    # Delete the QAction if the button isn't needed any more (e.g. replaced by a more recent Saved Note button)
    def delete(self):
        self.display.deleteLater()


    # Runs when the QAction is clicked
    def clicked(self, a):
        with open(self.path, "r") as f:
            for i, c in enumerate(f.read().split(control)): # Loop used for page control
                self.parent.pages[i].setPlainText(c)










# ------------------------------------------------------------------------------------------------------------------------------------- #
# The Main Window
# ------------------------------------------------------------------------------------------------------------------------------------- #

# The actual UI is constructed here (e.g. toolbar, text editor)
# Houses most of the functions used for saving/loading and handwriting conversion

class MainWindow(QtWidgets.QMainWindow): # Inherits goodies from QMainWIndow
    def __init__(self):
        super().__init__()

        # Important pieces of the UI
        self.pages = [QTextEdit()] # Classic digital text editor
        self.toolbar = QToolBar() # Toolbar for various buttons
        self.toolbar.setStyleSheet("background-color: " + backgroundcolor) # TODO Toolbar styling doesn't work via styles.css???
        self.canvas = Canvas() # Canvas for drawing/writing

        # Builds the toolbar
        self.initUI()
        
        # Containers used for constructing the layout of the UI
        self.w = QtWidgets.QWidget()
        self.h = QtWidgets.QVBoxLayout()
        self.w.setLayout(self.h)
        self.display = QtWidgets.QStackedLayout()
        self.h.addLayout(self.display)
        self.display.addWidget(self.pages[0])
        self.h2 = QtWidgets.QStackedLayout()
        self.h.addLayout(self.h2)
        self.h2.addWidget(self.canvas)
        
        # Builds a keyboard from the keyboard class
        kb1 = QtWidgets.QWidget()
        self.normboard = Keyboard(self.display, self.h2,
                                  '1234567890-=',
                                  'qwertyuiop[]',
                                  "asdfghjkl;'#",
                                  '\zxcvbnm,./`')
        kb1.setLayout(self.normboard)
        self.h2.addWidget(kb1)

        # Builds a shifted keyboard from the keyboard class
        kb2 = QtWidgets.QWidget()
        self.shiftboard = Keyboard(self.display, self.h2,
                                   ['!','"','£','$','%','^','&&','*','(',')','_','+'],
                                   'QWERTYUIOP{}',
                                   'ASDFGHJKL:@~',
                                   '|ZXCVBNM<>?¬')
        kb2.setLayout(self.shiftboard)
        self.h2.addWidget(kb2)

        # TODO Someone else please comment these I have no clue what these do lol
        self.setCentralWidget(self.w)
        self.display.currentChanged.connect(self.BarDisplayUpdate)
        

    # Scans the save directory for recent notes and adds them to the toolbar
    def addNotes(self):
        all_saved = []
        self.saved_note_buttons = []

        # List all files in /saved/
        for f in os.listdir(path):
            all_saved.append(f)

        # Takes the first 5 notes and makes Saved Note Buttons with them
        for i in all_saved[:5]:
            self.saved_note_buttons.append(savedNote(i, self)) # Keeps track of the notes buttons by putting them in a list
            self.saved_note_buttons[::-1][0].display.triggered.connect(self.saved_note_buttons[::-1][0].clicked) # When button clicked, trigger the objects clicked function
            self.toolbar.addAction(self.saved_note_buttons[::-1][0].display) # Add the button to the toolbar
    

    # Builds the toolbar!
    def initUI(self):
        self.toolbar.setMovable(False) # Stop the toolbar being dragged around, everything breaks if you do that
        self.addToolBar(Qt.LeftToolBarArea,self.toolbar) # Adds the toolbar to the main UI





        # Controls for pages
        self.pages_head = QtWidgets.QLabel('Pages',self)
        self.pages_head.setAlignment(Qt.AlignCenter) # Centers the text... hallelujah!
        self.toolbar.addWidget(self.pages_head) # Adds to the toolbar

        # Button takes you to the next page (or creates a new one)
        self.nextPageButton = QAction(QIcon(resourcepath+ '/NewPageIconInv.png'),'Next/New page',self)
        self.nextPageButton.triggered.connect(self.NextPage)
        self.toolbar.addAction(self.nextPageButton)

        # Button takes you to the last page
        self.lastPageButton = QAction(QIcon(resourcepath+'/InvalidLastPageIconInv.png'),'Previous page',self)
        self.lastPageButton.triggered.connect(self.LastPage)
        self.toolbar.addAction(self.lastPageButton)

        # Displays how many pages there are and which one you're on
        self.pageDisplay = QtWidgets.QLabel('1 / 1', self)
        self.pageDisplay.setAlignment(Qt.AlignCenter)
        self.pageDisplay.setStyleSheet("font-size: 10px;")
        self.toolbar.addWidget(self.pageDisplay)





        # Special controls label
        self.controls_head = QtWidgets.QLabel('Controls',self)
        self.controls_head.setAlignment(Qt.AlignCenter)
        self.controls_head.setStyleSheet("padding-top: 50px;") # Creates a spacer between pages and special controls
        self.toolbar.addWidget(self.controls_head)

        # Button triggers handwriting to text function
        self.interpretButton = QAction(QIcon(resourcepath+'/InterpretIconInv.png'),'Interpret',self)
        self.interpretButton.triggered.connect(self.ReadText)
        self.toolbar.addAction(self.interpretButton)

        # Swaps from handwriting input to keyboard
        self.boardSwitchButton = QAction('Swap Input', self)
        self.boardSwitchButton.triggered.connect(self.BoardSwitch)
        self.toolbar.addAction(self.boardSwitchButton)

        # Newline charcter, as newlines can't be made from the handwriting input
        self.newLineButton = QAction('New line', self)
        self.newLineButton.triggered.connect(self.NewLine)
        self.toolbar.addAction(self.newLineButton)

        # Button to save the current note 
        self.saveButton = QAction('Save',self)
        self.saveButton.triggered.connect(self.SaveNotes)
        self.toolbar.addAction(self.saveButton)





        # Saved Notes heading
        self.notes_heading = QtWidgets.QLabel('Recent Notes',self)
        self.notes_heading.setAlignment(Qt.AlignCenter)
        self.notes_heading.setStyleSheet("padding-top: 50px") # Creates a spacer between special controls and saved notes
        self.toolbar.addWidget(self.notes_heading)
        
        # Adds all the note buttons to the bottom of the toolbar
        self.addNotes()



        # UI Initilisation
        self.setGeometry(50,50,1200,620) # Set window size for Windows/MacOS
        #self.setGeometry(0,0,800,480) # Set window size for the Pi & touchscreen display
        self.setWindowTitle('PiPad') # Window title to look professional
        self.show() # Reveal the UI

        
    # Inserts a newline
    def NewLine(self):
        current = self.display.currentIndex()
        self.pages[current].insertPlainText('\n')


    # Takes the user to the next page or creates one
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


    # Takes the user to the last page
    def LastPage(self):
        current = self.display.currentIndex()
        if current != 0:
            self.display.setCurrentIndex(current-1)
            self.nextPageButton.setIcon(QIcon(resourcepath+'/NextPageIconInv.png'))


    # Updates the label that shows how many pages you have and what page you are on
    def BarDisplayUpdate(self):
        current = self.display.currentIndex()
        if current == 0:
            self.lastPageButton.setIcon(QIcon(resourcepath+'/InvalidLastPageIconInv.png'))
        newPageDisplay = str(current+1)+' / '+str(len(self.pages))
        self.pageDisplay.setText(newPageDisplay)

    
    # The handwriting to text function
    def ReadText(self):
        # Dark magic is required to convert the Canvas path into png format
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        self.canvas.image.save(buffer, "png")
        data = BytesIO(buffer.data())
        buffer.close()
        
        img = Image.open(data) # Make a PIL image object from the png data
        thresh = 200
        fn = lambda x : 255 if x > thresh else 0
        img = img.convert('L').point(fn, mode='1') # Turns the image back and white (better for tesseract)

        # Code that crops the image so that the text fills the picture (also better for tesseract)
        colour = (255, 255, 255) # (white)
        x_elements=[]
        y_elements=[]

        rgb_img = img.convert('RGB')
        for x in range(rgb_img.size[0]):
            for y in range(rgb_img.size[1]):
                r, g, b = rgb_img.getpixel((x, y))
                if (r,g,b) == colour:
                    x_elements.append(x)
                    y_elements.append(y)

        # +/-20px gives a nice border round the text
        x3 = min(x_elements) - 20
        y3 = min(y_elements) - 20
        x4 = max(x_elements) + 20
        y4 = max(y_elements) + 20
        crop = img.crop((x3,y3,x4,y4))

        # pytessesract calls tesseceract through the commandine
        text = pytesseract.image_to_string(crop, config ='--psm 10') # TODO config is important so tweak for best performance
        text = text.replace(control, "") # If the control character appears, get rid of it! It will mess up saving/backspace

        # Add the text to the text editor and reset the canvas
        self.pages[self.display.currentIndex()].insertPlainText(text.strip())
        self.canvas.clearImage()


    # Switch the keyboard and handwriting inputs when nessassary
    def BoardSwitch(self):
        if self.h2.currentIndex() == 0:
            self.h2.setCurrentIndex(1)
        else:
            self.h2.setCurrentIndex(0)
            

    # Save the note currently being edited
    def SaveNotes(self, a):
        content = [i.toPlainText() for i in self.pages]
        name = " ".join(content[0].replace("\n", " ").split(" ")[:2]) + ".txt" # Make a name from the first 2 words on the first page
        # TODO Replace name with a dialog box for proper saving

        # Actually write to the file
        with open(path + name, "a") as f:
            f.write(control.join(content))
        
        # Update notes by deleting them and re-adding them, forces a rescan of /saved/
        for note in self.saved_note_buttons:
            note.delete()
        self.addNotes()










# ------------------------------------------------------------------------------------------------------------------------------------- #
# The Entry Point
# ------------------------------------------------------------------------------------------------------------------------------------- #

# The code starts down here in the main function

def main():
    with open(csspath, "r") as f:
        app = QApplication(sys.argv) # Create a QApplication
        ex = MainWindow() # Create an instance of the UI
        ex.setStyleSheet(f.read()) # Sets styles.css as the cascading style sheet for the UI
        sys.exit(app.exec_()) # Exit the program if the app dies

# Code won't start if imported as a library... good I guess?
if __name__ == '__main__':
    main()
