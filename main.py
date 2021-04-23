  
# ------------------------------------------------------------------------------------------------------------------------------------- #
# Imports and Global Variables
# ------------------------------------------------------------------------------------------------------------------------------------- #

# Useful stuff from the Python Standard Library
import sys, os, math, time, csv


# PyQt5 - We haven't imported everything to keep overhead as low as possible
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QIODevice, QBuffer
from PyQt5.QtGui import QIcon, QImage, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QTextEdit, QMainWindow, QAction, QApplication, QToolBar, QSizePolicy, QSpacerItem


# Imports used for coverting handwriting to text
import pytesseract
from PIL import Image
from io import BytesIO
import PIL.ImageOps

# Global Variables for Windows
#resourcepath = "Z:\PiPad-main\PiPad-main\\resources"
#csspath = "Z:\PiPad-main\PiPad-main\styles.css"
#path = "Z:\PiPad-main\PiPad-main\saved\\"


# Global Variables for Linux/UNIX
resources = home + '/resources/'
csspath = os.getcwd() + "/styles.css"
path = os.getcwd() + "/saved/"


# OS independant globals
control = "¦p"
backgroundcolor = "#171717"
home = os.getcwd()
currentDocument = ('Untitled',os.getcwd())









# ------------------------------------------------------------------------------------------------------------------------------------- #
# The Canvas
# ------------------------------------------------------------------------------------------------------------------------------------- #

# Used as the 'paper', canvas is the surface the user writes on.

class Canvas(QtWidgets.QWidget): # Inherit all the good stuff from QtWdgets
    '''A surface for the user to write on'''
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


    def setPenColor(self, newColor):
        '''Use later for different colours if we need it'''
        self.myPenColor = newColor


    def setPenWidth(self, newWidth):
        '''Use later for different widths if we need it'''
        self.myPenWidth = newWidth
    

    def clearImage(self):
        '''Erase the image after the handwriting is turned to text'''
        self.path = QPainterPath()
        self.image.fill(Qt.black)
        self.update()

    # TODO comment this function
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(event.rect(), self.image, self.rect())
        

    def mousePressEvent(self, event):
        '''Overwrites an existing method to prepare to draw when mouse clicked'''
        self.path.moveTo(event.pos())


    def mouseMoveEvent(self, event):
        '''Overwrites a pre-existing method to draw when mouse dragged'''
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

class Keyboard(QtWidgets.QGridLayout):
    '''A custom widget to facillitate touchscreen typing'''
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

        # Constructs the keyboard from a set of characters passed into the class instantiation function
        for rowNum, keyRow in enumerate(KeysToAdd):
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
        

    def makeKey(self, key):
        '''Generates the generic function for a key, using conservation of local scope'''
        if self.stacked:
            return lambda: self.display.currentWidget().insertPlainText(key)
        else:
            return lambda: self.display.insertPlainText(key)

 
    def makeKeyRow(self, rowNum, keyRow):
        '''Creates a row of keys for the keyboard that expands to fill the available space'''
        for colNum, key in enumerate(keyRow):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.keys[key].setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.addWidget(self.keys[key], rowNum, colNum)
            #Due to the working of PyQt5, the first '&' in a button's name disappears.
            if key == '&&':       
                self.keys['&&'].clicked.connect((self.makeKey('&')))
            else:
                self.keys[key].clicked.connect((self.makeKey(key)))


    def Backspace(self):
        '''Deletes one character'''
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
        '''Switches the current keyboard to a shifted keyboard (plus other funky characters)'''
        if self.rackStack.currentIndex() == 1:
            self.rackStack.setCurrentIndex(2 if self.stacked else 0)
        else:
            self.rackStack.setCurrentIndex(1)


# ------------------------------------------------------------------------------------------------------------------------------------- #
# The Main Window
# ------------------------------------------------------------------------------------------------------------------------------------- #

# The actual UI is constructed here (e.g. toolbar, text editor)
# Houses most of the functions used for saving/loading and handwriting conversion

