# Inputs
from pynput.keyboard import Key
from pynput import keyboard

# Output
from pynput.mouse import Button
from pynput.keyboard import Key

from lib.debug import *
from enum import Enum
import time

# version : 9b408c108beed598446c33adb692a0e253b5f8c7

# Exemple of use for input manager :
# inputs = InputManager()
# print("press a")
# inputs.waitForKey("a")
# print("press b")
# inputs.waitForKey("b")
# print("press c")
# inputs.waitForKey("c")

class InputManager:

    currentKeys = None
    keyAsStr = None
    Mode = Enum('Mode', ['waitForKeys', 'signal'])
    signaled = {}

    def on_press(self, key):
        if key == keyboard.Key.esc:
            # Stop listener
            printDebug("Aborted")
            return False
        if(str(key)[0]!='K'):
            self.keyAsStr = '{0}'.format(key.char)
        else:
            self.keyAsStr = str('{0}'.format(key))
        printDebug("key pressed = ", self.keyAsStr)
        if self.mode == self.Mode.waitForKeys:
            if self.keyAsStr in self.currentKeys: return False
        if self.mode == self.Mode.signal:
            self.signaled[self.keyAsStr] = True

    def on_release(self, key):
        if(str(key)[0]!='K'):
            self.keyAsStr = '{0}'.format(key.char)
        else:
            self.keyAsStr = str('{0}'.format(key))
        printDebug("key released = ", self.keyAsStr)

    def waitForKey(self, *keys):
        self.mode = self.Mode.waitForKeys
        self.currentKeys = keys
        kbL = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        kbL.start()
        kbL.join()
        return self.keyAsStr
    
    def listenKeyboardThread(self):
        self.mode = self.Mode.signal
        kbL = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        kbL.start()
        return

    def signal(self, keyAsStr):
        try:
            self.signaled[keyAsStr]
            self.signaled[keyAsStr] = False
            return True
        except KeyError:
            return False

    def timerBetweenTwoPress(self):
        self.waitForKey("t")
        startTime = time.time()
        self.waitForKey("t")
        timeInSeconds = time.time() - startTime
        return timeInSeconds