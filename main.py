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

    #### CHANGE OPTIONS HERE ####

    # Field of View
    # Alter this between 0.1 and 3.0 for best results. 0.1 is very narrow, while larger numbers allow
    # for more soldiers to be targeted
    fov = 3

    # Distance Limit
    # Example, set to 100 to limit locking onto soldiers further than 100 meters away.
    distance_limit = None  # can also be: None

    # Trigger Button
    # Grab your preferred button from lib/keycodes.py
    trigger = keycodes.ALT

    # If set to True you will automatically crouch and uncrouch while shooting others. According to my experience this will make you be less shot by others.
    dodge_Mode = False

    # Your key to crouch. Use a string here instead of a keycode.
    crouch_Key = "ctrl"

    toggle_dodge_Mode = keycodes.NUMPAD2

    toggle_keep_target = keycodes.NUMPAD3

    # If set to True your weapon will automatically shoot after finding a target
    autoshoot = False

    # Toggle autoshoot. Use this if you are using a sniper or a small magazine.
    toggle_autoshoot = keycodes.NUMPAD1

    # If set to True your weapon will automatically scope as soon as you lock onto a target
    autoscope = False

    # Press this button to switch between normal aimbot and hunt
    hunt_Toggle = keycodes.NUMPAD5

    # Press this and you have to input a name into the console to hunt. You don't need to write the exact name the program will try to find the name with the most matches.
    hunt_Target_Switch = keycodes.NUMPAD8

    # Aim Location Options
    # Aim Location Switching (default is the first one listed)
    # Check available bones in lib/bones.py
    aim_locations = [bones['Head'], bones['Spine'],
                     bones['Neck'], bones['Hips']]

    # Key to switch aim location (set to None to disable)
    aim_switch = keycodes.END
    #aim_switch = None

    # Normally, you won't need to change this
    # This will attempt to gather your primary screen size. If you have issues or use
    # a windowed version of BFV, you'll need to set this yourself, which probably comes with its own issues
    screensize = ctypes.windll.user32.GetSystemMetrics(
        0), ctypes.windll.user32.GetSystemMetrics(1)
    # or
    #screensize = (1280, 960)

    # Here you can change fall off multiplier
    base_Y_aim_correction = 1
    increase_falloff_multiplier = keycodes.ADD
    decrease_falloff_multiplier = keycodes.SUBTRACT
    increase_base_Y_correction = keycodes.NUMPAD6
    decrease_base_Y_correction = keycodes.NUMPAD9

    movement_prediction_activator_key = keycodes.MULTIPLY
    movement_prediction_increase = keycodes.PAGEUP
    movement_prediction_decrease = keycodes.PAGEDOWN

    collection = [fov,
                  distance_limit,
                  trigger,
                  autoshoot,
                  autoscope,
                  aim_locations,
                  aim_switch,
                  screensize,
                  hunt_Toggle,
                  hunt_Target_Switch,
                  dodge_Mode,
                  crouch_Key,
                  toggle_autoshoot,
                  toggle_dodge_Mode,
                  toggle_keep_target,
                  increase_falloff_multiplier,
                  decrease_falloff_multiplier,
                  base_Y_aim_correction,
                  movement_prediction_activator_key,
                  printMethod,
                  increase_base_Y_correction,
                  decrease_base_Y_correction,
                  movement_prediction_increase,
                  movement_prediction_decrease
                  ]
    if fov < 0.1 or fov > 3.0:  # you can delete this if you know what you're doing
        print("Check your fov settings.")
        exit(1)
    if distance_limit is not None and distance_limit <= 0:
        print("Check your distance_limit settings")
        exit(1)

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

    print("Using screensize: %s x %s" % screensize)
    aimer = aim.Aimer(collection)
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