class MainWindow(QtWidgets.QMainWindow): # Inherits goodies from QMainWIndow
    '''The main window. It houses all the GUI'''
    def __init__(self):
        super().__init__()

        # Important pieces of the UI
        self.pages = [QTextEdit()] # List of all pages of the loaded file
        self.saveNoteButtons = [] # List of all SaveNote buttons
        self.recentFileNames = [] #List of all files with an active SaveNote button
        self.toolbar = QToolBar() # Toolbar for various buttons
        #self.toolbar.setStyleSheet("background-color: " + backgroundcolor) # TODO Toolbar styling doesn't work via styles.css???
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
        self.normboard = Keyboard(self.display, self.h2, False)
        kb1.setLayout(self.normboard)
        self.h2.addWidget(kb1)

        # Builds a shifted keyboard from the keyboard class
        kb2 = QtWidgets.QWidget()
        self.shiftboard = Keyboard(self.display, self.h2, True)
        kb2.setLayout(self.shiftboard)
        self.h2.addWidget(kb2)

        # Assigns the layout to the main window
        self.setCentralWidget(self.w)
        self.display.currentChanged.connect(self.BarDisplayUpdate)
        self.BarDisplayUpdate()
        

    def addNotes(self):
        '''Scans the save directory for recent notes and adds them to the toolbar'''
        # Get list of recent files
        global resources
        os.chdir(resources)
        with open('FileList.csv','r') as file:
            data = [line for line in csv.reader(file)]

        # Clean up list to make it usable (and skip to end if no files listed
        if data != []:
            while [] in data:
                data.remove([])

        # Makes Saved Note Buttons with the listed files
            for num, file in enumerate(data):
                self.recentFileNames.append(file[0]+'.txt')
                self.saveNoteButtons.append(QtWidgets.QAction(file[0],self)) # Keeps track of the notes buttons by putting them in a list
                self.saveNoteButtons[num].triggered.connect(self.makeSaveNote(file,self)) # When button clicked, trigger the desired function
                self.toolbar.addAction(self.saveNoteButtons[num]) # Add the button to the toolbar

    def deleteNotes(self):
        '''Removes all current SaveNote buttons to prepare for new ones.'''
        for i in range(len(self.saveNoteButtons)):
            self.saveNoteButtons.pop(0).deleteLater()
    
 
    def initUI(self):
        '''Builds the toolbar!'''
        self.toolbar.setMovable(False) # Stop the toolbar being dragged around, everything breaks if you do that
        self.addToolBar(Qt.LeftToolBarArea,self.toolbar) # Adds the toolbar to the main UI

        # Move to correct location for accessing icons
        global resources
        os.chdir(resources)

        # Controls for pages
        self.pages_head = QtWidgets.QLabel('Pages',self)
        self.pages_head.setAlignment(Qt.AlignCenter) # Centers the text... hallelujah!
        self.toolbar.addWidget(self.pages_head) # Adds to the toolbar

        # Button takes you to the next page (or creates a new one)
        self.nextPageButton = QAction(QIcon('NewPageIcon.png'),'Next/New page',self)
        self.nextPageButton.triggered.connect(self.NextPage)
        self.toolbar.addAction(self.nextPageButton)

        # Button takes you to the last page
        self.lastPageButton = QAction(QIcon('LastPageIconInv.png'),'Previous page',self)
        self.lastPageButton.triggered.connect(self.LastPage)
        self.toolbar.addAction(self.lastPageButton)

        # Button deletes current page
        self.deletePageButton = QAction(QIcon('DeletePageIcon.png'),'Delete Page',self)
        self.deletePageButton.triggered.connect(self.DeletePage)
        self.toolbar.addAction(self.deletePageButton)

        # Displays how many pages there are and which one you're on
        self.pageDisplay = QtWidgets.QLabel('1 / 1', self)
        self.pageDisplay.setAlignment(Qt.AlignCenter)
        self.pageDisplay.setStyleSheet("font-size: 8px;")
        self.toolbar.addWidget(self.pageDisplay)





        # Special controls label
        self.controls_head = QtWidgets.QLabel('Controls',self)
        self.controls_head.setAlignment(Qt.AlignCenter)
        self.controls_head.setStyleSheet("padding-top: 30px;") # Creates a spacer between pages and special controls
        self.toolbar.addWidget(self.controls_head)

        # Button triggers handwriting to text function
        self.interpretButton = QAction(QIcon('InterpretIcon.png'),'Interpret',self)
        self.interpretButton.triggered.connect(self.ReadText)
        self.toolbar.addAction(self.interpretButton)

        # Swaps from handwriting input to keyboard
        self.boardSwitchButton = QAction(QIcon('SwapInputIcon.png'),'Swap Input', self)
        self.boardSwitchButton.triggered.connect(self.BoardSwitch)
        self.toolbar.addAction(self.boardSwitchButton)

        # Newline charcter, as newlines can't be made from the handwriting input
        self.newLineButton = QAction(QIcon('NewLineIcon.png'),'New line', self)
        self.newLineButton.triggered.connect(self.NewLine)
        self.toolbar.addAction(self.newLineButton)





        # Saved Notes heading
        self.notes_heading = QtWidgets.QLabel('Notes',self)
        self.notes_heading.setAlignment(Qt.AlignCenter)
        self.notes_heading.setStyleSheet("padding-top: 30px") # Creates a spacer between special controls and saved notes
        self.toolbar.addWidget(self.notes_heading)

        # Button saves current document
        self.saveButton = QAction(QIcon('SaveIcon.png'),'Save',self)
        self.saveButton.triggered.connect(self.SaveNotes)
        self.toolbar.addAction(self.saveButton)

        # Button saves current document with entered location and name
        self.saveAsButton = QAction(QIcon('SaveAsIcon.png'),'Save As',self)
        self.saveAsButton.triggered.connect(self.SaveNotesAs)
        self.toolbar.addAction(self.saveAsButton)

        # Opens file browser
        self.loadButton = QAction(QIcon('BrowseFilesIcon.png'),'Browse Files', self)
        self.loadButton.triggered.connect(self.LoadNotes)
        self.toolbar.addAction(self.loadButton)
        
        # Adds all the note buttons to the bottom of the toolbar
        self.addNotes()



        # UI Initilisation
        self.setGeometry(50,50,1200,620) # Set window size for Windows/MacOS
        self.setGeometry(0,0,800,480) # Set window size for the Pi & touchscreen display
        self.setWindowTitle('PiPad- '+currentDocument[0])# Window title to look professional
        self.show() # Reveal the UI

        
    def NewLine(self):
        '''Inserts a newline'''
        current = self.display.currentIndex()
        self.pages[current].insertPlainText('\n')


