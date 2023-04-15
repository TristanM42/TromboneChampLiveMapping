# Input listeners
from pynput import keyboard, mouse
# import pynput.mouse as mIn
# import pynput.keyboard as kIn

#Output writer
from pynput.mouse import Button, Controller
from pynput.keyboard import Key

import pickle
import time
import ctypes
import threading

# version : 7391ed1a97877bfdbba9213807178d7cf0020cfd

# Current features :
#   - record and play in real time actions : typing, clicking, scrolling
#   - serialization for saving a record in a file and extract it for playing it
#   - start recording at first event (w, x or space using osu mode)
#   - osu mode : only one press event until release ( = keys converted to click)
#   - compiled with pyinstaller, but not so much speed gain
#   - log "move" only once
#   - trombone champ mode : start on first key pressed and register mouse move (to detect sliders extremums), but limiting mouse move events at a maximum framerate of 53.4 fps (obtained from 200 bpm divided by 16 : 1/((60/200)/16)) or 27 fps for 8 division.

# === Features coming ===
#   - hotkeys mapping needed (key 'x01' = ctrl + a, ...)
#   - debug mode :
#       - pause with hotkey and give pdb or display actions done and next actions
#       - continue or stop playing
#       - move mouse only
#       - play actions withing given interval in time or index
#   - custom speed factor
#   - custom key to stop recording, instead of escape
#   - try python compilation if possible for quick install
#   - pack multiples events in one for easy handling of recorder key combinations (shift+escape to stop recording for example)
#   - loop whole seq (or only part of the seq by shortcuts) for n iterations
#   - optimize data save by reducing the framerate
#   - Recorder mode (1 = fast ; 2 = tutorial ; 3 = real time ; 4 = custom/song like)
#   - versioning of differents records with an incremental name or ask user a name
#   - ...
#
# =======================

mouseController = mouse.Controller()
keyboardController = keyboard.Controller()

