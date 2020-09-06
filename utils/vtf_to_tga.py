import sys, os
import subprocess
from random import randint

# https://developer.valvesoftware.com/wiki/VTF2TGA
# Runs vtf2tga.exe on every vtf file
# Same thing as `VTFCmd.exe -folder "<dir>\materials\*.vtf" -recurse`

# Usage Instructions:
# run the script directly
# or `python vtf_to_tga.py input_path` from the cmd prompt


IGNORE_ALREADY_EXPORTED = True
IGNORE_WORLD_CUBEMAPS = True

PATH_TO_CONTENT_ROOT = r""

vtf2tga_paths = [
    r"../vtf2tga/2013/vtf2tga.exe",
    r"../vtf2tga/csgo/vtf2tga.exe",
    #r"C:\Program Files (x86)\Steam\steamapps\common\Source SDK Base 2013 Multiplayer\bin\vtf2tga.exe"
    #r"..\vtf2tga\tf2\vtf2tga.exe"
    #r"..\vtf2tga\l4d2\vtf2tga.exe"
    #r"..\vtf2tga\2004\vtf2tga.exe"
]

currentDir = os.getcwd()

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

if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2): PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        while not PATH_TO_CONTENT_ROOT:
            c = input('Type the main directory of the vtf files you want to export (enter to use current directory, q to quit).: ') or currentDir
            if not os.path.isdir(c) or not os.path.isfile(c):
                if c in ('q', 'quit', 'exit', 'close'): quit()
                print('Could not find file or directory.')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')

def formatVmatDir(localPath):
    if not localPath: return None
    localPath = os.path.normpath(localPath)
    return localPath.replace(PATH_TO_CONTENT_ROOT, '')

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

                if IGNORE_ALREADY_EXPORTED:
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

# Verify file paths
fileList = []
if(PATH_TO_CONTENT_ROOT):
    folderPath = PATH_TO_CONTENT_ROOT
    if not PATH_TO_CONTENT_ROOT.rstrip('\\/').endswith('materials'):
        folderPath = os.path.join(PATH_TO_CONTENT_ROOT, 'materials')

    absFilePath = os.path.abspath(folderPath)

    if os.path.isdir(absFilePath):
        print("Scanning for .vtf files. This may take a while...")
        fileList.extend(parseDir(absFilePath))
    elif(absFilePath.lower().endswith('.vtf')):
        fileList.append(absFilePath)
else:
    input("No file or directory specified, press any key to quit...")
    quit()


erroredFileList = []

for vtfFile in fileList:

    expectedOutputTGA = vtfFile.replace('.vtf', '.tga')
    expectedOutputPFM = vtfFile.replace('.vtf', '.pfm')

    #if not OVERRIDE_EXPORTED_FILES:
    #    if os.path.exists(expectedOutputTGA) or os.path.exists(expectedOutputPFM):
    #        #print ("Already exists. Skipping", os.path.basename(expectedOutputTGA))
    #        continue

    forceCsgo = False
    if 'skybox' in vtfFile:
        forceCsgo = True

    print ("+ ---------------------------------")
    print ("+ Opening file",  formatVmatDir(vtfFile))
    for vtf2tga_exe in vtf2tga_paths:

        # skip 2013 if it's a skybox. csgo version outputs pfm files. 
        if forceCsgo and "csgo/vtf2tga.exe" not in vtf2tga_exe:
            continue

        try:
            command = [vtf2tga_exe, "-i", vtfFile]
            result = subprocess.run(command, stdout=subprocess.PIPE)
            #print (result.stdout)

            #tag = "[" + vtf2tga_exe.replace('vtf2tga', '').replace('.exe', '').strip('/\\') + "]"
            #tag = os.path.basename(vtf2tga_exe.replace('vtf2tga', '').replace('.exe', '').replace('/bin/', '').strip('/\\.'))
            tag = tags[vtf2tga_paths.index(vtf2tga_exe)]

            if result.returncode == 0: # TGA or PFM file created. Onto the next VTF.
                textureFile = ''
                if os.path.exists(expectedOutputTGA):
                    textureFile = formatVmatDir(expectedOutputTGA)
                elif os.path.exists(expectedOutputPFM):
                    textureFile = formatVmatDir(expectedOutputPFM)

                print(tag, "Created file", textureFile)
                print("+ ---------------------------------\n")
                break

            else: # Else try with the next vtf lib version
                print(tag, "Could not export this vtf.")
                if not ((len(vtf2tga_paths) > 1) and (vtf2tga_paths.index(vtf2tga_exe) < (len(vtf2tga_paths) - 1))):
                    erroredFileList.append(vtfFile)


        except: pass

if erroredFileList:
    print("Could not export the following files:")
    for erroredFile in erroredFileList:
        print(formatVmatDir(erroredFile))

print("\n+ Looks like we are done.\n\n")

