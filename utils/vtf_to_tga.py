import sys, os, re
import subprocess
import threading, multiprocessing
import shutil
from pathlib import Path
import py_shared as sh 

# https://developer.valvesoftware.com/wiki/VTF2TGA
# Runs vtf2tga.exe on every vtf file
# Same thing as `VTFCmd.exe -folder "<dir>\materials\*.vtf" -recurse`


# Path to content root, before /materials/
PATH_TO_CONTENT_ROOT = r""
PATH_TO_NEW_CONTENT_ROOT = r""


fs = sh.Source("materials", PATH_TO_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT)

OVERWRITE = False
IGNORE_WORLD_CUBEMAPS = True

MULTITHREAD = True

currentDir = os.path.dirname(os.path.realpath(__file__)) #os.getcwd()

IN_EXT = ".vtf"
VTEX_PARAMS_EXT = ".txt"

OUT_EXT_LIST = [
    '.tga',     # LDR
    '.pfm',     # HDR
]

OUT_NAME_ENDS = [
    "",     # default
    "up",   # CUBEMAP FACE UP (+ dn, lf, rt, ft, bk)
    "000",  # GIF FRAME 0 (+ 001, 002, 003, ...)
    "_z000" # ??? LAYER 0 (+ _z001, _z002, _z003, ...)
]

def OutputList(path: Path, with_suffix = False) -> list:
    """ Return list with all the possible output names
    """ 
    for name in OUT_NAME_ENDS:
        outPath = Path(path.parent) / Path(path.stem + name)
        if not with_suffix: yield outPath
        for ext in OUT_EXT_LIST:
            yield Path(str(outPath) + ext) #.with_suffix(ext)

# if there is one, force skybox vtfs to run on the 2nd row executable __very specific__ 
FORCE_SKYBOX_2ND_VTF2TGA = True

# Add your vtf2tga.exe here. Accepts full (C:/) and relative paths (../). Priority is top to bottom
vtf2tga_paths = [
    r"../vtf2tga/2013/vtf2tga.exe",
    r"../vtf2tga/csgo/vtf2tga.exe", # FORCE_SKYBOX_2ND_VTF2TGA
    r"C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\bin\vtf2tga.exe",
    #r"C:\Program Files (x86)\Steam\steamapps\common\Source SDK Base 2013 Multiplayer\bin\vtf2tga.exe",
    #r"D:\Games\steamapps\common\Team Fortress 2\bin\vtf2tga.exe",
    #r"..\vtf2tga\tf2\vtf2tga.exe",
    #r"..\vtf2tga\hl2\vtf2tga.exe",
]
tags = []

for vtf2tga_path in vtf2tga_paths:
    full_path = Path(vtf2tga_path.replace("..", currentDir))

    if full_path.exists():
        print("+ Using:", full_path)
        vtf2tga_paths[vtf2tga_paths.index(vtf2tga_path)] = full_path
        tags.append(os.path.basename(vtf2tga_path.replace('vtf2tga', '').replace('.exe', '').replace('bin', '').strip('/\\.')))
    else:
        print("~ Invalid vtf2tga path:", full_path)
        vtf2tga_paths[vtf2tga_paths.index(vtf2tga_path)] = None

if not any(vtf2tga_paths):
    print(f"No valid vtf2tga.exe was found. Please open {os.path.basename(__file__)} and verify your paths.")
    quit(-1)

erroredFileList = []
threads = []
totalFiles = 0
MAX_THREADS = min(multiprocessing.cpu_count() + 2, 10)
semaphore = multiprocessing.BoundedSemaphore(value=MAX_THREADS)

