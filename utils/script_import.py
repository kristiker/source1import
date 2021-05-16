#
# .OLD_EXT -> .NEW_EXT for content inside files
# csgo soundscapes:
# "wave" ambient\dust2\wind_sand_01.wav" -> "wave" "sounds\ambient\dust2\wind_sand_01.vsnd" 
#
# surfaceprop need processing
if __name__ != "__main__":
    from utils.shared import base_utils as sh
    from pathlib import Path
    from utils.shared.keyvalues1 import KV, VDFDict

from shared import base_utils as sh
from pathlib import Path
from shared.keyvalues1 import KV, VDFDict


PATH_TO_CONTENT_ROOT = r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo" #r"D:\Games\steamapps\common\Half-Life Alyx\game\csgo"
PATH_TO_NEW_CONTENT_ROOT = r"D:\Games\steamapps\common\Half-Life Alyx\game\hlvr_addons\csgo"


def fix_wave_resource(old_value):
    old_value = old_value.lstrip('~')
    return f"sounds/{Path(old_value).with_suffix('.vsnd').as_posix()}"

def recurse(kv, find_key, fixup_func):
    for key, value in kv.iteritems(indexed_keys=True):
        if isinstance(value, VDFDict):
            recurse(value, find_key, fixup_func)
        elif key[1] == find_key:
            kv[key] = fixup_func(value)

def ImportSoundscape(file):
    soundscapes = KV.CollectionFromFile(file)

    for soundscape, keyvalues in soundscapes.iteritems(indexed_keys=True):
        print(soundscape)
        for key, value in keyvalues.iteritems(indexed_keys=True):
            if not isinstance(value, VDFDict):
                continue
            recurse(value, 'wave', fix_wave_resource)
    
    new_soundscapes = ''
    newsc_path = file.with_suffix('.txt')

    for key, value in soundscapes.items():
        if isinstance(value, VDFDict):
            new_soundscapes += f"{key}{value.ToStr()}"
        else:
            new_soundscapes += f'{key}\t"{value}"\n'

    with open(newsc_path, 'w') as fp:
        fp.write(new_soundscapes)
    
    soundscapes_manifest.add("file", newsc_path.name)

fs = sh.Source("scripts", PATH_TO_NEW_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT)

vscSoundscapeFiles = fs.collect_files(".vsc", ".txt", existing = True, customMatch="soundscapes_*.vsc")

manifest_file = fs.SEARCH_PATH / "soundscapes_manifest.txt"
soundscapes_manifest = KV.FromFile(manifest_file)

for file in vscSoundscapeFiles:
    print(file)
    ImportSoundscape(file)

with open(manifest_file, 'w') as fp:
    fp.write(str(soundscapes_manifest))
