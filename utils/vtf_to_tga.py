import sys, os
import subprocess
from random import randint

# https://developer.valvesoftware.com/wiki/VTF2TGA
# Runs vtf2tga.exe on every vtf file
# Same thing as `VTFCmd.exe -folder "<dir>\materials\*.vtf" -recurse`

# Usage Instructions:
# run the script directly
# or `python vtf_to_tga.py input_path` from the cmd prompt


OVERWRITE_EXISTING_TGA = False
IGNORE_WORLD_CUBEMAPS = True

# if available, force skybox vtfs to run on the 2nd row executable
FORCE_SKYBOX_ON_2ND_EXE = True

currentDir = os.getcwd()
PATH_TO_CONTENT_ROOT = r""

# Add your vtf2tga.exe here. Accepts full (C:/) and relative paths (../).
vtf2tga_paths = [
    r"../vtf2tga/2013/vtf2tga.exe",
    r"../vtf2tga/csgo/vtf2tga.exe", # FORCE_SKYBOX_ON_2ND_EXE
    #r"C:\Program Files (x86)\Steam\steamapps\common\Source SDK Base 2013 Multiplayer\bin\vtf2tga.exe"
    #r"..\vtf2tga\tf2\vtf2tga.exe"
    #r"..\vtf2tga\l4d2\vtf2tga.exe"
    #r"..\vtf2tga\2004\vtf2tga.exe"
]

tags = []
for item in range(len(vtf2tga_paths)):
    path = vtf2tga_paths[item]
    path = os.path.normpath(path.replace("..", currentDir))

    if os.path.exists(path):
        print("+ Using", path)
        vtf2tga_paths[item] = path
        tags.append(os.path.basename(path.replace('vtf2tga', '').replace('.exe', '').replace('bin', '').strip('/\\.')))
    else:
         vtf2tga_paths.remove(path)

if not vtf2tga_paths:
    print("The specified VTF2TGA executables were not found.")
    quit(-1)

if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2): PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        while not PATH_TO_CONTENT_ROOT:
            c = input('Type the main directory of the vtf files you want to export (enter to use current directory, q to quit).: ') or currentDir
            if not os.path.isdir(c) and not os.path.isfile(c):
                if c in ('q', 'quit', 'exit', 'close'): quit()
                print('Could not find file or directory.')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')

def parseDir(dirName):
    files = []
    skipdirs = ['dev', 'debug', 'tools', 'vgui', 'console', 'correction']
    for root, _, fileNames in os.walk(dirName):
        for skipdir in skipdirs:
            if ('materials\\' + skipdir) in root: continue

        for fileName in fileNames:
            if fileName.lower().endswith('.vtf'):
                filePath = os.path.join(root,fileName)

                if IGNORE_WORLD_CUBEMAPS:
                    numbers = sum(c.isdigit() for c in fileName)
                    dashes = fileName.count('_') + fileName.count('-')
                    if (numbers > 4) and (dashes >= 2) and (fileName.startswith('c')):
                        #if fileName.lower().endswith('.hdr.vtf') or \
                        #os.path.exists(fileName.lower().replace('.vtf', '.hdr.vtf')):
                        #print("Ignoring world cubemap file", fileName)
                        continue

                if OVERWRITE_EXISTING_TGA:
                    if os.path.exists(filePath.replace('.vtf', '.tga'))\
                    or os.path.exists(filePath.replace('.vtf', '.pfm'))\
                    or os.path.exists(filePath.replace('.vtf', '000.tga')):
                        #print("Ignoring already exported file", fileName)
                        continue

                files.append(filePath)

                if len(files) % randint(90, 270) == 0:
                    print("Found", len(files), "files")

    print("Total:", len(files), "files")

    return files

fileList = []

if os.path.isfile(PATH_TO_CONTENT_ROOT):
    if(PATH_TO_CONTENT_ROOT.lower().endswith('.vtf')):
        fileList.append(PATH_TO_CONTENT_ROOT)
        PATH_TO_CONTENT_ROOT = PATH_TO_CONTENT_ROOT.split("materials", 1)[0]
    else:
        print("~ Invalid file.")
else:
    folderPath = PATH_TO_CONTENT_ROOT
    if not 'materials' in PATH_TO_CONTENT_ROOT \
    and not PATH_TO_CONTENT_ROOT.endswith('.vtf') \
    and not PATH_TO_CONTENT_ROOT.rstrip('\\/').endswith('materials'):
        folderPath = os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, 'materials'))
    if os.path.isdir(folderPath):
        print("\n-", folderPath.capitalize())
        print("+ Scanning for .vtf files. This may take a while...")
        fileList.extend(parseDir(folderPath))
    else: print("~ Could not find a /models/ folder inside this dir.\n")

PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'

def formatVmatDir(localPath):
    if not localPath: return None
    localPath = os.path.normpath(localPath)
    return localPath.replace(PATH_TO_CONTENT_ROOT, '')

erroredFileList = []

for vtfFile in fileList:

    expectedOutputTGA = vtfFile.replace('.vtf', '.tga')
    expectedOutputPFM = vtfFile.replace('.vtf', '.pfm')
    expectedOutputTGA_frame = vtfFile.replace('.vtf', '000.tga')

    force_2nd = False
    if(FORCE_SKYBOX_ON_2ND_EXE and (len(vtf2tga_paths) > 1) and ('skybox' in vtfFile)):
        force_2nd = True # 2nd exe outputs pfm files. use that for hdr skybox files

    for vtf2tga_exe in vtf2tga_paths:
        if(force_2nd and (vtf2tga_paths.index(vtf2tga_exe) != 1)):
            continue

        try:
            command = [vtf2tga_exe, "-i", vtfFile]
            result = subprocess.run(command, stdout=subprocess.PIPE)
            #print (result.stdout)

            if result.returncode == 0: # TGA or PFM file created. Onto the next VTF.
                textureFile = ''
                if os.path.exists(expectedOutputTGA): textureFile = formatVmatDir(expectedOutputTGA)
                elif os.path.exists(expectedOutputPFM): textureFile = formatVmatDir(expectedOutputPFM)
                elif os.path.exists(expectedOutputTGA_frame): textureFile = formatVmatDir(expectedOutputPFM)

                print("[" + tags[vtf2tga_paths.index(vtf2tga_exe)] + "]", "Sucessfully created", textureFile)
                break

            if not ((len(vtf2tga_paths) > 1) and (vtf2tga_paths.index(vtf2tga_exe) < (len(vtf2tga_paths) - 1))):
                erroredFileList.append(vtfFile)

        except: pass

if erroredFileList:
    print("Could not export the following files:")
    for erroredFile in erroredFileList:
        print(formatVmatDir(erroredFile))

print("\n+ Looks like we are done.")

