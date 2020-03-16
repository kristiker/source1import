# cmd command: python mdl_to_vmdl.py "C:\Program Files (x86)\Steam\steamapps\common\SteamVR\tools\steamvr_environments\content\steamtours_addons\l4d2_converted\models"
# MUST run in the models folder

import re, sys, os

INPUT_FILE_EXT = '.vmf'
# this leads to the root of the game folder, i.e. dota 2 beta/content/dota_addons/, make sure to remember the final slash!!
PATH_TO_GAME_CONTENT_ROOT = ""
PATH_TO_CONTENT_ROOT = ""
    
print('Source 2 .vmf Prepper! By caseytube via Github')
print('Converts .vmf files to be ready for Source 2')
print('--------------------------------------------------------------------------------------------------------')

filename = sys.argv[1]
convertedFilename = filename.replace('.vmf', '') + 'Converted.vmf'
if not os.path.exists(filename):
    print("input file doesn't exist")
    quit()

print('Importing', os.path.basename(filename))

with open(convertedFilename, 'w') as convFile:
    with open(filename, 'r') as vmfFile:
        for line in vmfFile.readlines():
            splitLine = line.replace('"', '').replace("'", "").split()
            last = len(splitLine) - 1
            
            if "uaxis" in line:
                oldVar = splitLine[last]
                print(oldVar)
                newVar = float(oldVar) * 32
                print(newVar)
                newLine = line.replace(str(oldVar), str(newVar))
                convFile.write(newLine)
            elif "vaxis" in line:
                oldVar = splitLine[last]
                print(oldVar)
                newVar = float(oldVar) * 32
                print(newVar)
                newLine = line.replace(str(oldVar), str(newVar))
                convFile.write(newLine)
            else:
                convFile.write(line)