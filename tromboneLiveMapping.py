from recorder import Recorder
import json
import numpy as np
from ioManager import InputManager
import pickle
import os

''' Map an axis coordinates to notes (= pitch, in Trombone champ unit) and create the Trombone champ map file. '''

# TODO :
#   - quantizer except for sliders (= only for separated notes) from a scale (default being chromatic scale)
#   - post editing to correct pitch with a global pitch offset (make a pitch list for every pitch start and another for every pitch end)
#   - live mapping (with sliders)
# others features :
#   - extract melody (highest notes) from a midi
#   - arpeggiator

# repeat a note pattern : (np.array(listOfNotes) + [shiftingInBeats,shiftingInPitch,0,shiftingInPitch,0]).tolist()
# tune the time start offset : notes = np.array(yourNotesArray) then notes[:,0] -= 1 then notes.tolist()

scaleIntervals = { # in half tones ; add octave (0+12) for repeating pattern without losing a note
    "chromatic" : [0,1,2,3,4,5,6,7,8,9,10,11,12],
    "major" : [0,2,4,5,7,9,11,12],
    "minor" : [0,2,3,5,7,8,10,12],
    "pentatonicMajor" : [0,3,5,7,10,12],
}

absoluteNotes = ["C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B"]

def lerpAxis(position, minPosition, maxPosition, minPitch, maxPitch):
    lerpedPitch = (position-minPosition)/(maxPosition-minPosition)*(maxPitch-minPitch) + minPitch
    return lerpedPitch

def getPitchForScale(scaleName="chromatic", noteOffset="C"):
    rootIndex = absoluteNotes.index(noteOffset)
    return [n*13.75-165+rootIndex*13.75 for n in scaleIntervals[scaleName]] # root is always lowest C here

def periodizeSerie(inputSerie, n, extraSteps=0):
    ''' Extend the input serie n times with the same pattern (= repeat each local increase rate, periodically). Use extraSteps in case you need more accuracy, for iterations that are less than one period. /!\ Output is different of what would be a periodized function, since each new period applies the slope on its root. '''
    periodizedSerie = inputSerie[:]
    for j in range(n+1):
        for i in range(len(inputSerie)-1):
            if (j==n and i>=extraSteps): break
            periodizedSerie.append(periodizedSerie[-1]+(inputSerie[i+1]-inputSerie[i]))
    return periodizedSerie

def quantizeNote(note, scalePitchList):
    return min(scalePitchList, key=lambda x:abs(x-note))

def correctOffset(songname):
    with open(songname, "r+") as f:
        data = f.read()
        pyson = json.loads(data)
        input = InputManager()
        print("Press 't' for first note of the music then press again when it's the same note coming in your chart", flush=True)
        timeInSeconds = input.timerBetweenTwoPress() 
        print("Time offset = ", timeInSeconds, flush=True)
        timeToBar = lambda time : (time*mapBPM/60)
        mapBPM = pyson["tempo"]
        endpoint = pyson["endpoint"]
        notes = np.array(pyson["notes"])
        timeOffset = timeToBar(timeInSeconds)
        notes[:,0] -= timeOffset
        endpoint -= timeOffset
        pyson["notes"] = np.round(notes,2).tolist()
        pyson["endpoint"] = np.round(endpoint,2)
        f.seek(0)
        json.dump(pyson, f, separators=(',', ':'))
        f.truncate()

def excepthook(type, value, traceback):
    pdb.post_mortem(traceback)

# Sequence of chromatic notes (starting from lowest C, and then spread until the highest C) :
# Trombone notes format : [Bar (time), Length, Pitch Start, Pitch Delta (angle), Pitch End] /!\ here, a bar is actually one beat, not 4 beats as we could expect (if signature is 4/4) ; pitch delta should be pitch end - pitch start
# All notes are 13.75 apart, starting from -165 for lowest C.
# tromboneChromaticSequence = [[1,0.5,-165,0,-165],[1.5,0.5,-151.25,0,-151.25],[2,0.5,-137.5,0,-137.5],[2.5,0.5,-123.75,0,-123.75],[3,0.5,-110,0,-110],[3.5,0.5,-96.25,0,-96.25],[4,0.5,-82.5,0,-82.5],[4.5,0.5,-68.75,0,-68.75],[5,0.5,-55,0,-55],[5.5,0.5,-41.25,0,-41.25],[6,0.5,-27.5,0,-27.5],[6.5,0.5,-13.75,0,-13.75],[7,0.5,0,0,0],[7.5,0.5,13.75,0,13.75],[8,0.5,27.5,0,27.5],[8.5,0.5,41.25,0,41.25],[9,0.5,55,0,55],[9.5,0.5,68.75,0,68.75],[10,0.5,82.5,0,82.5],[10.5,0.5,96.25,0,96.25],[11,0.5,110,0,110],[11.5,0.5,123.75,0,123.75],[12,0.5,137.5,0,137.5],[12.5,0.5,151.25,0,151.25],[13,0.5,165,0,165]] # regex to get the note : (\[.*?\],){13} (1 is the lowest C, 13 is the middle C) or "notes":\[(\[.*?\], ){13} in tmb file

