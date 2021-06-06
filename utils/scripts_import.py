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

SOUNDSCAPES_MANIFEST = Path("scripts/soundscapes_manifest.txt")
SOUND_OPERATORS_FILE = "scripts/sound_operator_stacks.txt" # TODO.....

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
    newsc_path = fs.Output(file.with_suffix('.txt'))
    newsc_path.parent.mkdir(exist_ok=True)

    for key, value in soundscapes.items():
        if isinstance(value, VDFDict):
            new_soundscapes += f"{key}{value.ToStr()}"
        else:
            new_soundscapes += f'{key}\t"{value}"\n'

    with open(newsc_path, 'w') as fp:
        fp.write(new_soundscapes)
    print("+ Saved", fs.LocalDir(newsc_path))
    
    #soundscapes_manifest.add("file", f'scripts/{newsc_path.name}')

def ImportSoundscapeManifest(asset_path: Path):
    "Integ, but with '.vsc' fixup for csgo"

    out_manifest = fs.Output(asset_path)
    out_manifest.parent.mkdir(exist_ok=True)
    with open(asset_path) as old, open(out_manifest, 'w') as out:
        contents = old.read().replace('.vsc', '.txt')
        if False:  # importing to an hla addon fix
            ls = contents.split('{', 1)
            ls[1] = '\n\t"file"\t"scripts/test123.txt"' + ls[1]
            contents = '{'.join(ls)
        out.write(contents)
    
    print("+ Saved manifest", fs.LocalDir(out_manifest))
    return out_manifest

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
    'CHAN_STREAM': 0,#5,		# allocate stream channel from the static or dynamic area
    'CHAN_STATIC': 0,#6,		# allocate channel from the static area 
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

import wave
import contextlib
def _get_wavfile_duration(wave_path):
    with contextlib.closing(wave.open(wave_path,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return frames / float(rate)

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
        if k == 'pitch':  # Normalize pitch
            range=range/100;out_v=out_v/100
        rv[k] = out_v
        if range != 0:
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

op_stacks = {}
def ImportGameSound(asset_path: Path):
    kv = KV.CollectionFromFile(asset_path)
    kv3 = {}

    for gamesound, gs_kv in kv.items():
        
        out_kv = dict(type='src1_3d')
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
    
            elif k == 'channel':  # big ass guess
                out_k, out_v= 'event_type', float(CHAN.get(v, 0))

            elif k in ('volume', 'pitch', 'soundlevel'):
                if rangekv:=_handle_range(k, v):
                    out_kv.update(rangekv)
                    continue

                if k == 'volume':
                    if v == 'VOL_NORM': out_v = 1.0  # aka just continue? (default)
                elif k == 'pitch':
                    if type(v) is str:
                        out_v = PITCH.get(v, 100)
                    # Normalize pitch
                    out_v = out_v / 100
                elif k == 'soundlevel':
                    if type(v) is str:
                        if (out_v:=SNDLVL.get(v)) is None:
                            out_v = 75
                            if v.startswith('SNDLVL_'):
                                try:
                                    out_v = int(v[7:-2])
                                except:
                                    print(v[7:])
                            else: print(v)
            elif k == 'delay_msec': out_k, out_v = 'delay', v/1000
            elif k == 'ignore_occlusion': out_k, out_v = 'occlusion_scale', (1 if not v else 0)#'sa_enable_occlusion'
            elif k == 'operator_stacks':  # this only exists in globul offensif
                ...
                #print("~~~~~ stack")
                op_stacks[v.ToStr()] = op_stacks.get(v.ToStr(), 0) + 1

                if mx:=v.get('update_stack', {}).get('mixer', {}).get('mixgroup'):
                    out_kv['mixgroup'] = mx
                #for opk, opv in v.items():
                #    #input(f"{opk} {opv.ToStr()}")
                #    if opk == 'update_stack':
                #        for up_k, up_v in opv.items():
                #            ...
                            #if isinstance(up_v, dict):
                            #    if mx:=up_v.get('mixgroup'):
                            #        out_kv['mixgroup'] = mx
                # update stack
                    # volume_falloff
                    # {
                    #         input_max       "800"
                    #         input_curve_amount      "0.9"
                    # }
                    # volume_fallof_max/min in out_kv
                continue
            elif k in ('soundentry_version', 'alert', 'hrtf_follow','gamedata',): # skiplist
                continue
            out_kv[out_k] = out_v
        
        kv3[gamesound] = out_kv

    vsndevts_file = EXPORT_CONTENT / "soundevents" / asset_path.relative_to(IMPORT_GAME / "scripts").with_suffix('.vsndevts')
    vsndevts_file.parent.mkdir(parents=True, exist_ok=True)
    with open(vsndevts_file, 'w') as fp:
        fp.write(dict_to_kv3_text(kv3))

    print("+ Saved", vsndevts_file.relative_to(EXPORT_CONTENT))
    return asset_path

if __name__ == '__main__':
    IMPORT_GAME =    Path(r"D:\Games\steamapps\common\Half-Life Alyx\game\csgo")
    EXPORT_CONTENT = Path(r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo")
    EXPORT_GAME =    Path(r"D:\Games\steamapps\common\Half-Life Alyx\game\hlvr_addons\csgo")
    
    # import soundscapes...
    fs = sh.Source("scripts", IMPORT_GAME, EXPORT_GAME)

    for vsc in fs.collect_files(".vsc", ".txt", existing = True, customMatch="soundscapes_*.vsc"):
        ImportSoundscape(vsc)

    for soundscapes_txt in fs.collect_files(".txt", ".txt", existing = True, customMatch="soundscapes_*.txt"):
        if soundscapes_txt.name == SOUNDSCAPES_MANIFEST.name:
            ImportSoundscapeManifest(soundscapes_txt)
            continue
        ImportSoundscape(soundscapes_txt)

    # import game sounds...
    fs = sh.Source("scripts", IMPORT_GAME, EXPORT_CONTENT)

    for file in fs.collect_files(".txt", ".vsndevts", existing = True, customMatch="game_sounds*.txt", customPath=(IMPORT_GAME / 'scripts')):
        ImportGameSound(file)

    quit()
    for k, v in collected.items():
        print(k, v[1])
    for opstack, count in op_stacks.items():
        print()
        print(count)
        print(opstack)

def ImportUpdateResourceRefs(asset_path: Path):
    ...
    # we ported .wavs to vsnds,
    # this func is for other generic scripts to update their resource refs
    # eg. search for each value and see if its a ref and replace each
    # after that just integ