#-------------Page Manipulation Functions-------------------------------------------------

    def NextPage(self):
        '''Takes the user to the next page or creates one'''
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
        '''Takes the user to the last page'''
        current = self.display.currentIndex()
        if current != 0:
            self.display.setCurrentIndex(current-1)
        self.BarDisplayUpdate()


    def DeletePage(self):
        '''Deletes current page, and returns to the page before it'''
        doomedPageNumber = self.display.currentIndex()
        if doomedPageNumber == 0:
            self.NextPage()
        else:
            self.LastPage()
        self.display.removeWidget(self.pages[doomedPageNumber])
        self.pages = self.pages[1:] if doomedPageNumber==0 else self.pages[:doomedPageNumber]+self.pages[doomedPageNumber+1:]
        self.BarDisplayUpdate()


    def BarDisplayUpdate(self):
        '''Updates the label that shows how many pages you have and what page you are on'''
        current = self.display.currentIndex()+1
        total = self.display.count()
        global resources
        os.chdir(resources)
        
        # Updates Last Page Button if on or not on first page
        if current == 1:
            self.lastPageButton.setIcon(QIcon('LastPageIconInv.png'))
        else:
            self.lastPageButton.setIcon(QIcon('LastPageIcon.png'))
            
        # Changes between next and new page icons depending on if at last page
        if current == total:
            self.nextPageButton.setIcon(QIcon('NewPageIcon.png'))
        else:
            self.nextPageButton.setIcon(QIcon('NextPageIcon.png'))

        # Updates the page number display
        newPageDisplay = str(current)+' / '+str(total)
        self.pageDisplay.setText(newPageDisplay)

