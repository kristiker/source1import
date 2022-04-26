import shared.base_utils2 as sh
from pathlib import Path
from shared.keyvalues1 import KV, VDFDict

OVERWRITE_SCRIPTS = True

scripts = Path('scripts')
SOUNDSCAPES_MANIFEST = scripts / "soundscapes_manifest.txt"
SURFACEPROPERTIES_MANIFEST = scripts / "surfaceproperties_manifest.txt"

def main():
    sh.import_context['dest'] = sh.EXPORT_GAME
    print("Importing Scripts!")

    # soundscapes vsc...
    for soundscapes_vsc in sh.collect("scripts", ".vsc", ".txt", OVERWRITE_SCRIPTS, match="soundscapes_*.vsc"):
        ImportSoundscape(soundscapes_vsc)

    # soundscapes txt... (also manifest)
    for soundscapes_txt in sh.collect("scripts", ".txt", ".txt", OVERWRITE_SCRIPTS, match="soundscapes_*.txt"):
        if soundscapes_txt.name == SOUNDSCAPES_MANIFEST.name:
            ImportSoundscapeManifest(soundscapes_txt)
            continue
        ImportSoundscape(soundscapes_txt)

    # game sounds...
    sh.import_context['dest'] = sh.EXPORT_CONTENT

    for file in (sh.src(scripts)).glob('**/game_sounds*.txt'):
        if file.name != 'game_sounds_manifest.txt':
            ImportGameSounds(file)

    if (boss:=sh.src(scripts)/'level_sounds_general.txt').is_file():
        ImportGameSounds(boss)

    # surfaceproperties...
    for surfprop_txt in sh.collect("scripts", ".txt", ".txt", OVERWRITE_SCRIPTS, match="surfaceproperties*.txt"):
        if surfprop_txt.name == SURFACEPROPERTIES_MANIFEST.name:
            continue
        ImportSurfaceProperties(surfprop_txt)

    print("Looks like we are done!")

def fix_wave_resource(old_value):
    soundchars = '*?!#><^@~+)(}$' + '`' # public\soundchars.h
    old_value = old_value.strip(soundchars)

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
    for key, value in soundscapes.items():
        if isinstance(value, VDFDict):
            new_soundscapes += f"{key}{value.ToStr()}"
        else:
            new_soundscapes += f'{key}\t"{value}"\n'

    newsc_path = sh.output(file, '.txt')
    newsc_path.parent.MakeDir()
    sh.write(new_soundscapes, newsc_path)
    print("+ Saved", newsc_path.local)
    return newsc_path
    #soundscapes_manifest.add("file", f'scripts/{newsc_path.name}')

def ImportSoundscapeManifest(asset_path: Path):
    "Integ, but with '.vsc' fixup for csgo"
    
    out_manifest = sh.output(asset_path)
    out_manifest.parent.MakeDir()

    with open(asset_path) as old, open(out_manifest, 'w') as out:
        contents = old.read().replace('.vsc', '.txt').replace('soundscaples_manifest', 'soundscapes_manifest')
        if False:  # importing to an hla addon fix
            ls = contents.split('{', 1)
            ls[1] = '\n\t"file"\t"scripts/test123.txt"' + ls[1]
            contents = '{'.join(ls)
        out.write(contents)

    print("+ Saved manifest file", out_manifest.local)
    return out_manifest

from shared.keyvalues3 import dict_to_kv3_text

"""
channel ['CHAN_VOICE']
volume [1, 0.3, '0.4, 0.7']
soundlevel ['SNDLVL_NORM', 0]
pitch ['PITCH_NORM', 150]
wave ['common/null.wav']
rndwave [VDFDict([('wave', '~player/footsteps/slosh1.wav'), ('wave', '~player/footsteps/slosh2.wav'), ('wave', '~player/footsteps/slosh3.wav'), ('wave', '~player/footsteps/slosh4.wav')])]
"""
def ImportGameSounds(asset_path: Path):
    "scripts/game_sounds*.txt -> [sounds/*/major.minor.sound]"
    game_sound_folder = sh.EXPORT_CONTENT / "sounds" / asset_path.stem.removeprefix('game_sounds_')
    game_sound_folder.MakeDir()
    PITCH = {
        'PITCH_NORM': 100,
        'PITCH_LOW': 95,
        'PITCH_HIGH': 120,
    }
    def _handle_range(k, v):
        if not (type(v) is str and ',' in v):
            return
        try:
            mm = tuple(v.split(',', 1))
            min, max = float(mm[0]), float(mm[1])
        except Exception:
            return
        else:
            out_v = min+max / 2
            range = out_v - min
            if k == 'pitch':  # Normalize pitch
                range=range/100;out_v=out_v/100
            return out_v, range
    kv = KV.CollectionFromFile(asset_path)
    for gamesound, gs_data in kv.items(): # "weapon.fire", {}
        sound_file = game_sound_folder / f'{gamesound}.sound'
        sound_data = dict(
            ui = False,
            volume = 1.0,
            volumerandom = 0.0,
            pitch = 1.0,
            pitchrandom = 0.0,
            distancemax = 2000.0,
            sounds = [],
            selectionmode = "0",
        )
        if not OVERWRITE_SCRIPTS and sound_file.exists():
            continue
        for (_, k), v in gs_data.items(indexed_keys=True):
            ## Turns out you can have multiple 'wave' in counter strike global offensive!
            # instead of using rndwave {} !!
            if k == 'wave':
                if "common/null" in v:
                    continue
                sound_data['sounds'].append(fix_wave_resource(v))    
            elif k == 'rndwave':
                for rndwave_k, rndwave_v in v.items(indexed_keys=True):
                    if rndwave_k[1] != 'wave':
                        continue
                    res = fix_wave_resource(rndwave_v)
                    if res != 'sounds/common/null.vsnd':
                        sound_data['sounds'].append(res)
            elif k in ('volume', 'pitch'):
                if range:=_handle_range(k, v):
                    sound_data[k] = range[0]
                    sound_data[k+'random'] = range[1]
                    continue
                if k == 'volume':
                    if v == 'VOL_NORM':
                        continue
                    sound_data[k] = float(v)
                elif k == 'pitch':
                    if type(v) is str:
                        v = PITCH.get(v, 100)
                    # Normalize pitch
                    sound_data[k] = v / 100
            elif k == 'soundlevel':
                ...
        sh.write(dict_to_kv3_text(dict(data=sound_data)), sound_file)
        print("+ Saved", sound_file.local)

