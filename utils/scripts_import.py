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
    soundchars = '*?!#><^@~+)(}$' # public\soundchars.h
    for char in soundchars:
        while old_value[0] == char:
            old_value = old_value[1:]

    return f"sounds/{Path(old_value).with_suffix('.vsnd').as_posix()}"

def ImportSoundscape(file: Path):
    soundscapes = KV.CollectionFromFile(file)

    fixups = {'wave': fix_wave_resource}

    def recursively_fixup(kv: VDFDict):
        for key, value in kv.iteritems(indexed_keys=True):
            if isinstance(value, VDFDict):
                recursively_fixup(value)
            elif (k:=key[1]) in fixups:
                kv[key] = fixups[k](value)

    recursively_fixup(soundscapes)
    
    new_soundscapes = ''
    newsc_path = file.with_suffix('.txt')

    for key, value in soundscapes.items():
        if isinstance(value, VDFDict):
            new_soundscapes += f"{key}{value.ToStr()}"
        else:
            new_soundscapes += f'{key}\t"{value}"\n'

    with open(newsc_path, 'w') as fp:
        fp.write(new_soundscapes)
    print("Saved", newsc_path)
    
    soundscapes_manifest.add("file", f'scripts/{newsc_path.name}')

fs = sh.Source("scripts", PATH_TO_NEW_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT)

vscSoundscapeFiles = fs.collect_files(".vsc", ".txt", existing = True, customMatch="soundscapes_*.vsc")

manifest_file = fs.SEARCH_PATH / "soundscapes_manifest.txt"
soundscapes_manifest = KV.FromFile(manifest_file)

for file in vscSoundscapeFiles:
    print(file)
    ImportSoundscape(file)

with open(manifest_file, 'w') as fp:
    fp.write(str(soundscapes_manifest))

# in soundscapes_*.txt: soundmixer <string>
# ->
# Selects a custom soundmixer. Soundmixers manage the priority and volume of groups of sounds; create new ones in scripts\soundmixers.txt (ALWAYS use Default_Mix as a template).
# 
# "quiet"
# {
# 	"soundmixer"	"Citadel_Dialog_Only"
# 
# 	...
# }

def ImportUpdateResourceRefs(asset_path: Path):
    ...
    # we ported .wavs to vsnds,
    # this func is for other generic scripts to update their resource refs
    # eg. search for each value and see if its a ref and replace each
    # after that just integ