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
 - Here pytesseract is imported which is what is used for converting handwriting to text. We Have been experimenting with different ways to use AI to read handwriting and we have tried creating a neural network ouserselves. However, we found that the most effecient and effective way was using pytesseract as it saved us time to focus on other crucial parts of code that needed construction or completion.
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
- This is where we decided to use pytesseract for our character recogntion and conversion.
```
        self.pages[self.display.currentIndex()].insertPlainText(text.strip())
        self.canvas.clearImage()
```
- This code is needed to reset the canvas after the conversion has been processed
# Save/Load Functions