if __name__ == "__main__":


    # correctOffset('song.tmb')
    # import sys
    # sys.exit()

    # Set manually bpm of the map ; if used an osu file, go to [TimingPoints] and take the second value as beatDurationInMS, then bpm = 60/(beatDurationInMS/1000)
    mapBPM = 185

    seqFile = 'pickled_sequence.pkl'
    lastMappingCrashedAfterRecord = os.path.isfile(seqFile)
    rec = None
    if lastMappingCrashedAfterRecord:
        seqR = None
        with open(seqFile, mode='rb') as binary_file:
            seqR = pickle.load(binary_file)
        rec = Recorder(seqR)
        import pdb
        import sys
        sys.excepthook = excepthook
    else:
        # Record keyboard times and mouse positions
        rec = Recorder(mode='6' ,framerate=53.4)
        rec.startThreads() # /!\ blocking instruction, press escape to finish the recording
        with open(seqFile, mode='wb') as binary_file:
            pickle.dump(rec.seq, binary_file)

    # Convert Y axis to MIDI pitch : if using osu file, we probably need to convert from normalized space to Full HD resolution : "equivalent to a pixel when osu! is running in 640x480 resolution" => actually, max limits in x,y = (512,384) + invert y axis
    # yNormalized = [96, 103, 129, 157, 129, 103, 96, 76, 154, 200, 257, 76, 76, 76, 76, 76, 76, 76, 76, 76, 76, 76, 74, 74, 74, 74, 74, 74, 96, 104, 123, 157, 124, 102, 93, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 72, 96, 103, 129, 157, 129, 103, 96, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 96, 104, 123, 157, 124, 102, 93, 257, 152, 73, 159, 72, 256, 153, 72, 258, 153, 74, 155, 77, 256, 156, 75, 255, 153, 72, 154, 259, 258, 153, 72, 87, 96, 124, 157, 122, 93, 76, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 96, 104, 123, 157, 124, 102, 93, 80, 92, 124, 95, 92, 124, 154, 124, 124, 154, 167, 154, 87, 96, 124, 157, 122, 93, 76, 94, 125, 95, 92, 124, 154, 124, 124, 154, 167, 154, 87, 96, 124, 157, 122, 93, 76] # regex : "^\d+,(\d+),\d+,.*$\n" and keep group 1
    # fullHDCoordinates = [lerpAxis(y,0,384,125,125+841) for y in yNormalized]
    fullHDCoordinates = rec.seq.mousePosition
    yList = [pos[1] for pos in fullHDCoordinates]
    # ylistInverted = [1080-y for y in yList]
    # Let's convert from Full HD to pitch (yea i assume you all have a full HD resolution for now) : lowest octave is at y = 935 pixels and highest octave is at 145 pixels
    pitchList = [lerpAxis(y,145,935,165,-165) for y in yList]
    pitchList = [round(e,2) for e in pitchList]
    scalePitchList = getPitchForScale("major", "C")
    scalePitchList = periodizeSerie(scalePitchList, 1) # spread it on the other octave (higher)
    quantizedPitchStartList = pitchList #[quantizeNote(n, scalePitchList) for n in pitchList]

    # Convert time from milliseconds to bar : if using osu file, hitobjects format is "x,y,time,type,hitSound,objectParams,hitSample"
    timeMSToBar = lambda timeInMS : ((timeInMS/1000)*mapBPM/60) # timeS = (bar*4)*60/bpm
    # mapTimings = [52637, 52761, 52886, 53011, 53135, 53260, 53384, 53726, 53850, 53975, 54100, 54474, 54848, 54972, 55097, 55222, 55595, 55969, 56343, 56467, 56592, 56717, 57091, 57465, 57839, 57963, 58088, 58213, 58586, 58710, 58835, 58960, 59084, 59209, 59333, 60113, 60299, 60486, 60674, 60861, 61048, 61235, 61422, 61608, 61794, 61981, 62169, 62356, 62543, 62730, 62917, 63104, 63290, 63477, 63665, 63852, 64039, 64226, 64413, 64600, 64724, 64849, 64974, 65098, 65223, 65347, 66095, 66281, 66468, 66656, 66843, 67030, 67217, 67404, 67590, 67776, 67963, 68151, 68338, 68525, 68712, 68899, 69086, 69272, 69459, 69647, 69834, 70021, 70208, 70581, 70705, 70830, 70955, 71079, 71204, 71328, 72076, 72262, 72449, 72637, 72824, 73011, 73198, 73385, 73571, 73757, 73944, 74132, 74319, 74506, 74693, 74880, 75067, 75253, 75440, 75628, 75815, 76002, 76189, 76376, 76562, 76686, 76811, 76936, 77060, 77185, 77309, 78057, 78243, 78430, 78618, 78805, 78992, 79179, 79366, 79552, 79738, 79925, 80113, 80300, 80487, 80674, 80861, 81048, 81234, 81421, 81609, 81796, 81983, 82170, 82544, 82668, 82793, 82918, 83042, 83167, 83291, 84038, 84162, 84288, 84412, 84786, 84911, 85036, 85160, 85533, 85658, 85782, 85907, 86281, 86405, 86530, 86655, 86779, 86904, 87028, 87153, 87279, 87403, 87777, 87902, 88027, 88151, 88524, 88649, 88773, 88898, 89272, 89396, 89521, 89646, 89770, 89895, 90019] # regex : "^\d+,\d+,(\d+),.*$\n" and keep group 1
    timeToBar = lambda time : (time*mapBPM/60) # timeS = (bar*4)*60/bpm
    mapTimings = rec.seq.timeFromStart
    mapTimingsInBars = list(map(timeToBar, mapTimings))
    # Make sure that we start song at zero + one bar for example :
    barOffset = mapTimingsInBars[0] - 4
    mapTimingsInBars = [b - barOffset for b in mapTimingsInBars]
    mapTimingsInBars = [round(e,2) for e in mapTimingsInBars]

    # Calculate the duration of the note, given by the closest time where a key is released or slider change direction
    notes = [] # Trombone Champ format : [Bar (time), Length, Pitch Start, Pitch Delta (angle), Pitch End]
    actions = rec.seq.actions
    i = 0
    currentAction = None
    lastDurationWasFromButtonUp = True
    duration = None
    pitchStart = None
    pitchEnd = None
    pitchDelta = None
    while i < len(mapTimingsInBars):
        if lastDurationWasFromButtonUp:
            if not (actions[i][0] == 'Button.right' or actions[i][0] == 'Button.left' and actions[i][1] == True):
                i += 1
                continue
        slopeRef = yList[i+1] - yList[i]
        x = 1
        while True:
            currentAction = actions[i+x][0]
            if currentAction == 'Button.right' or currentAction == 'Button.left':
                if actions[i+x][1] == False:
                    lastDurationWasFromButtonUp = True
                    break
            slope = yList[i+x+1] - yList[i+x]
            if slopeRef != 0: 
                if slope/slopeRef <= 0:
                    lastDurationWasFromButtonUp = False
                    break
            elif slope != 0: 
                if slopeRef/slope <= 0:
                    lastDurationWasFromButtonUp = False
                    break
            x += 1
        start = mapTimingsInBars[i]
        duration = mapTimingsInBars[i+x] - start
        pitchStart = quantizedPitchStartList[i]
        pitchEnd = quantizedPitchStartList[i+x]
        pitchDelta = pitchEnd - pitchStart
        notes.append([start, duration, pitchStart, pitchDelta, pitchEnd])
        i = i+x

    # Generate the Trombone champ file :
    author = "Peter Lambert"
    description = "A map based on osu! tutorial, that you can play as if you would have a mouse, even though x axis does not matter."
    difficulty = 7
    endpoint = notes[-1][0] + notes[-1][1]
    genre = "Video game"
    name = "osu! Tootorial"
    shortName = name
    year = 2007
    trackRef = "osu!Tootorial" # folder name must match !

    desc1 = '{"UNK1":0,"author": "' + author + '","description":"' + description + '","difficulty":'+ str(difficulty) +',"endpoint":' + str(endpoint) + ',"genre":"' + genre + '","lyrics":[],"name":"' + name + '","notes":'
    desc2 = ',"savednotespacing":120,"shortName":"' + shortName + '","tempo":' + str(mapBPM) + ',"timesig":2,"trackRef":"' + trackRef + '","year":' + str(year) + '}'

    notes = np.round(np.array(notes), 2).tolist()

    finalFileString = desc1 + str(notes) + desc2
    with open("song.tmb", 'w') as f:
        f.write(finalFileString)

    if lastMappingCrashedAfterRecord:
        os.remove(seqFile)