#-------------Input Functions-------------------------------------------------------------
    
    def ReadText(self):
        '''The handwriting to text function'''
        # Dark magic is required to convert the Canvas path into png format
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        self.canvas.image.save(buffer, "png")
        data = BytesIO(buffer.data())
        buffer.close()
        
        img = Image.open(data) # Make a PIL image object from the png data
        img = PIL.ImageOps.invert(img)
        thresh = 200
        fn = lambda x : 255 if x > thresh else 0
        img = img.convert('L').point(fn, mode='1') # Turns the image black and white (better for tesseract)

        # Code that crops the image so that the text fills the picture (also better for tesseract)
        colour = (0, 0, 0) # (black)
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
        text = text.replace(control, "") # If the control character appears, get rid of them! It will mess up saving/backspace

        # Add the text to the text editor and reset the canvas
        self.pages[self.display.currentIndex()].insertPlainText(text.strip())
        self.canvas.clearImage()


    def BoardSwitch(self):
        '''Switches the keyboard and handwriting inputs when nessassary'''
        if self.h2.currentIndex() == 0:
            self.h2.setCurrentIndex(1)
        else:
            self.h2.setCurrentIndex(0)

#-------------Save / Load Functions-------------------------------------------------------            

    def SaveNotesAs(self):
        '''Save open note under chosen name in chosen location'''
        # Declare currentDocument as global
        global currentDocument

        # Get the user to choose where to save the file
        dlg = SelectionDialog(self,False)
        if dlg.exec_():

            # Get the name of the file
            dlg2 = KeyboardDialog(self,'Name the document',currentDocument[0])
            if dlg2.exec_():
                name = self.dataSlot
                fname = name+'.txt'

                # Check if overwriting is necessary and appropriate
                if fname in os.listdir(os.getcwd()):
                    dlg3 = ConfirmationDialog(self,name+' already exists. Overwrite it?')
                    if dlg3.exec_():

                # Update currentDocument to reflect user choices, then regular save
                        currentDocument = (name,os.getcwd())
                        self.setWindowTitle('PiPad- '+currentDocument[0])
                        self.SaveNotes()
                else:
                    currentDocument = (name,os.getcwd())
                    self.setWindowTitle('PiPad- '+currentDocument[0])
                    self.SaveNotes()
                

    def SaveNotes(self):
        '''Save the current document'''
        global resources
        
        # Get file content
        content = [i.toPlainText() for i in self.pages]

        # Write to the file
        os.chdir(currentDocument[1])
        with open(currentDocument[0] + '.txt', "w") as f:
            f.write(control.join(content))

        # Read the recent file list
        os.chdir(resources)
        with open('FileList.csv','r') as file:
            oldList = [line for line in csv.reader(file)]
        if oldList != []:
            while [] in oldList:
                oldList.remove([])
            if [currentDocument[0],currentDocument[1]] in oldList:
                oldList.remove([currentDocument[0],currentDocument[1]])

        # Update the recent file list.
        oldList.insert(0,[currentDocument[0],currentDocument[1]])
        if len(oldList) > 5:
            oldList = oldList[:5]
        with open('FileList.csv','w') as file:
            csv.writer(file).writerows(oldList)

        # Update the SaveNote buttons
        self.deleteNotes()
        self.addNotes()
        #CONFUSION! It adds notes, displays the dialogue then removes notes?
        #Functional, but weird.
                 
        # Tell user the file has been saved.
        dlg = ConfirmationDialog(self,currentDocument[0]+' has been saved.','Success!',False)
        if dlg.exec_():
            pass

    def LoadNotes(self, fileName=False):
        '''The user selects a file, which is then loaded
If fileName is not False, selection is skipped and the given file is loaded'''
        global currentDocument
        # Get file's name, and navigate to it
        if fileName: # Used by the SaveNote Buttons to skip dialogue use
            os.chdir(fileName[1])
            fileName = fileName[0]+'.txt'
        else: # Used by Browse Files
            dlg = SelectionDialog(self)
            if dlg.exec_():
                fileName = self.dataSlot

        # Read file
        if fileName: # Ends function if no file has been selected
            with open(fileName, 'r') as file:
                contents = (file.read()).split(control)

            # Make QTextEdits for each page
            newpages = [QTextEdit() for page in contents]
            for pageNum, pageText in enumerate(contents):
                newpages[pageNum].setPlainText(pageText)

            # Replace current document
            self.pages.append(newpages[0])                  #Set up page 1 (for visuals)
            self.display.addWidget(newpages[0])             #
            self.display.setCurrentWidget(newpages.pop(0))  #
            for i in range(1,len(self.pages)):                #Remove previous pages
                self.display.removeWidget(self.pages.pop(0))  #
            if len(newpages) >= 1:                    #Add the rest of the new pages
                for page in newpages:                 #
                    self.pages.append(page)           #
                    self.display.addWidget(page)      #
            currentDocument = (fileName[:-4], os.getcwd())
            self.BarDisplayUpdate()                  #And fix the displays
            self.setWindowTitle('PiPad- '+fileName[:-4])  #

    def makeSaveNote(self, file, parent):
        '''makes a function for a SaveNote button.
Works similarly to Keyboard's makeKey'''
        return lambda: parent.LoadNotes(file)



