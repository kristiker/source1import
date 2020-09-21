import re, sys, os

OVERWRITE_EXISTING_VMDL = False

INPUT_FILE_EXT = '.mdl'
OUTPUT_FILE_EXT = '.vmdl'

PATH_TO_CONTENT_ROOT = r""
    
VMDL_BASE = '''<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
{
    m_sMDLFilename = "<mdl>"
}
'''

print('Source 2 VMDL Generator! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.')
print('------------------------------------------------------------------------------')

fileList = []

currentDir = os.path.dirname(os.path.realpath(__file__)) #os.getcwd()
PATH_TO_CONTENT_ROOT = r""

if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2): PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        while not PATH_TO_CONTENT_ROOT:
            c = input('Type in the directory of the .mdl file(s) (enter to use current directory, q to quit).: ') or currentDir
            if not os.path.isdir(c) and not os.path.isfile(c):
                if c in ('q', 'quit', 'exit', 'close'): quit()
                print('Could not find file or directory.')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')

def parseDir(dirName):
    fileCount = 0
    files = []
    for root, _, fileNames in os.walk(dirName):
        if "models\\editor" in root: fileNames.clear()
        for fileName in fileNames:
            if fileName.lower().endswith(INPUT_FILE_EXT):
                fileCount += 1
                filePath = os.path.join(root,fileName)
                if len(files) % 17 == 0 or (len(files) == 0): print(f"  Found {len(files)} %sfiles" % ("" if OVERWRITE_EXISTING_VMDL else f"/ {fileCount} "), end="\r")
                if not OVERWRITE_EXISTING_VMDL:
                    if os.path.exists(filePath.replace(INPUT_FILE_EXT, OUTPUT_FILE_EXT)): continue
                files.append(filePath)
    return files

if os.path.isfile(PATH_TO_CONTENT_ROOT): # input is a single file
    if(PATH_TO_CONTENT_ROOT.lower().endswith(INPUT_FILE_EXT)):
        fileList.append(PATH_TO_CONTENT_ROOT)
        PATH_TO_CONTENT_ROOT = PATH_TO_CONTENT_ROOT.split("models", 1)[0]
    else:
        print("~ Invalid file.")
else:
    folderPath = PATH_TO_CONTENT_ROOT
    if not 'models' in PATH_TO_CONTENT_ROOT \
    and not PATH_TO_CONTENT_ROOT.endswith(INPUT_FILE_EXT) \
    and not PATH_TO_CONTENT_ROOT.rstrip('\\/').endswith('models'):
        folderPath = os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, 'models'))
    if os.path.isdir(folderPath):
        print("\n-", folderPath.capitalize())
        print("\n+ Scanning for%s" % ("" if OVERWRITE_EXISTING_VMDL else " unexported"), INPUT_FILE_EXT, "files. This may take a while...")
        fileList.extend(parseDir(folderPath))
        PATH_TO_CONTENT_ROOT = PATH_TO_CONTENT_ROOT.split("models", 1)[0] # join 
        # ^^ this is bad. rework PATH_TO_CONTENT_ROOT
    else:
        print("~ Could not find a /models/ folder inside this dir.")

PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'

def putl(f, line, indent = 0):
    f.write(('\t' * indent) + line + '\r\n')

def strip_quotes(s):
    return s.strip('"').strip("'")

def fix_path(s):
    return strip_quotes(s).replace('\\', '/').replace('//', '/').strip('/')

##################################################################
# Main function, loop through every .mdl
#
for mdl_path in fileList:
    out_file = mdl_path.replace(INPUT_FILE_EXT, OUTPUT_FILE_EXT)
    mdl_file = fix_path(mdl_path.replace(PATH_TO_CONTENT_ROOT, ""))

    print('Importing', mdl_file)

    out = sys.stdout

    with open(out_file, 'w') as out:
        putl(out, VMDL_BASE.replace('<mdl>', mdl_file).replace((' ' * 4), '\t'))
