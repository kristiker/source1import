#
# idk if vsc supported
# .OLD_EXT -> .NEW_EXT for content inside files
# csgo soundscapes:
# "wave" ambient\dust2\wind_sand_01.wav" -> "wave" "sounds\ambient\dust2\wind_sand_01.vsnd" 
#
# surfaceprop need processing
#
#
#
#
#
import py_shared as sh
from pathlib import Path
PATH_TO_CONTENT_ROOT = r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo"#r"D:\Games\steamapps\common\Half-Life Alyx\game\csgo"
PATH_TO_NEW_CONTENT_ROOT = r"D:\Games\steamapps\common\Half-Life Alyx\game\hlvr_addons\csgo"

#fs = sh.Source("scripts", PATH_TO_CONTENT_ROOT, PATH_TO_CONTENT_ROOT)
#fs.arg_parser.add_argument('-x', help="Force aaa.", action="store_true")

#vscSoundscapeFiles = fs.collect_files(".vsc", ".txt", existing = True, customMatch="soundscapes_*.vsc")

fs = sh.Source("materials", PATH_TO_CONTENT_ROOT, PATH_TO_CONTENT_ROOT)

skyfacecollections = fs.collect_files(".json", ".vmat", existing = False, customPath = Path ( r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo/materials/skybox/legacy_faces/" ) )

for x in skyfacecollections:
    #print(fs.SCRIPT_SCOPE, fs.IN_SUBSCOPE)
    #print(fs.LocalDir("something/materials/skybox/legacy_faces/lol/lol.xdx"))
    print(x)
    