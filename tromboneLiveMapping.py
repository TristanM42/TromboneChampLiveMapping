''' Map an axis coordinates to notes (= pitch, in Trombone champ unit) and create the Trombone champ map file. '''

def lerpAxis(position, minPosition, maxPosition, minPitch, maxPitch):
    lerpedPitch = (position-minPosition)/(maxPosition-minPosition)*(maxPitch-minPitch) + minPitch
    return lerpedPitch

# Sequence of chromatic notes in trombone format : [Bar (time), Length, Pitch Start, Pitch Delta (angle), Pitch End]
# tromboneChromaticSequence = [[1,0.5,-165,0,-165],[1.5,0.5,-151.25,0,-151.25],[2,0.5,-137.5,0,-137.5],[2.5,0.5,-123.75,0,-123.75],[3,0.5,-110,0,-110],[3.5,0.5,-96.25,0,-96.25],[4,0.5,-82.5,0,-82.5],[4.5,0.5,-68.75,0,-68.75],[5,0.5,-55,0,-55],[5.5,0.5,-41.25,0,-41.25],[6,0.5,-27.5,0,-27.5],[6.5,0.5,-13.75,0,-13.75],[7,0.5,0,0,0],[7.5,0.5,13.75,0,13.75],[8,0.5,27.5,0,27.5],[8.5,0.5,41.25,0,41.25],[9,0.5,55,0,55],[9.5,0.5,68.75,0,68.75],[10,0.5,82.5,0,82.5],[10.5,0.5,96.25,0,96.25],[11,0.5,110,0,110],[11.5,0.5,123.75,0,123.75],[12,0.5,137.5,0,137.5],[12.5,0.5,151.25,0,151.25],[13,0.5,165,0,165]]

# Set manually bpm of the map ; if used an osu file, go to [TimingPoints] and take the second value as beatDurationInMS, then bpm = 60/(beatDurationInMS/1000)
mapBPM = 160.5

# Convert time from milliseconds to bar : if using osu file, hitobjects format is "x,y,time,type,hitSound,objectParams,hitSample"
timeToBar = lambda timeInMS : ((timeInMS/1000)*mapBPM/60)/4 # timeS = (bar*4)*60/bpm
mapTimings = [52637, 52761, 52886, 53011, 53135, 53260, 53384, 53726, 53850, 53975, 54100, 54474, 54848, 54972, 55097, 55222, 55595, 55969, 56343, 56467, 56592, 56717, 57091, 57465, 57839, 57963, 58088, 58213, 58586, 58710, 58835, 58960, 59084, 59209, 59333, 60113, 60299, 60486, 60674, 60861, 61048, 61235, 61422, 61608, 61794, 61981, 62169, 62356, 62543, 62730, 62917, 63104, 63290, 63477, 63665, 63852, 64039, 64226, 64413, 64600, 64724, 64849, 64974, 65098, 65223, 65347, 66095, 66281, 66468, 66656, 66843, 67030, 67217, 67404, 67590, 67776, 67963, 68151, 68338, 68525, 68712, 68899, 69086, 69272, 69459, 69647, 69834, 70021, 70208, 70581, 70705, 70830, 70955, 71079, 71204, 71328, 72076, 72262, 72449, 72637, 72824, 73011, 73198, 73385, 73571, 73757, 73944, 74132, 74319, 74506, 74693, 74880, 75067, 75253, 75440, 75628, 75815, 76002, 76189, 76376, 76562, 76686, 76811, 76936, 77060, 77185, 77309, 78057, 78243, 78430, 78618, 78805, 78992, 79179, 79366, 79552, 79738, 79925, 80113, 80300, 80487, 80674, 80861, 81048, 81234, 81421, 81609, 81796, 81983, 82170, 82544, 82668, 82793, 82918, 83042, 83167, 83291, 84038, 84162, 84288, 84412, 84786, 84911, 85036, 85160, 85533, 85658, 85782, 85907, 86281, 86405, 86530, 86655, 86779, 86904, 87028, 87153, 87279, 87403, 87777, 87902, 88027, 88151, 88524, 88649, 88773, 88898, 89272, 89396, 89521, 89646, 89770, 89895, 90019] # regex : "^\d+,\d+,(\d+),.*$\n" and keep group 1
mapTimingsInBars = list(map(timeToBar, mapTimings))
# Make sure that we start song at zero + one bar for example :
barOffset = mapTimingsInBars[0]
mapTimingsInBars = [b - barOffset + 1 for b in mapTimingsInBars]
mapTimingsInBars = [ '%.2f' % e for e in mapTimingsInBars]

# Convert Y axis to MIDI pitch : if using osu file, we probably need to convert from normalized space to Full HD resolution : "equivalent to a pixel when osu! is running in 640x480 resolution" + invert y axis
yNormalized = [96, 103, 129, 157, 129, 103, 96, 76, 154, 200, 257, 76, 76, 76, 76, 76, 76, 76, 76, 76, 76, 76, 74, 74, 74, 74, 74, 74, 96, 104, 123, 157, 124, 102, 93, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 72, 96, 103, 129, 157, 129, 103, 96, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 96, 104, 123, 157, 124, 102, 93, 257, 152, 73, 159, 72, 256, 153, 72, 258, 153, 74, 155, 77, 256, 156, 75, 255, 153, 72, 154, 259, 258, 153, 72, 87, 96, 124, 157, 122, 93, 76, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 72, 256, 153, 72, 153, 72, 256, 153, 96, 104, 123, 157, 124, 102, 93, 80, 92, 124, 95, 92, 124, 154, 124, 124, 154, 167, 154, 87, 96, 124, 157, 122, 93, 76, 94, 125, 95, 92, 124, 154, 124, 124, 154, 167, 154, 87, 96, 124, 157, 122, 93, 76] # regex : "^\d+,(\d+),\d+,.*$\n" and keep group 1
fullHDCoordinates = [y*1080/480 for y in yNormalized]
fullHDCoordinatesWithInvertedAxis = [-y for y in fullHDCoordinates]
# Let's convert from Full HD to pitch (yea i assume you all have a full HD resolution for now) : lowest octave is at y = 935 pixels and highest octave is at 145 pixels
pitchList = [lerpAxis(y,145,935,-165,165) for y in fullHDCoordinatesWithInvertedAxis]
pitchList = [ '%.2f' % e for e in pitchList]

# Generate the Trombone champ file :
author = "Peter Lambert"
description = "A map based on osu! tutorial, that you can play as if you would have a mouse, even though x axis does not matters."
difficulty = 7
minimalDurationInBars = 0.25
endpoint = mapTimingsInBars[-1] + minimalDurationInBars # = last note timing + its duration (assuming that we only simple hits, refactor later for holding a note)
genre = "Video game"
name = "osu! Tootorial"
shortName = name
year = 2007

desc1 = '{"UNK1":0,"author": "' + author + '","description":"' + description + '","difficulty":'+ str(difficulty) +',"endpoint":' + str(endpoint) + ',"genre":"' + genre + '","lyrics":[],"name":"' + name + '","notes":'
desc2 = ',"savednotespacing":120,"shortName":"' + shortName + '","tempo":' + str(mapBPM) + ',"timesig":2,"trackRef":"CustomSongs","year":' + str(year) + '}'
notes = []
for timeAsbars,pitch in zip(mapTimingsInBars, pitchList):
    notes.append([timeAsbars, minimalDurationInBars, pitch, 0, pitch])
finalFileString = desc1 + str(notes) + desc2
with open("song.tmb", 'w') as f:
    f.write(finalFileString)