class Recorder:

    # Sequence class :

    class Sequence:

        def __init__(self, mode=None, framerate=1000):
            self.eventIndex = 0
            self.mode = '2'
            self.start_time = 0
            self.actions = []
            self.timeFromStart = [] # time of last event in seconds (decimal)
            self.mousePosition = [] # as top left corner convention
            self.lockedOn = {}
            self.startFlag = False
            self.lastButtonEventState = None
            self.framerate = framerate

            if(mode==None):
                print("Recorder mode ? (1 = fast ; 2 = tutorial ; 3 = real time ; 4 = custom/song like ; 5 = osu ; 6 = Trombone Champ)")
                self.mode = str(input())
                if(self.mode=='5'): print("osu mode : Press w, x or space to start at first circle")
            else:
                self.mode = mode
            self.osuClickIsLeft = True

        def handleEvent(self, key, pressed, timeEvent, x=None, y=None):
            if(self.mode == '5' and self.readOnly == True and self.startFlag == False):
                if(key=='Key.space' or key=='w' or key=='x'):
                    self.startFlag = True
                    t = threading.Thread(target=self.parent.playSequence)
                    t.start()
            if((self.mode == '5' or self.mode == '6')and self.readOnly == False and self.startFlag == False):
                if(key!='Key.space' and key!='w' and key!='x'):
                    return False
                else:
                    self.start_time = time.time()
                    print(str(self.start_time) + " ; " + str(timeEvent))
                    self.nextTime = self.start_time + 1/self.framerate
                    self.startFlag = True
            if(self.readOnly == True): return False
            if (key=='move' and time.time() < self.nextTime): return
            self.checkLock(key)
            if(x == y == None):
                (x, y) = self.mousePosition[-1] if len(self.mousePosition) > 0 else mouseController.position
            self.customAction(key, pressed, timeEvent, x, y)

        def checkLock(self, key):
            try:
                self.lockedOn[key]
            except KeyError:
                print(key + " not registered yet")
                self.lockedOn[key] = False

        def customAction(self, key, pressed, timeEvent, x, y):
            # if(pressed==True):
            #     pdb.set_trace()
            if (pressed==True and self.lockedOn[key]==False) or key=='move' or pressed==False or pressed==-1:
                if(self.mode == '5' or self.mode == '6'):
                    if(key=='move'):
                        self.actions.append((key,))
                    elif(len(key)==1 or key=='Button.left' or key=='Button.right'):
                        self.osuClickIsLeft = not self.osuClickIsLeft
                        self.actions.append(('Button.left',pressed) if(self.osuClickIsLeft) else ('Button.right',pressed))
                        print(self.actions[-1])
                    else:
                        return
                    self.timeFromStart.append(timeEvent-self.start_time)
                    self.mousePosition.append((x,y))
                elif(self.mode == '3'):
                    if (key != 'move' or self.actions[-1][0] != 'move'):
                        print("key pressed = " + key)
                    self.actions.append((key,) if key=='move' else (key,pressed))
                    self.timeFromStart.append(timeEvent-self.start_time)
                    self.mousePosition.append((x,y))
                if(pressed==False):
                    self.lockedOn[key] = False
                elif(self.lockedOn[key]==False):
                    self.lockedOn[key] = True
                # if(self.mode == ...

            if key=='move':
                self.nextTime = self.timeFromStart[-1] + 1/self.framerate + self.start_time



    # Keyboards events :

    def on_press(self, key):
        timePress = time.time()
        keyStr = None
        if key == keyboard.Key.esc:
            # Stop listener
            self.recorderExitSignalSent = True
            print("Aborted")
            return False
        if(str(key)[0]!='K'):
            keyStr = '{0}'.format(key.char)
        else:
            keyStr = str('{0}'.format(key))
        self.seq.handleEvent(keyStr, True, timePress)
    def on_release(self, key):
        timeRelease = time.time()
        keyStr = None
        if(str(key)[0]!='K'):
            keyStr = '{0}'.format(key.char)
        else:
            keyStr = str('{0}'.format(key))
        self.seq.handleEvent(keyStr, False, timeRelease)

    # Mouse events :

    def on_move(self, x, y):
        self.seq.handleEvent('move', None, time.time(), x, y)
        if(self.recorderExitSignalSent): return False
    def on_click(self, x, y, button, pressed):
        self.seq.handleEvent(str(button), pressed, time.time())
    def on_scroll(self, x, y, dx, dy):
        self.seq.handleEvent('scroll', dy, time.time())


    def startThreads(self):
        self.seq.start_time = time.time()
        # Listening in non-blocking fashion :
        kbL = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        mL = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll)
        mL.start()
        kbL.start()
        mL.join()
        kbL.join()
        self.seq.startFlag = False

    def playSequence(self):
        print("WARNING : Now playing a sequence...")
        start_time = time.time()
        closestIndex = 2
        while(time.time() - start_time <= self.seq.timeFromStart[-1]):
            if(self.recorderExitSignalSent): break
            if(self.seq.timeFromStart[closestIndex] <= time.time() - start_time):
                if (self.seq.actions[closestIndex][0] != 'move' or self.seq.actions[closestIndex-1][0] != 'move'):
                    print("now play " + str(self.seq.actions[closestIndex][0]))
                if(self.seq.actions[closestIndex][0] == 'move'):
                    # pdb.set_trace()
                    mouseController.position = (self.seq.mousePosition[closestIndex][0], self.seq.mousePosition[closestIndex][1])
                elif(self.seq.actions[closestIndex][0] == 'scroll'):
                    mouseController.scroll(0,self.seq.actions[closestIndex][1])
                elif(len(self.seq.actions[closestIndex][0]) == 1): # if key (not click)
                    if(self.seq.actions[closestIndex][1] == True): # if isPressed
                        keyboardController.press(self.seq.actions[closestIndex][0])
                    else:
                        keyboardController.release(self.seq.actions[closestIndex][0])
                elif(self.seq.actions[closestIndex][0][:3] == 'Key'): # if special key (not click)
                    if(self.seq.actions[closestIndex][1] == True): # if isPressed
                        keyboardController.press(eval(self.seq.actions[closestIndex][0]))
                    else:
                        keyboardController.release(eval(self.seq.actions[closestIndex][0]))
                else: # then it's click
                    if(self.seq.actions[closestIndex][1] == True): # if isPressed
                        mouseController.press(eval(self.seq.actions[closestIndex][0]))
                    else:
                        mouseController.release(eval(self.seq.actions[closestIndex][0]))
                closestIndex += 1
        print("Done")

    def initPlaying(self):
        self.seq.readOnly = True
        time.sleep(0.5)
        t = threading.Thread(target=self.startThreads)
        t.start()
        if((self.seq.mode=='5' or self.seq.mode=='6') and self.seq.startFlag == False):
            print("Press w,x or space key to start from first event")
        else:
            self.playSequence()
        t.join()


    def __init__(self, seqR=None, mode=None, framerate=1000):
        self.recorderExitSignalSent = False
        if(seqR==None):
            self.seq = self.Sequence(mode, framerate)
        else:
            self.seq = seqR
        self.seq.readOnly = False
        self.seq.parent = self
        PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)


# Example of use
if __name__ == '__main__':


    print("Mode record ou play ? (1 = record ; 2 = play)")
    mode = str(input())


    if(mode=='1'):

        rec = Recorder() 
        rec.startThreads() # /!\ blocking instruction, press escape to finish the recording (or a programmed shortcut)

        # pdb.set_trace()

        # # Use pickle for class serialization :

        with open('pickled_sequence.pkl', mode='wb') as binary_file:
            # Write 
            pickle.dump(rec.seq, binary_file)


    if(mode=='2'):

        seqR = None
        with open('pickled_sequence.pkl', mode='rb') as binary_file:
            # Read
            seqR = pickle.load(binary_file)
            # pdb.set_trace()

        rec = Recorder(seqR)
        rec.initPlaying()


