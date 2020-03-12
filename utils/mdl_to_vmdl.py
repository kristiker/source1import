# cmd command: python mdl_to_vmdl.py "C:\Program Files (x86)\Steam\steamapps\common\SteamVR\tools\steamvr_environments\content\steamtours_addons\l4d2_converted\models"
# MUST run in the models folder

import re, sys, os

INPUT_FILE_EXT = '.mdl'
OUTPUT_FILE_EXT = '.vmdl'
# this leads to the root of the game folder, i.e. dota 2 beta/content/dota_addons/, make sure to remember the final slash!!
PATH_TO_GAME_CONTENT_ROOT = ""
PATH_TO_CONTENT_ROOT = ""
    
VMDL_BASE = '''<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
{
    m_sMDLFilename = "<mdl>"
}
'''

def text_parser(filepath, separator="="):
    return_dict = {}
    with open(filepath, "r") as f:
        for line in f:
            if not line.startswith("//") or line in ['\n', '\r\n'] or line.strip() == '':
                line = line.replace('\t', '').replace('\n', '')
                line = line.split(separator)
                return_dict[line[0]] = line[1]
    return return_dict

def walk_dir(dirname):
    files = []

    for root, dirs, filenames in os.walk(dirname):
        for filename in filenames:
            if filename.lower().endswith(INPUT_FILE_EXT):
                files.append(os.path.join(root,filename))
            
    return files

abspath = ''
files = []
globalVars = text_parser("global_vars.txt", " = ")
PATH_TO_GAME_CONTENT_ROOT = globalVars["gameContentRoot"]
PATH_TO_CONTENT_ROOT = PATH_TO_GAME_CONTENT_ROOT + sys.argv[1] + "/"
print(PATH_TO_CONTENT_ROOT)

# recursively search all dirs and files
abspath = os.path.abspath(PATH_TO_CONTENT_ROOT)
if os.path.isdir(abspath):
    files.extend(walk_dir(abspath))
#else:
#    if abspath.lower().endswith(INPUT_FILE_EXT):
#        files.append(abspath)

def putl(f, line, indent = 0):
    f.write(('\t' * indent) + line + '\r\n')

def strip_quotes(s):
    return s.strip('"').strip("'")

def fix_path(s):
    return strip_quotes(s).replace('\\', '/').replace('//', '/').strip('/')

def relative_path(s, base):
    base = base.replace(abspath, '')
    base = base.replace(os.path.basename(base), '')

    return fix_path(os.path.basename(abspath) + base + '/' + fix_path(s))


def get_mesh_name(file):
    return os.path.splitext(os.path.basename(fix_path(file)))[0]

if(PATH_TO_GAME_CONTENT_ROOT == ""):
    print("ERROR: Please open vmt_to_vmat in your favorite text editor, and modify PATH_TO_GAME_CONTENT_ROOT to lead to your games content files (i.e. ...\steamvr_environments\content\steamtours_addons\)")
    quit()
    
print('Source 2 VMDL Generator! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.')
print('--------------------------------------------------------------------------------------------------------')

for filename in files:
    out_name = filename.replace(INPUT_FILE_EXT, OUTPUT_FILE_EXT)
    if os.path.exists(out_name): continue

    print('Importing', os.path.basename(filename))

    out = sys.stdout
    
    mdl_path = fix_path(filename.replace(abspath, ""))
    
    with open(out_name, 'w') as out:
        putl(out, VMDL_BASE.replace('<mdl>', mdl_path).replace((' ' * 4), '\t'))
