import sys, os
import subprocess

# https://developer.valvesoftware.com/wiki/VTF2TGA
# Runs vtf2tga.exe on every vtf file
# Same thing as `VTFCmd.exe -folder "<dir>\materials\*.vtf" -recurse`

# Usage Instructions:
# run the script directly
# or `python vtf_to_tga.py input_path` from the cmd prompt


OVERWRITE_EXISTING_TGA = False
IGNORE_WORLD_CUBEMAPS = True

# Add your vtf2tga.exe here. Accepts full (C:/) and relative paths (../). Priority is top to bottom
vtf2tga_paths = [
    r"../vtf2tga/2013/vtf2tga.exe",
    r"../vtf2tga/csgo/vtf2tga.exe", # FORCE_SKYBOX_2ND_VTF2TGA
    r"C:\Program Files (x86)\Steam\steamapps\common\Source SDK Base 2013 Multiplayer\bin\vtf2tga.exe",
    r"C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\bin\vtf2tga.exe",
    r"D:\Games\steamapps\common\Team Fortress 2\bin\vtf2tga.exe",
    #r"..\vtf2tga\tf2\vtf2tga.exe",
    #r"..\vtf2tga\hl2\vtf2tga.exe",
]

# if there is one, force skybox vtfs to run on the 2nd row executable
FORCE_SKYBOX_2ND_VTF2TGA = True

currentDir = os.path.dirname(os.path.realpath(__file__)) #os.getcwd()
PATH_TO_CONTENT_ROOT = r""

INPUT_FILE_EXT = ".vtf"
OUTPUT_FILE_EXT = [
    '.tga',     # LDR
    '.pfm',     # HDR
    'up.tga',   # LDR CUBEMAP FACE UP (+ dn, lf, rt, ft, bk)
    'up.pfm',   # HDR CUBEMAP FACE UP (+ dn, lf, rt, ft, bk)
    '000.tga'   # GIF FRAME 0 (+ 001, 002, 003, ...)
]

tags = []

for vtf2tga_path in vtf2tga_paths:
    full_path = os.path.normpath(vtf2tga_path.replace("..", currentDir))

    if os.path.exists(full_path):
        print("+ Using:", full_path)
        vtf2tga_paths[vtf2tga_paths.index(vtf2tga_path)] = full_path
        tags.append(os.path.basename(vtf2tga_path.replace('vtf2tga', '').replace('.exe', '').replace('bin', '').strip('/\\.')))
    else:
        print("~ Path does not exist:", full_path)
        vtf2tga_paths[vtf2tga_paths.index(vtf2tga_path)] = None

if not any(vtf2tga_paths):
    print(f"No valid vtf2tga.exe was found. Please open {os.path.basename(__file__)} and verify your paths.")
    quit(-1)

if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2): PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        while not PATH_TO_CONTENT_ROOT:
            c = input('\n\nType in the directory of your .vtf file(s) (enter to use current directory, q to quit).: ') or currentDir
            if not os.path.isdir(c) and not os.path.isfile(c):
                if c in ('q', 'quit', 'exit', 'close'): quit()
                print('Could not find file or directory.')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')

def parseDir(dirName):
    fileCount = 0
    files = []
    skipdirs = ['console', 'correction', 'dev', 'debug', 'editor', 'tools', 'vgui']
    
    for root, _, fileNames in os.walk(dirName):
        for skipdir in skipdirs:
            if ('materials\\' + skipdir) in root: fileNames.clear()

        for fileName in fileNames:
            if fileName.lower().endswith(INPUT_FILE_EXT):
                fileCount += 1
                filePath = os.path.join(root,fileName)

                if len(files) % 17 == 0 or (len(files) == 0):
                    print(f"  Found {len(files)} %sfiles" % ("" if OVERWRITE_EXISTING_TGA else f"/ {fileCount} "), end="\r")

                if IGNORE_WORLD_CUBEMAPS:
                    numbers = sum(c.isdigit() for c in fileName)
                    dashes = fileName.count('_') + fileName.count('-')
                    if (numbers > 4) and (dashes >= 2) and (fileName.startswith('c')):
                        #if fileName.lower().endswith('.hdr.vtf') or \
                        #os.path.exists(fileName.lower().replace('.vtf', '.hdr.vtf')):
                        continue

                bExists = False
                if not OVERWRITE_EXISTING_TGA:
                    for outExt in OUTPUT_FILE_EXT:
                        if os.path.exists(filePath.replace(INPUT_FILE_EXT, outExt)):
                            bExists = True
                    if bExists:
                        continue

                files.append(filePath)

    return files

