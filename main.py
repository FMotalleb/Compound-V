from tkinter import N
from lib import aimer as aim
from lib import helpers
from lib import keycodes
from lib.bones import bones
import time
import ctypes
import threading
import tkinter as tk
from overlay import Window


def main(printMethod):
    print("Compound-V by survivalizeed")
    print()
    if not helpers.is_admin():
        print("- Error: This must be run with admin privileges")
        input("Press Enter to continue...")
        exit(1)

    if not helpers.is_python3():
        print("- Error: This script requires Python 3")
        input("Press Enter to continue...")
        exit(1)

    arch = helpers.get_python_arch()
    if arch != 64:
        print("- Error: This version of Python is not 64-bit")
        input("Press Enter to continue...")
        exit(1)

    # print("Using screensize: %s x %s" % screensize)
    aimer = aim.Aimer(print_method=printMethod)
    aimer.start()


win_0 = Window()
label_0 = tk.Label(win_0.root, text="init")
label_0.pack()


def printMethod(text):
    label_0.config(text=text,)


window_thread = threading.Thread(target=main, args=[printMethod])
# Start the thread
window_thread.start()

label_0.mainloop()
