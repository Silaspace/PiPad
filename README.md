# PiPad

## Imports and Globals
```
import sys, os, math, time
```
 - These are useful imports from the Python Standard Library that are needed for basic tasks in the code.
 
```
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QIODevice, QBuffer
from PyQt5.QtGui import QIcon, QImage, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QTextEdit, QMainWindow, QAction, QApplication, QToolBar, QSizePolicy, QSpacerItem
```
 - These are the imports from PyQt5 which are needed for the majority of the UserInterface code. We decided on using PyQt5 because it is widespread and relatively easy to use and a great choice for the UI we needed to make.

```
import pytesseract
from PIL import Image
from io import BytesIO
import PIL.ImageOps
```
 - Here pytesseract is imported which is what is used for converting handwriting to text. We have been experimenting with different ways to use AI to read handwriting and we have tried creating a neural network ouserselves. However, we found that the most effecient and effective way was using pytesseract as it saved us time to focus on other crucial parts of code that needed construction or completion.
```
#resourcepath = "Z:\PiPad-main\PiPad-main\\resources"
#csspath = "Z:\PiPad-main\PiPad-main\styles.css"
#path = "Z:\PiPad-main\PiPad-main\saved\\"
```
 - These are global variables for Windows because we are using Windows machines to develop and design the code.

```
resourcepath = os.getcwd() + "/resources/"
csspath = os.getcwd() + "/styles.css"
path = os.getcwd() + "/saved/"
```
 - These are global variables for linux which we have chosen to use as the OS for our Raspberry Pi.
 
```
control = "~"
backgroundcolor = "#171717"
```
# Canvas
 - The "canvas" is what the user will use to write on.
 
 ```
        self.image = QImage(1200, 300, QImage.Format_RGB32)
        self.path = QPainterPath()
 ```
 - Here we are defining Qimage and Qpath which are important for code in the future
 ```
    def clearImage(self):
        self.path = QPainterPath()
        self.image.fill(Qt.black)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(event.rect(), self.image, self.rect())
        
    def mouseMoveEvent(self, event):
        self.path.lineTo(event.pos())
        p = QPainter(self.image)
        p.setPen(QPen(self.myPenColor, self.myPenWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(self.path)
        p.end()
        self.update()
```
- Here in clearImage, self.image is used to refer to the background and self.path is being reset. self.update is a function from the parent class that has been inherited.
- In mouseMoveEvent self.path is used to create a line when the user is drawing.
# Input functions
```
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        self.canvas.image.save(buffer, "png")
        data = BytesIO(buffer.data())
        buffer.close()
```
- Here this code has been wrote to turn whats been applied to the canvas into a png format so it can be manipulated.
```
        img = Image.open(data)
        img = PIL.ImageOps.invert(img)
        thresh = 200
        fn = lambda x : 255 if x > thresh else 0
        img = img.convert('L').point(fn, mode='1')
```
- Here is the beginning of some of the optimisations we have applied to our program so that the software is as efficient as possible.
- This just turns the png of the canvas into a monochrome format so that any coloured inputs can be used in optimistation
```
        crop = img.crop((x3,y3,x4,y4))
```
- This crops the canvas image, that is going to be used by the AI, so that all white parts of the image are removed as its not needed. Originally we had thought of doing this by using vectors to find maximum and minimum boundarys for the image but this caused unwanted problems. We ended up obtaining specific co-ordiantes for our image to be cropped to because it was most reliable.
```
        text = pytesseract.image_to_string(crop, config ='--psm 10')
```
- This is where we decided to use pytesseract for our character recogntion and conversion. We had tried different configuration options and came to the concliusion that psm 10 works the best for our purposes as it performed the best when attempting character recognition.
```
        self.pages[self.display.currentIndex()].insertPlainText(text.strip())
        self.canvas.clearImage()
```
- This code is needed to reset the canvas after the conversion has been processed
# Delete Notes
```
        for i in range(len(self.saveNoteButtons)):
            self.saveNoteButtons.pop(0).deleteLater()
```
- If the user chooses to delete saved notes then this function will do that for them to make the experience even more convenient.
# Save/Load Functions
- The program has a save/load fuction so that drawings and/or notes can be saved so that they can be edited and revisited.
```
        dlg = SelectionDialog(self,False)
        if dlg.exec_():
```
- Here in (SaveNotesAs) we are enabling the user to choose where to save the file.
```
                if fname in os.listdir(os.getcwd()):
                    dlg3 = ConfirmationDialog(self,name+' already exists. Overwrite it?')
                    if dlg3.exec_():
```
- They can also overwite files as notes may need to be modified. These are all necessary functions for an ideal school or workplace device and we chose to have this increased functionality in the product to ensure it could provide near as much help as current products but for a fraction of the price.
```
        self.deleteNotes()
        self.addNotes()
```
- To refresh the notes once one has been added or removed the current notes are all deleted and replaced with the new ones.
- The user ias also notified when a file has been saved so as to make their experience as fluent as possible.
# The Keybaord
- The keybaord is an on-screen display so no external devices are needed to function the raspberry Pi.
```
        super().__init__()
        self.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.stacked = Stacked
        self.keys = {}
        self.display = display
        self.rackStack = rackStack
```
 - setSizeConstraint is used because without it the keyboard doesnt correctly fit the display.
 - rackstack is used so that when the user presses shift it can swich between the keybaords one which has lower case and the other being upper case characters.
```
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
```
- Here we are just declaring the charcters that will be used for both keybards by using a list within lists where each new sub-list is a new row on the keybaord.
```
        for colNum, key in enumerate(keyRow):
            self.keys[key] = QtWidgets.QPushButton(key)
            self.keys[key].setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.addWidget(self.keys[key], rowNum, colNum)
```
- Here is part of the code that takes care of enlarging the buttons in relationship to the size of the window so that the keybaord can be as optimal as possible for the users inentions.
```
        DanOrange = self.display.currentWidget() if self.stacked else self.display
        DanOrange.insertPlainText(control)
        text = DanOrange.toPlainText()
        delpos = text.find(control)
        if delpos != 0:
            DanOrange.setPlainText(text[delpos+len(control):])
            DanOrange.insertPlainText(text[:delpos-1])
        else:
            DanOrange.setPlainText(text[len(control):])
```
- Here is the code for deleting character which we have added to our project as a function withing the application so that file editing is simple and any mistakes can be corrected easily.
```
        if self.rackStack.currentIndex() == 1:
            self.rackStack.setCurrentIndex(2 if self.stacked else 0)
        else:
            self.rackStack.setCurrentIndex(1)
```
- This is how the keybaord switches to a CAPS keybaord when the Shift key is pressed by the user so that they have full access the a wide range of options for creating and addiing to or editing files.