fileList = []

if os.path.isfile(PATH_TO_CONTENT_ROOT):
    if(PATH_TO_CONTENT_ROOT.lower().endswith(INPUT_FILE_EXT)):
        fileList.append(PATH_TO_CONTENT_ROOT)
        PATH_TO_CONTENT_ROOT = PATH_TO_CONTENT_ROOT.split("materials", 1)[0]
    else:
        print("~ Invalid file.")
else:
    folderPath = PATH_TO_CONTENT_ROOT
    if not 'materials' in PATH_TO_CONTENT_ROOT \
    and not PATH_TO_CONTENT_ROOT.endswith(INPUT_FILE_EXT) \
    and not PATH_TO_CONTENT_ROOT.rstrip('\\/').endswith('materials'):
        folderPath = os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, 'materials'))
    if os.path.isdir(folderPath):
        print("\n-", folderPath.capitalize())
        print("+ Scanning for%s" % ("" if OVERWRITE_EXISTING_TGA else " unexported"), INPUT_FILE_EXT, "files. This may take a while...")
        fileList.extend(parseDir(folderPath))
    else: print("~ Could not find a /materials/ folder inside this dir.\n")

PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'

def formatVmatDir(localPath):
    if not localPath: return None
    localPath = os.path.normpath(localPath)
    return localPath.replace(PATH_TO_CONTENT_ROOT, '')

erroredFileList = []

for vtfFile in fileList:

    expectOutput = []
    for outExt in OUTPUT_FILE_EXT:
        expectOutput.append(os.path.normpath(vtfFile.replace(INPUT_FILE_EXT, outExt)))

    force_2nd = False
    if(FORCE_SKYBOX_2ND_VTF2TGA and (len(vtf2tga_paths) > 1) and ('skybox' in vtfFile)):
        force_2nd = True # 2nd exe outputs pfm files. use that for hdr skybox files

    for vtf2tga_exe in vtf2tga_paths:
        tag = tags[vtf2tga_paths.index(vtf2tga_exe)]
        try:
            # TODO: custom output
            command = [vtf2tga_exe, "-i", vtfFile]
            result = subprocess.run(command, stdout=subprocess.PIPE)
            #print (result.stdout)

            # if we are forcing on index 1, continue (don't break) even if index 0 got bCreated
            if (force_2nd and (vtf2tga_paths.index(vtf2tga_exe) != 1)):
                continue
            
            if result.returncode == 0: # VTF2TGA reported success
                
                bCreated = False
                
                for outPath in expectOutput:
                    if os.path.exists(outPath):
                        bCreated = True
                        print(f"[{tag}] Sucessfully created: {formatVmatDir(outPath)}")
                        break

                if not bCreated:
                    print(f"[{tag}] uhm...? {formatVmatDir(vtfFile)}")
    
                break # Output file created. Onto the next VTF.
                    

            #else: # VTF2TGA reported failure
            #    print(f"[{tag}] Something went wrong!")

            if not ((len(vtf2tga_paths) > 1) and (vtf2tga_paths.index(vtf2tga_exe) < (len(vtf2tga_paths) - 1))):
                erroredFileList.append(vtfFile)

        except: pass

if erroredFileList:
    print("\tNo vtf2tga could export the following files:")

    for erroredFile in erroredFileList:
        print(formatVmatDir(erroredFile))

    print(f"\tTotal: {len(erroredFileList)} / {len(fileList)}  |  " + "{:.2f}".format((len(erroredFileList)/len(fileList)) * 100) + r" % Error rate\n")

print("\n+ Looks like we are done.")

