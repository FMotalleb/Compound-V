from gc import collect
from turtle import screensize
from lib import BFV
from lib.bones import bones
import time
import math
from ctypes import *
from pynput.mouse import Button, Controller
from difflib import SequenceMatcher
import pydirectinput
from threading import Thread
from playsound import playsound
import os
import numpy as np
import lib.keycodes as keycodes
import yaml

debug = 1


class Aimer:
    tick = 0
    fallOffMultiplier = 0
    closestDistance = 9999
    closestSoldier = None
    closestSoldierMovementX = 0
    closestSoldierMovementY = 0
    lastSoldier = 0
    screensize = (0, 0)
    dodge = False
    soldierPrevPosition = np.array([0., 0., 0.])
    counter = 0
    diff = np.array([0., 0., 0.])

    def config(self, config):
        scope = config['basic']
        self.fov = scope['fov']
        self.distance_limit = scope['min_distance']
        self.trigger = keycodes.asArray[scope['hold_to_aim_key']]

        scope = config['auto_shoot']
        self.autoshoot = scope['is_active']
        self.toggle_autoshoot = scope['toggle_key']

        aim_locations = []
        for bone in config['aiming']['locations']:
            aim_locations.append(bones[bone])
        self.aim_locations = aim_locations
        self.aim_switch = keycodes.asArray[config['aiming']
                                           ['switch_location_key']]

        scope = config['basic']['screen_size']
        self.screensize = (scope['width'],
                           scope['height'])

        scope = config['hunt']
        self.huntToggle = keycodes.asArray[scope['toggle_key']]
        self.huntTargetSwitch = keycodes.asArray[scope['target_select']]

        scope = config['auto_scope']
        self.autoscope = scope['is_active']

        scope = config['dodge']
        self.dodgeMode = scope['is_active']
        self.crouch_Key = scope['crouch_Key']
        self.toggle_dodge_Mode = keycodes.asArray[scope['toggle_key']]

        self.toggle_keep_target = keycodes.asArray[config['basic']
                                                   ['toggle_keep_target']]

        scope = config['aiming']['falloff_correction']
        self.fallOffMultiplier = scope['amount']
        self.increase_falloff_multiplier = keycodes.asArray[scope['increase_key']]
        self.decrease_falloff_multiplier = keycodes.asArray[scope['decrease_key']]

        scope = config['aiming']['fixed_correction']
        self.base_Y_aim_correction = scope['amount']
        self.increase_base_Y_correction = keycodes.asArray[scope['increase_key']]
        self.decrease_base_Y_correction = keycodes.asArray[scope['decrease_key']]

        scope = config['aiming']['movement_prediction_factor']
        self.movement_prediction_toggle_key = keycodes.asArray[scope['toggle_key']]
        self.movement_prediction_increase = keycodes.asArray[scope['increase_key']]
        self.movement_prediction_decrease = keycodes.asArray[scope['decrease_key']]
        self.movement_prediction_factor = scope['amount']
        self.movement_prediction = scope['is_active']

    def switchTo(self, config_name):
        with open("config.yaml", "r") as yamlfile:
            config = yaml.load(yamlfile, Loader=yaml.FullLoader)
        self.config(config['configs'][config_name])
        self.print("switched to {}".format(config_name))
        time.sleep(2)

    def __init__(self, config, print_method):
        self.config(config)
        self.print = print_method

    def DebugPrintMatrix(self, mat):
        print("[%.3f %.3f %.3f %.3f ]" %
              (mat[0][0], mat[0][1], mat[0][2], mat[0][3]))
        print("[%.3f %.3f %.3f %.3f ]" %
              (mat[1][0], mat[1][1], mat[1][2], mat[1][3]))
        print("[%.3f %.3f %.3f %.3f ]" %
              (mat[2][0], mat[2][1], mat[2][2], mat[2][3]))
        print("[%.3f %.3f %.3f %.3f ]\n" %
              (mat[3][0], mat[3][1], mat[3][2], mat[3][3]))

    def DebugPrintVec4(self, Vec4):
        print("[%.3f %.3f %.3f %.3f ]\n" %
              (Vec4[0], Vec4[1], Vec4[2], Vec4[3]))

    def accelDistance(self, distance):
        leftMin = 0
        rightMin = 0.5
        leftSpan = 100 - 0
        rightSpan = 1.2 - 0.5

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(distance - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)

        # return 0.0 + (distance - 0) / 20 * 100

    def dodgeIt(self):
        while True:
            if self.dodge:
                pydirectinput.press(self.crouch_Key)
            time.sleep(0.01)

    def activateSound(self):
        Thread(target=playsound, args=(os.getcwd() +
               '/snd/activate.mp3',), daemon=True).start()

    def deActivateSound(self):
        Thread(target=playsound, args=(os.getcwd() +
               '/snd/deactivate.mp3',), daemon=True).start()

    def start(self, retry_count=0):
        print("[+] Searching for BFV.exe")
        phandle = BFV.get_handle()
        if phandle:
            time.sleep(1)
        else:
            if(retry_count >= 10):
                print("[-] Error: Cannot find BFV.exe after 50 seconds exiting")
                exit(1)
            print(
                "[-] Error: Cannot find BFV.exe retry in 5 seconds: {}".format(retry_count))
            retry_count = retry_count+1

            time.sleep(5)

            self.start()

        print("[+] BFV.exe found, Handle 0x%x" % phandle)
        cnt = 0
        # mouse = Controller()
        self.lastSoldier = 0
        self.lastX = 0
        self.lastY = 0
        aim_location_index = 0
        aim_location_max = len(self.aim_locations) - 1
        aim_switch_pressed = False

        aim_location_names = []
        for location in self.aim_locations:
            for key in bones:
                if bones[key] == location:
                    aim_location_names.append(key)

        # m = Mouse()
        pressedCounter = 0
        pressed = False
        pressedL = False
        huntMode = False
        keepTarget = False
        huntSoldier = None
        huntSoldierName = None
        mouse = Controller()

        dodge = Thread(target=self.dodgeIt)
        dodge.start()

        while 1:
            if cdll.user32.GetAsyncKeyState(keycodes.INSERT) & 0x8000:
                self.print('reading config in cmd')
                config_name=input("enter config name: ")
                if config_name is not '':
                    self.switchTo(config_name)
                    
            # change aim location index if key is pressed
            if self.aim_switch:
                if cdll.user32.GetAsyncKeyState(self.aim_switch) & 0x8000:
                    aim_switch_pressed = True
                elif aim_switch_pressed:
                    aim_switch_pressed = False
                    aim_location_index = aim_location_index + 1
                    if aim_location_index > aim_location_max:
                        aim_location_index = 0

            BFV.process(phandle, cnt, self.aim_locations[aim_location_index])
            cnt += 1

            data = BFV.gamedata
            self.closestDistance = 9999
            self.closestSoldier = None
            self.closestSoldierMovementX = 0
            self.closestSoldierMovementY = 0
            if cdll.user32.GetAsyncKeyState(self.increase_falloff_multiplier) & 0x8000:
                self.fallOffMultiplier += 0.01
                self.print("FallOffMultiplier {:.3f}".format(
                    self.fallOffMultiplier))
                time.sleep(0.2)
            elif cdll.user32.GetAsyncKeyState(self.decrease_falloff_multiplier) & 0x8000:
                self.fallOffMultiplier -= 0.01
                self.print("FallOffMultiplier {:.3f}".format(
                    self.fallOffMultiplier))
                time.sleep(0.2)
            if cdll.user32.GetAsyncKeyState(self.increase_base_Y_correction) & 0x8000:
                self.base_Y_aim_correction += 1
                self.print("Base Y Aim Correction {:.3f}".format(
                    self.base_Y_aim_correction))
                time.sleep(0.2)
            elif cdll.user32.GetAsyncKeyState(self.decrease_base_Y_correction) & 0x8000:
                self.base_Y_aim_correction -= 1
                self.print("Base Y Aim Correction {:.3f}".format(
                    self.base_Y_aim_correction))
                time.sleep(0.2)
            if cdll.user32.GetAsyncKeyState(self.movement_prediction_increase) & 0x8000:
                self.movement_prediction_factor += 5
                self.print("movement correction factor {}".format(
                    self.movement_prediction_factor))
                time.sleep(0.2)
            elif cdll.user32.GetAsyncKeyState(self.movement_prediction_decrease) & 0x8000:
                self.movement_prediction_factor -= 5
                self.print("movement correction factor {}".format(
                    self.movement_prediction_factor))
                time.sleep(0.2)
            if cdll.user32.GetAsyncKeyState(self.movement_prediction_toggle_key) & 0x8000:
                self.movement_prediction = not self.movement_prediction
                if(self.movement_prediction):
                    self.print("movement prediction activated")
                    self.activateSound()
                else:
                    self.print("movement prediction deactivated")
                    self.deActivateSound()
                time.sleep(0.2)
            if cdll.user32.GetAsyncKeyState(self.toggle_keep_target) & 0x8000:
                keepTarget = not keepTarget
                if keepTarget:
                    self.print("keep target on")
                    self.activateSound()
                else:
                    self.print("keep target off")
                    self.deActivateSound()
                time.sleep(1)

            if cdll.user32.GetAsyncKeyState(self.huntToggle) & 0x8000:
                if not data.soldiers:
                    print("You are currently not in a round")
                elif huntSoldier is None:
                    print("No Soldier to hunt chosen")
                else:
                    huntMode = not huntMode
                    if huntMode:
                        self.distance_limit_old = self.distance_limit
                        self.distance_limit = None
                        self.activateSound()
                    else:
                        self.distance_limit = self.distance_limit_old
                        self.deActivateSound()
                time.sleep(1)

            if cdll.user32.GetAsyncKeyState(self.huntTargetSwitch) & 0x8000:
                if not data.soldiers:
                    print("You are currently not in a round")
                else:
                    print()
                    name = input("Enter a name to hunt:")
                    ratios = []
                    for soldier in data.soldiers:
                        ratios += [SequenceMatcher(None,
                                                   name, soldier.name).ratio()]
                    huntSoldierName = data.soldiers[ratios.index(
                        max(ratios))].name
                time.sleep(1)

            for soldier in data.soldiers:
                if huntSoldierName is None:
                    break
                if soldier.name == huntSoldierName:
                    huntSoldier = soldier
                    break

            if cdll.user32.GetAsyncKeyState(self.toggle_autoshoot) & 0x8000:
                self.autoshoot = not self.autoshoot
                if self.autoshoot:
                    self.print("auto shoot on")
                    self.activateSound()
                else:
                    self.print("auto shoot off")
                    self.deActivateSound()
                time.sleep(0.3)

            if cdll.user32.GetAsyncKeyState(self.toggle_dodge_Mode) & 0x8000:
                self.dodgeMode = not self.dodgeMode
                if self.dodgeMode:
                    self.activateSound()
                else:
                    self.deActivateSound()
                time.sleep(0.3)

            if self.lastSoldier != 0:
                if cdll.user32.GetAsyncKeyState(self.trigger) & 0x8000:
                    found = False
                    for Soldier in data.soldiers:
                        if huntMode and huntSoldier != Soldier:
                            continue
                        if self.lastSoldier == Soldier.ptr:
                            found = True
                            if Soldier.occluded:
                                if keepTarget:
                                    mouse.release(Button.left)
                                else:
                                    self.lastSoldier = 0
                                    self.closestSoldier = None
                                    self.lastX = 0
                                    self.lastY = 0
                                    self.soldierPrevPosition = np.array(
                                        [0., 0., 0.])
                                    self.diff = np.array([0., 0., 0.])
                                    self.counter = 0
                                    continue
                            try:
                                dw, distance, delta_x, delta_y, Soldier.ptr, dfc = self.calcAim(
                                    data, Soldier)
                                self.closestDistance = dfc
                                self.closestSoldier = Soldier

                                # accel = 0  # this is WIP
                                # + (self.lastX * accel)
                                self.closestSoldierMovementX = delta_x
                                # + (self.lastY * accel)
                                self.closestSoldierMovementY = delta_y
                                self.lastX = delta_x
                                self.lastY = delta_y
                                continue
                                # print("x: %s" % delta_x)
                            except Exception as e:
                                self.lastSoldier = 0
                                self.closestSoldier = None
                                #print("Disengaging: soldier no longer meets criteria: %s" % e)
                    if not found:
                        self.lastSoldier = 0
                        self.closestSoldier = None
                        self.lastX = 0
                        self.lastY = 0
                        self.soldierPrevPosition = np.array([0., 0., 0.])
                        self.diff = np.array([0., 0., 0.])
                        self.counter = 0
                        #print("Disengaging: soldier no longer found")
                else:
                    self.lastSoldier = 0
                    self.closestSoldier = None
                    self.lastX = 0
                    self.lastY = 0
                    self.soldierPrevPosition = np.array([0., 0., 0.])
                    self.diff = np.array([0., 0., 0.])
                    self.counter = 0
                    #print("Disengaging: key released")
            else:
                distanceList = []
                for Soldier in data.soldiers:
                    if huntMode and huntSoldier != Soldier:
                        continue
                    try:

                        if Soldier.occluded:
                            continue

                        dw, distance, delta_x, delta_y, Soldier.ptr, dfc = self.calcAim(
                            data, Soldier)

                        if dw > self.fov:
                            continue

                        if self.distance_limit is not None and distance > self.distance_limit:
                            continue

                        distanceList += [distance]
                        if distance <= min(distanceList):
                            if dfc < self.closestDistance:  # is actually comparing dfc, not distance
                                if cdll.user32.GetAsyncKeyState(self.trigger) & 0x8000:
                                    self.closestDistance = dfc
                                    self.closestSoldier = Soldier
                                    self.closestSoldierMovementX = delta_x
                                    self.closestSoldierMovementY = delta_y
                                    self.lastSoldier = Soldier.ptr
                                    self.lastSoldierObject = Soldier
                                    self.lastX = delta_x
                                    self.lastY = delta_y
                                    self.distance = distance
                    except:
                        # print("Exception", sys.exc_info()[0])
                        continue
                status = "[%s] " % aim_location_names[aim_location_index]
                if self.lastSoldier != 0:
                    if self.autoscope:
                        pressed = True
                        pressedCounter = 0
                        mouse.press(Button.right)

                    if self.lastSoldierObject.name != "":
                        name = self.lastSoldierObject.name
                        if self.lastSoldierObject.clan != "":
                            name = "[%s]%s" % (
                                self.lastSoldierObject.clan, name)
                    else:
                        name = "0x%x" % self.lastSoldier
                    status = status + "locked onto %s" % name
                else:
                    status = status + "idle"
                    pressedCounter += 1
                    if pressed and self.autoscope and pressedCounter >= 50:
                        mouse.release(Button.right)
                        pressedCounter = 0
                        pressed = False
                if not huntMode:
                    print("%-50s" % status, end="\r")
                if huntMode and huntSoldierName is not None:
                    print("Current Hunt: ", "[%s]%s" % (huntSoldier.clan, huntSoldier.name), "Distance: ", round(self.FindDistance(huntSoldier.transform[3][0], huntSoldier.transform[3][1], huntSoldier.transform[3][2],
                                                                                                                                   data.mytransform[3][0], data.mytransform[3][1], data.mytransform[3][2]), 1), end="\r")
            if self.dodgeMode:
                self.dodge = False
            if self.autoshoot and pressedL:
                mouse.release(Button.left)
                pressedL = False
            if cdll.user32.GetAsyncKeyState(self.trigger) & 0x8000:
                if self.closestSoldier is not None:
                    if self.closestSoldierMovementX > self.screensize[0] / 2 or self.closestSoldierMovementY > \
                            self.screensize[1] / 2:
                        continue

                    else:
                        if abs(self.closestSoldierMovementX) > self.screensize[0]:
                            continue
                        if abs(self.closestSoldierMovementY) > self.screensize[1]:
                            continue
                        if self.closestSoldierMovementX == 0 and self.closestSoldierMovementY == 0:
                            continue
                        increment = self.distance * self.fallOffMultiplier
                        if self.distance < 75:
                            increment = 0

                        increment = increment + self.base_Y_aim_correction

                        self.print("target: {}\ndistance: {:.1f}\ncorrection: {}".format(
                            self.closestSoldier.name, self.distance, round(increment)))
                        self.move_mouse(int(self.closestSoldierMovementX), int(
                            self.closestSoldierMovementY) - round(increment))
                        if self.dodgeMode:
                            self.dodge = True
                        if self.autoshoot:
                            if not self.closestSoldier.occluded:
                                mouse.press(Button.left)
                                pressedL = True
                        time.sleep(0.001)
                else:
                    self.print("no target")
            else:
                if self.closestSoldier is not None:
                    self.print("can pick {}".format(self.closestSoldier.name))
                else:
                    self.print("idle")

    def calcAim(self, data, Soldier):

        transform = Soldier.aim

        distance = self.FindDistance(Soldier.transform[3][0], Soldier.transform[3][1], Soldier.transform[3][2],
                                     data.mytransform[3][0], data.mytransform[3][1], data.mytransform[3][2])

        if Soldier.ptr == self.lastSoldier and distance > 45 and self.movement_prediction:
            soldierPosition = np.array(
                [transform[0], transform[1], transform[2]])
            if not np.array_equal(self.soldierPrevPosition, [0., 0., 0.]):
                if(self.counter == 7):
                    self.diff = soldierPosition - self.soldierPrevPosition
                    self.diff *= distance / self.movement_prediction_factor
                    if self.diff[0] < 0.1 and self.diff[0] > -0.1 and self.diff[1] < 0.1 and self.diff[1] > -0.1 and self.diff[2] < 0.1 and self.diff[2] > -0.1:
                        self.diff = np.array([0., 0., 0.])
            if(self.counter == 7):
                self.soldierPrevPosition = soldierPosition
                self.counter = 0
            self.counter += 1

        transform[0] = transform[0] + \
            (self.diff[0]) + Soldier.accel[0] - data.myaccel[0]
        transform[1] = transform[1] + \
            (self.diff[1]) + Soldier.accel[1] - data.myaccel[1]
        transform[2] = transform[2] + \
            (self.diff[2]) + Soldier.accel[2] - data.myaccel[2]

        x, y, w = self.World2Screen(
            data.myviewmatrix, transform[0], transform[1], transform[2])

        distance = self.FindDistance(Soldier.transform[3][0], Soldier.transform[3][1], Soldier.transform[3][2],
                                     data.mytransform[3][0], data.mytransform[3][1], data.mytransform[3][2])

        dw = distance - w

        delta_x = (self.screensize[0] / 2 - x) * -1
        delta_y = (self.screensize[1] / 2 - y) * -1

        dfc = math.sqrt(delta_x ** 2 + delta_y ** 2)

        return dw, distance, delta_x / 2, delta_y / 2, Soldier.ptr, dfc

    def FindDistance(self, d_x, d_y, d_z, l_x, l_y, l_z):
        distance = math.sqrt((d_x - l_x) ** 2 + (d_y - l_y)
                             ** 2 + (d_z - l_z) ** 2)
        return distance

    def World2Screen(self, MyViewMatrix, posX, posY, posZ):

        w = float(
            MyViewMatrix[0][3] * posX + MyViewMatrix[1][3] * posY + MyViewMatrix[2][3] * posZ + MyViewMatrix[3][3])

        x = float(
            MyViewMatrix[0][0] * posX + MyViewMatrix[1][0] * posY + MyViewMatrix[2][0] * posZ + MyViewMatrix[3][0])

        y = float(
            MyViewMatrix[0][1] * posX + MyViewMatrix[1][1] * posY + MyViewMatrix[2][1] * posZ + MyViewMatrix[3][1])

        mX = float(self.screensize[0] / 2)
        mY = float(self.screensize[1] / 2)

        x = float(mX + mX * x / w)
        y = float(mY - mY * y / w)

        return x, y, w

    def move_mouse(self, x, y):  # relative
        ii = Input_I()
        ii.mi = MouseInput(x, y, 0, 0x1, 0, pointer(c_ulong(0)))
        command = Input(c_ulong(0), ii)
        windll.user32.SendInput(1, pointer(command), sizeof(command))


PUL = POINTER(c_ulong)


class KeyBdInput(Structure):
    _fields_ = [("wVk", c_ushort),
                ("wScan", c_ushort),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(Structure):
    _fields_ = [("uMsg", c_ulong),
                ("wParamL", c_short),
                ("wParamH", c_ushort)]


class MouseInput(Structure):
    _fields_ = [("dx", c_long),
                ("dy", c_long),
                ("mouseData", c_ulong),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class POINT(Structure):
    _fields_ = [("x", c_long),
                ("y", c_long)]


class Input_I(Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(Structure):
    _fields_ = [("type", c_ulong),
                ("ii", Input_I)]