vsurf_base_params = {
    'physics': ('density','elasticity','friction','dampening','thickness',),
    'Sounds':('bulletimpact','scraperough','scrapesmooth','impacthard','impactsoft','rolling','break','strain',),
    'audioparams': ('audioreflectivity','audiohardnessfactor','audioroughnessfactor','scrapeRoughThreshold','impactHardThreshold',),
}

class CaseInsensitiveKey(str):
    def __hash__(self): return hash(self.lower())
    def __eq__(self, other: str): return self.lower() == other.lower()
class CaseInsensitiveDict(dict):
    def __setitem__(self, key, value): super().__setitem__(CaseInsensitiveKey(key), value)
    def __getitem__(self, key): return super().__getitem__(CaseInsensitiveKey(key))

def ImportSurfaceProperties(asset_path: Path):
    "scripts/surfaceproperties*.txt -> surfaces/*/name.surface"
    
    surface_folder = sh.EXPORT_CONTENT / "surfaces" / asset_path.stem.removeprefix('surfaceproperties').lstrip("_")
    surface_folder.MakeDir()

    kv = KV.CollectionFromFile(asset_path)

    for surface, properties in {**kv}.items():
        surface_file = surface_folder / f'{surface}.surface'
        surface_data = CaseInsensitiveDict({
            CaseInsensitiveKey("Friction"): 0.5,
            CaseInsensitiveKey("Elasticity"): 0.5,
            CaseInsensitiveKey("Density"): 0.5,
            CaseInsensitiveKey("Thickness"): 0.5,
            CaseInsensitiveKey("Dampening"): 0.0,
            CaseInsensitiveKey("BounceThreshold"): 0.0,
            CaseInsensitiveKey("ImpactEffects"): CaseInsensitiveDict({
                CaseInsensitiveKey("Bullet"): [],
                CaseInsensitiveKey("BulletDecal"): [],
                CaseInsensitiveKey("Regular"): [],
            }),
            CaseInsensitiveKey("Sounds"): CaseInsensitiveDict({
                CaseInsensitiveKey("ImpactSoft"): "",
                CaseInsensitiveKey("ImpactHard"): "",
                CaseInsensitiveKey("RoughScrape"): "",
                CaseInsensitiveKey("FootLeft"): "",
                CaseInsensitiveKey("FootRight"): "",
                CaseInsensitiveKey("FootLaunch"): "",
                CaseInsensitiveKey("FootLand"): "",
        }),
            CaseInsensitiveKey("basesurface"): "surfaces/default.surface",
            CaseInsensitiveKey("description"): "",
        })
        for key, value in properties.items():
            key = {'stepleft':'footleft','stepright':'footright','base':'basesurface'}.get(key, key)
            if key in surface_data: # needs to be a counterpart
                if key == "basesurface":
                    value = f"{surface_folder.relative_to(sh.EXPORT_CONTENT).as_posix()}/{value}.surface"
                surface_data[key] = value
            elif key in surface_data["Sounds"]:
                surface_data["Sounds"][key] = value

        sh.write(dict_to_kv3_text(dict(data=surface_data)), surface_file)
        print("+ Saved", surface_file.local)

    return surface_folder

if __name__ == '__main__':
    sh.parse_argv()
    main()  

def ImportUpdateResourceRefs(asset_path: Path):
    ...
    # this func is for other generic scripts to update their resource refs
    # eg. search for each value and see if its a ref and replace each
    # after that just integ
def ImportUpdateResourceRefs_ProcessKVEscapeSeqs():...