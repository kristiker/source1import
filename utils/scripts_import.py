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
    print("+ Saved", fs.LocalDir(newsc_path))
    
    soundscapes_manifest.add("file", f'scripts/{newsc_path.name}')

fs = sh.Source("scripts", PATH_TO_NEW_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT)

manifest_file = fs.SEARCH_PATH / "soundscapes_manifest.txt"
soundscapes_manifest = KV.FromFile(manifest_file)

#for file in fs.collect_files(".vsc", ".txt", existing = True, customMatch="soundscapes_*.vsc"):
#    ImportSoundscape(file)

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

from particles_import import dict_to_kv3_text
if __name__ is None:
    from utils.particles_import import dict_to_kv3_text

collected = {}
def collect_dev(k, v):
    
    v_evauluated = eval(repr(v))
    v_type = type(v_evauluated)

    c = collected.setdefault(k, ([], []))
    if v_type not in c[0]:
        c[0].append(v_type)
        c[1].append(v_evauluated)

CHAN = {
    'CHAN_AUTO': 0,
    'CHAN_WEAPON': 1,
    'CHAN_VOICE': 2,
    'CHAN_ITEM': 3,
    'CHAN_BODY': 4,
    'CHAN_STREAM': 5,		# allocate stream channel from the static or dynamic area
    'CHAN_STATIC': 6,		# allocate channel from the static area 
}
SNDLVL = {
    'SNDLVL_NONE': 0,
    'SNDLVL_25dB': 25,
    'SNDLVL_30dB': 30,
    'SNDLVL_35dB': 35,
    'SNDLVL_40dB': 40,
    'SNDLVL_45dB': 45,
    'SNDLVL_50dB': 50,
    'SNDLVL_55dB': 55,
    'SNDLVL_IDLE': 60,
    'SNDLVL_TALKING': 60,
    'SNDLVL_60dB': 60,
    'SNDLVL_65dB': 65,
    'SNDLVL_STATIC': 66,
    'SNDLVL_70dB': 70,
    'SNDLVL_NORM': 75,
    'SNDLVL_75dB': 75,
    'SNDLVL_80dB': 80,
    'SNDLVL_85dB': 85,
    'SNDLVL_90dB': 90,
    'SNDLVL_95dB': 95,
    'SNDLVL_100dB': 100,
    'SNDLVL_105dB': 105,
    'SNDLVL_120dB': 120,
    'SNDLVL_130dB': 130,
    'SNDLVL_GUNFIRE': 140,
    'SNDLVL_140dB': 140,
    'SNDLVL_150dB': 150,
}
PITCH = {
    'PITCH_NORM': 100,
    'PITCH_LOW': 95,
    'PITCH_HIGH': 120,
}

#import wave
#import contextlib
#fname = '/tmp/test.wav'
#with contextlib.closing(wave.open(fname,'r')) as f:
#    frames = f.getnframes()
#    rate = f.getframerate()
#    duration = frames / float(rate)
#    print(duration)
def _handle_range(k, v):
    if not (type(v) is str and ',' in v):
        return
    try:
        mm = tuple(v.split(',', 1))
        min, max = float(mm[0]), float(mm[1])
    except: return
    else:
        rv = {}
        out_v = min+max / 2
        range = out_v - min
        rv[k] = out_v
        rv[k + '_rand_min'] = -range
        rv[k + '_rand_max'] = range
        return rv

"""
channel ['CHAN_VOICE']
volume [1, 0.3, '0.4, 0.7']
soundlevel ['SNDLVL_NORM', 0]
pitch ['PITCH_NORM', 150]
wave ['common/null.wav']
soundentry_version [2]
operator_stacks [VDFDict([('start_stack', VDFDict([('import_stack', 'CS_limit_start')])), ('update_stack', VDFDict([('import_stack', 'CS_update_foley'), ('mixer', VDFDict([('mixgroup', 'FoleyWeapons')]))]))])]
compatibilityattenuation [1.0]
rndwave [VDFDict([('wave', '~player/footsteps/slosh1.wav'), ('wave', '~player/footsteps/slosh2.wav'), ('wave', '~player/footsteps/slosh3.wav'), ('wave', '~player/footsteps/slosh4.wav')])]
precache_file ['scripts/game_sounds_fbihrt.txt']
gamedata [VDFDict([('priority', 'Interesting')])]
preload_file ['scripts/game_sounds_radio.txt']
autocache_file ['sound/music/valve_csgo_01/game_sounds_music.txt']
delay_msec [70]
ignore_occlusion [1]
alert [1]
hrtf_follow [1]
"""

def ImportGameSound(asset_path: Path):
    print(fs.LocalDir(asset_path))
    kv = KV.CollectionFromFile(asset_path)
    kv3 = {}

    for gamesound, gs_kv in kv.items():
        
        out_kv = {}
        for (i, k), v in gs_kv.items(indexed_keys=True):
            out_k, out_v = k, v
            collect_dev(k, v)
            ## Turns out you can have multiple 'wave' in counter strike global offensive!
            # instead of using rndwave {} !! Fucking volvo
            if k == 'wave':
                if i != 0:
                    if i == 1:
                        out_kv['vsnd_files'] = [out_kv['vsnd_files'], fix_wave_resource(v)]
                    else:
                        out_kv['vsnd_files'].append(fix_wave_resource(v))
                    continue
                out_k, out_v = 'vsnd_files', fix_wave_resource(v)
    
            elif k == 'rndwave':
                out_k, out_v = 'vsnd_files', []
                for rndwave_k, rndwave_v in v.items(indexed_keys=True):
                    if rndwave_k[1] != 'wave':
                        continue
                    out_v.append(fix_wave_resource(rndwave_v))
    
            elif k in ('volume', 'pitch', 'soundlevel'):
                if rangekv:=_handle_range(k, v):
                    out_kv.update(rangekv)
                    continue

                if k == 'pitch':
                    if type(v) is str:
                        out_v = PITCH.get(v, 100)
                    # Normalize pitch
                    out_v = out_v / 100
                elif k == 'soundlevel':
                    if type(v) is str:
                        out_v = SNDLVL.get(v, 75)
                        if SNDLVL.get(v) is None:
                            print(v)
            elif k == 'delay_msec': out_k, out_v = 'delay', v/1000
            elif k == 'ignore_occlusion': out_k, out_v = 'occlusion_scale', (1 if not v else 0)#'sa_enable_occlusion'
            elif k == 'operator_stacks':
                print("~~~~~ stack")
                for opk, opv in v.items():
                    input(f"{opk} {opv.ToStr()}")
                    # update stack
                    # volume_falloff
                    # {
                    #         input_max       "800"
                    #         input_curve_amount      "0.9"
                    # }
                    # volume_fallof_max/min in out_kv
            out_kv[out_k] = out_v
        
        kv3[gamesound] = out_kv

    
    #input(dict_to_kv3_text(kv3))
    return asset_path


IMPORT_GAME = Path(r'D:\Games\steamapps\common\Half-Life Alyx\game\csgo')
EXPORT_CONTENT = r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo"

fs = sh.Source("scripts", IMPORT_GAME, EXPORT_CONTENT)


for file in fs.collect_files(".txt", ".vsndevts", existing = True, customMatch="game_sounds*.txt", customPath=(IMPORT_GAME / 'scripts')):
    ImportGameSound(file)

for k, v in collected.items():
    print(k, v[1])

def ImportUpdateResourceRefs(asset_path: Path):
    ...
    # we ported .wavs to vsnds,
    # this func is for other generic scripts to update their resource refs
    # eg. search for each value and see if its a ref and replace each
    # after that just integ