# ------------------------------------------------------------------------------------------------------------------------------------- #
# Confirmation Dialog
# ------------------------------------------------------------------------------------------------------------------------------------- #

# Displays a text prompt to user, and asks for confirmation that they are aware.
# Sometimes allows cancellation of prompting action

class ConfirmationDialog(QtWidgets.QDialog):
    '''A dialogue that conveys a simple message to elicit a yes/no response from the user.
Normally used for cautions, but if cancellable is False, can be used as a notification.'''

    def __init__(self,parent,message,title='Caution!',cancellable=True):
        super().__init__(parent)
        self.setWindowTitle(title)

        # Assembling the layout
        layout = QtWidgets.QVBoxLayout()
        # Message Display
        label = QtWidgets.QLabel(message)
        layout.addWidget(label)
        # Ok and Cancel buttons. Care is taken to only add Cancel if desired.
        shortcut = QtWidgets.QDialogButtonBox #Seriously reduces length of next line
        buttonBox = QtWidgets.QDialogButtonBox(shortcut.Cancel|shortcut.Ok if cancellable else shortcut.Ok)
        buttonBox.accepted.connect(self.accept)
        if cancellable:
            buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)


# ------------------------------------------------------------------------------------------------------------------------------------- #
# Keyboard Dialog
# ------------------------------------------------------------------------------------------------------------------------------------- #

# Displays a keyboard and entry field, to allow for the user to enter text on a touchscreen
#TODO: Can Dan change size of QTextEdit to make it one line? QLineEdit not compatable with Keyboard.

class KeyboardDialog(QtWidgets.QDialog):
    '''A dialogue that allows the entry of text'''
    
    def __init__(self,parent,title,default):
        super().__init__(parent)
        self.setWindowTitle(title)

        # Assembling the layout
        layout = QtWidgets.QVBoxLayout()
        # Entry field
        self.display = QtWidgets.QTextEdit()
        self.display.setPlaceholderText(default)
        layout.addWidget(self.display)
        # Keyboard, with QStackedWidget to allow shift
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
        # Ok and Cancel buttons
        shortcut = QtWidgets.QDialogButtonBox #Without this, next line ets far too long
        buttonBox = QtWidgets.QDialogButtonBox(shortcut.Cancel|shortcut.Ok)
        buttonBox.accepted.connect(self.Input)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)

    def Input(self):
        '''Sends data and closes dialogue'''
        text = self.display.toPlainText()
        self.parent().dataSlot = text if text else self.display.placeholderText()
        self.accept() #Inherited, not defined here










# ------------------------------------------------------------------------------------------------------------------------------------- #
# Selection Dialog
# ------------------------------------------------------------------------------------------------------------------------------------- #

# Provides a GUI for navigating the file system.
# Allows for loading and basic file manipulation

