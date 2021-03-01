import os
FileName = "program data.txt"
newfile = 0

print(os.getcwd())

def load(FileName):
    TextFile = open(FileName,"r")
    name = TextFile.read()
    TextFile.close()
    print(name)

def save(FileName):
    TextFile = open(FileName,"w")
    name = str(input("Enter your text. "))
    TextFile.write(name)
    TextFile.close()
    print("Saved!")

def menu(FileName):
    n = 0
    while n<1 or n>3:
        print("Current file is " + FileName)
        n = int(input("Do you want to switch files / save / load? (1 to save, 2 to load, 3 to switch) "))
    if n ==  1:
        save(FileName)
    elif n ==  2:
        load(FileName)
    else:
        FileName = input("Enter the file name. ")
        newfile = 0
        try:
         TextFile = open(FileName,"x")
         newfile = 1
         print("File created.")
        except:
            TextFile = open(FileName,"r")
            print("File loaded.")
        print(newfile)
        TextFile.close()
    menu(FileName)

menu(FileName)
