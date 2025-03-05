import eel
import os
import tkinter
from tkinter import filedialog

@eel.expose
def saveFST2File(fst):
    filename = filedialog.asksaveasfilename(initialdir=os.getcwd(),
        title = "Save as")#,
        #filetypes =  [("text file","*.txt")])
    if type(filename) is not str:
        return
    with open(filename, 'w') as f:
        f.write(fst)

#####
root = tkinter.Tk()
root.withdraw()
eel.init("auxtool")
eel.start("index.html")