class SelectionDialog(QtWidgets.QDialog):
    '''A dialogue that allows file browsing.
SelectFile determines whether desired user input is a file or location
If SelectFile is false (target is a location), files cannot be opened.'''

    def __init__(self,parent,SelectFile = True):
        super().__init__(parent)
        self.setWindowTitle('Select a file' if SelectFile else 'Select a location')
        os.chdir(resources) #For icons
        self.NormalMode = True #Whether buttons delete or open 
        self.FileSelectMode = SelectFile #Whether the aim is to select a file or location

        #--Assembling the layout---------------------------------------
        layout = QtWidgets.QVBoxLayout()
        
        # Toolbar
        toolbar = QtWidgets.QToolBar()
        layout.addWidget(toolbar)
        # Button to toggle between delete and open modes
        ModeToggle = QAction(QIcon('DeleteIcon.png'),'Delete',self)
        ModeToggle.triggered.connect(self.toggleMode)
        ModeToggle.setCheckable(True)
        toolbar.addAction(ModeToggle)
        # Button to move back one directory ('cd ..' on linux). Self used to allow updating of icon
        self.BackButton = QAction(QIcon('BackIcon.png'),'Back',self)
        self.BackButton.triggered.connect(self.backFile)
        toolbar.addAction(self.BackButton)
        # Button to make a new folder
        NewFolderButton = QAction(QIcon('NewFolderIcon.png'),'New Folder',self)
        NewFolderButton.triggered.connect(self.newDir)
        toolbar.addAction(NewFolderButton)
        # Button to make a new file (loaded automatically in the main editor)
        NewFileButton = QAction(QIcon('NewFileIcon.png'),'NewFileIcon.png',self)
        NewFileButton.triggered.connect(self.newFile)
        toolbar.addAction(NewFileButton)
        
        # An area with scroll, for displaying the files
        scrollBase = QtWidgets.QScrollArea()
        # QStackedLayout allows for updating of the list- a new list is stacked on top, then the old deleted
        self.listRack = QtWidgets.QStackedLayout()
        listRackWidget = QtWidgets.QWidget()
        listRackWidget.setLayout(self.listRack)
        # The base for the file list, to go in the scroll area
        listBase = QtWidgets.QVBoxLayout()
        listBaseWidget = QtWidgets.QWidget()
        listBaseWidget.setLayout(listBase)
        for i in ('-','----VERY-LONG-PLACEHOLDER----','This','makes','the',
                  'window','the','right','size'):
            listBase.addWidget(QtWidgets.QLabel(i))
        self.listRack.addWidget(listBaseWidget)
        # Adding the list to scroll area, and scroll area to main layout
        scrollBase.setWidget(listRackWidget)
        layout.addWidget(scrollBase)

        # Adding the Ok and Cancel buttons- only adds Ok if requesting a location
        shortcut = QtWidgets.QDialogButtonBox #Makes next line drastically shorter
        buttonBox = QtWidgets.QDialogButtonBox(shortcut.Cancel if self.FileSelectMode else shortcut.Cancel|shortcut.Ok)
        buttonBox.rejected.connect(self.reject)
        if not self.FileSelectMode:
            buttonBox.accepted.connect(self.sendLocation)
        layout.addWidget(buttonBox)

        self.setLayout(layout)
        #--Finished assembling layout----------------------------------

        # Moves to and displays the start of the file system
        os.chdir(home)
        self.getList()

    def getList(self, dirname=''):
        '''Updates the lst of files and folders
Setting dirname means the function changes directory before listing'''
        
        # Move directory if required
        if dirname != '':
            os.chdir(os.getcwd()+'\\'+dirname)

        # Useful variables to prevent constant use of os get functions (time saving?)
        current = os.getcwd()
        fileList = os.listdir(current)

        # Hides the PiPad resources file. User cannot input ¦, so no issue with inputted file names.
        if 'Resources¦' in fileList:
            fileList.remove('Resources¦')

        # Prepares to sort contents of CWD
        (dirList, txtList) = ([],[])
        scrollBase = QtWidgets.QScrollArea()
        listBase = QtWidgets.QVBoxLayout()
        listBaseWidget = QtWidgets.QWidget()
        listBaseWidget.setLayout(listBase)

        # Splits directory contents into txt files and directories
        for i in fileList:
            if os.path.isdir(current+'\\'+i):
                pass
                dirList.append(i)
            else:
                txtList.append(i)

        # Lists directories if any are present
        if len(dirList) != 0:
            listBase.addWidget(QtWidgets.QLabel('----Folders----'))
            for i in dirList:
                # Makes a QPushButton to interact with corresponding directory
                newButton = QtWidgets.QPushButton(i)
                newButton.clicked.connect(self.makeDirButton(i))
                newButton.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Fixed)
                listBase.addWidget(newButton)

        # Lists txt files if any are present
        if len(txtList) != 0:
            listBase.addWidget(QtWidgets.QLabel('-----Files-----'))
            for i in txtList:
                # Makes a QPushButton to interact with corresponding file
                newButton = QtWidgets.QPushButton(i)
                newButton.clicked.connect(self.makeFileButton(i))
                newButton.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Fixed)
                listBase.addWidget(newButton)

        # Updates GUI
        scrollBase.setWidget(listBaseWidget)
        self.listRack.addWidget(scrollBase)
        self.listRack.removeWidget(self.listRack.widget(0))
        self.BackIconUpdate()

    def toggleMode(self):
        '''Changes file browser between delete and open modes'''
        if self.NormalMode:
            self.NormalMode = False
        else:
            self.NormalMode = True

    def fileFunk(self,fileName):
        '''Functions to be run when a fle is clicked on'''
        # Returns file for loading, closing file browser
        if self.NormalMode and self.FileSelectMode:
            self.parent().dataSlot = fileName
            self.accept()

        # Deletes file
        elif not self.NormalMode:
            # Checks if user really wants to delete file
            dlg = ConfirmationDialog(self,f'Do you really want to delete {fileName}?')
            if dlg.exec_():
                
                returnAddress = os.getcwd()

                # Checks if deleted file has an active SaveNote button, and removes it
                if fileName in self.parent().recentFileNames:
                    # Read the recent file list
                    global resources
                    os.chdir(resources)
                    with open('FileList.csv','r') as file:
                        oldList = [line for line in csv.reader(file)]
                    if oldList != []:
                        while [] in oldList:
                            oldList.remove([])
                            
                    # Remove the deleted file from the list
                    oldList.remove([fileName[:-4],returnAddress])
                    with open('FileList.csv','w') as file:
                        csv.writer(file).writerows(oldList)

                    # Update the button display
                    self.parent().deleteNotes()
                    self.parent().addNotes()

                    os.chdir(returnAddress)

                # Deletes the file, and updates GUI        
                os.remove(returnAddress+'\\'+fileName)
                self.getList()

        # QPushButton does nothing if interacted with normally when selecting a location
        else:
            pass

    def dirFunk(self,dirName):
        '''Functions to be run when a directory is clicked on'''
        # Moves into directory, updates GUI
        if self.NormalMode:
            self.getList(dirName)

        # Deletes directory if empty
        else:
            if len(os.listdir(os.getcwd()+'\\'+dirName)) == 0: #rmdir fails if dir not empty
                # Checks if user is sure
                dlg = ConfirmationDialog(self,f'Do you really want to delete {dirName}?')
                if dlg.exec_():
                    # Deletes directory
                    os.rmdir(os.getcwd()+'\\'+dirName)
                    self.getList()
            else:
                # Tell user why the directory was not deleted
                dlg = ConfirmationDialog(self,f'Could not delete {dirName} as it was not empty.','Error',False)
                if dlg.exec_():
                    pass

    def makeDirButton(self,dirName):
        '''Makes a function for a directory button.
Works similarly to Keyboard's makeKey'''
        return lambda: self.dirFunk(dirName)

    def makeFileButton(self,fileName):
        '''Makes a function for a file button.
Works similarly to Keyboard's makeKey'''
        return lambda: self.fileFunk(fileName)

    def backFile(self):
        '''Moves into parent directory if possible (cd ..)'''
        global home
        cwd = os.getcwd()
        if cwd != home: #Won't move past home, to prevent crashes
            os.chdir(cwd[:cwd.rfind('\\')]) #Removes last part of the path
            self.getList() #Updates GUI

    def BackIconUpdate(self):
        '''Updates back file icon to reflect if valid/invalid'''
        global home
        global resources
        returnAddress = os.getcwd()
        os.chdir(resources)
        if returnAddress == home:
            self.BackButton.setIcon(QIcon('BackIconInv.png'))
        else:
            self.BackButton.setIcon(QIcon('BackIcon.png'))
        os.chdir(returnAddress)

    def newDir(self):
        '''Makes a new directory'''
        # Gets the name
        dlg = KeyboardDialog(self,'Name the Folder','New Folder')
        if dlg.exec_():
            # Makes the directory
            os.mkdir(self.dataSlot)
            # Updates GUI
            self.getList()

    def newFile(self):
        '''Makes a new file, loads it into main editor and closes file browser'''
        # Gets the name
        dlg = KeyboardDialog(self,'Name the File','Untitled')
        if dlg.exec_():
            # Makes the file
            with open(self.dataSlot+'.txt','w') as file:
                pass
            # Loads it into the editor
            self.parent().dataSlot = self.dataSlot+'.txt'
            self.accept()

    def sendLocation(self):
        '''An alternative to self.accept for sending back a location'''
        self.parent().dataSlot = os.getcwd()
        self.accept()








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