def vtf_import(vtfFile, expectOutput, force_2nd, vtf2tga_paths):
    semaphore.acquire()
    global totalFiles, erroredFileList

    for vtf2tga_exe in vtf2tga_paths:
        tag = tags[vtf2tga_paths.index(vtf2tga_exe)]

        #print(fs.Output(vtfFile.parent))
        command = [vtf2tga_exe, "-i", vtfFile] #, "-o", fs.Output(vtfFile.parent)
        result = subprocess.run(command, stdout=subprocess.PIPE) #
        #print (result.stdout.decode("utf-8"))

        # if we are forcing on index 1, continue (don't break) even if index 0 got bCreated
        if (force_2nd and (vtf2tga_paths.index(vtf2tga_exe) != 1)):
            continue
        
        if result.returncode == 0: # VTF2TGA reported success

            bCreated = False
            for outPath in expectOutput:
                if not outPath.exists(): continue
                bCreated = True
                totalFiles +=1
                print(f"[{tag}] Sucessfully created: {fs.LocalDir(outPath)}")
    
                # shitty workaround to vtf2tga not being able to output properly
                movePath = fs.Output(outPath)
                os.makedirs(movePath.parent, exist_ok=True) #fs.MakeDir(movePath)
                shutil.move(outPath, movePath)

            if not bCreated:
                print(f"[{tag}] uhm...? {fs.LocalDir(vtfFile)}")

            break # Output file created. Onto the next VTF.

        #else: # VTF2TGA reported failure
        #    print(f"[{tag}] Something went wrong!", result.stdout)

        if not ((len(vtf2tga_paths) > 1) and (vtf2tga_paths.index(vtf2tga_exe) < (len(vtf2tga_paths) - 1))):
            erroredFileList.append(vtfFile)

    semaphore.release()

# https://developer.valvesoftware.com/wiki/Vtex_compile_parameters
def txt_import(txtFile):
    transl_table = {
        "clamps": "clampu",
        "clampt": "clampv",
        "clampu": "clampw",
        "nocompress": "nocompress",
        "nolod": "nolod",
        "maxwidth": "maxres",
        "maxheight": "maxres",
        #"": "picmip0res",
        #"maxheight_360": "maxresmobile",
        #"maxwidth_360": "maxresmobile",
        "nomip": "nomip",
        "invertgreen": "legacy_source1_inverted_normal",
        #"": "brightness",
        #"": "brightness_offset",
    }

    with open(txtFile, 'r+') as fp:
        oldLines = fp.readlines()
        if "settings" in oldLines[0]: return
        fp.seek(0)
        fp.truncate()
        fp.write("\"settings\"\n{\n")
        for line in oldLines:
            key, value = re.split(r'\s', line, maxsplit=1)
            key, value = key.strip('"'), value.strip().strip('"')
            new_key = transl_table.get(key)
            if not new_key:
                fp.write(f"\t// \"{key}\"\t\t\"{value}\"\n") # comment it
            else:
                fp.write(f"\t\"{new_key}\"\t\t\"{value}\"\n")
        fp.write("}")

def main():

    vtfFileList = fs.collect_files(IN_EXT, OUT_EXT_LIST, existing = OVERWRITE, outNameRule = OutputList)
    txtFileList = fs.collect_files(VTEX_PARAMS_EXT, VTEX_PARAMS_EXT, existing = True)

    for vtfFile in vtfFileList:
        if threading.active_count() > (multiprocessing.cpu_count()) *15:
            print("Chief, there's a prob with your multithread code")
        
        if IGNORE_WORLD_CUBEMAPS:
            s_vtfFile = str(vtfFile.name)
            numbers = sum(c.isdigit() for c in s_vtfFile)
            dashes = s_vtfFile.count('_') + s_vtfFile.count('-')
            if (numbers > 4) and (dashes >= 2) and (s_vtfFile.startswith('c')):
                #if fileName.lower().endswith('.hdr.vtf') or \
                #os.path.exists(fileName.lower().replace('.vtf', '.hdr.vtf')):
                continue

        expectOutput = OutputList(vtfFile, True)
        force_2nd = False
        if(FORCE_SKYBOX_2ND_VTF2TGA and (len(vtf2tga_paths) > 1) and ('skybox' in str(vtfFile))):
            force_2nd = True # 2nd exe outputs pfm files. use that for hdr skybox files

        if MULTITHREAD:
            semaphore.acquire() # blocking=True
            threads.append(threading.Thread(target=vtf_import,  args=(vtfFile, expectOutput, force_2nd, vtf2tga_paths)))
            startThread = threads[-1]
            startThread.start()
            semaphore.release()
        else:
            vtf_import(vtfFile, expectOutput, force_2nd, vtf2tga_paths)

    for txtFile in txtFileList:
        print(f"Found vtex compile param file {txtFile}")
        #txt_import() blah blah

    for unfinished_thread in threads:
        unfinished_thread.join() # wait for the final threads to finish

    if erroredFileList:
        print("\tNo vtf2tga could export the following files:")

        for erroredFile in erroredFileList:
            print(fs.LocalDir(erroredFile))

        print(f"\tTotal: {len(erroredFileList)} / {len(vtfFileList)}  |  " + "{:.2f}".format((len(erroredFileList)/len(vtfFileList)) * 100) + f" % Error rate\n")

    print("\n+ Looks like we are done.")
