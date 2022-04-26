import shared.base_utils2 as sh
from pathlib import Path
from shared.keyvalues1 import KV, VDFDict
from shared.keyvalues3 import dict_to_kv3_text
import itertools

OVERWRITE_ASSETS = False

scripts = Path('scripts')
SOUNDSCAPES_MANIFEST = scripts / "soundscapes_manifest.txt"
SURFACEPROPERTIES_MANIFEST = scripts / "surfaceproperties_manifest.txt"

soundscapes = Path('soundscapes')
sounds = Path('sounds')
surfaces = Path('surfaces')

def main():
    sh.import_context['dest'] = sh.EXPORT_CONTENT
    print("Importing Scripts!")

    for soundscape_collection in itertools.chain(
        (sh.src(scripts)).glob('**/soundscapes_*.vsc'),
        (sh.src(scripts)).glob('**/soundscapes_*.txt')
    ):
        if soundscape_collection.name == SOUNDSCAPES_MANIFEST.name:
            continue
        ImportSoundscape(soundscape_collection)

    for file in (sh.src(scripts)).glob('**/game_sounds*.txt'):
        if file.name != 'game_sounds_manifest.txt':
            ImportGameSounds(file)

    if (boss:=sh.src(scripts)/'level_sounds_general.txt').is_file():
        ImportGameSounds(boss)

    # surfaceproperties...
    for surfprop_txt in (sh.src(scripts)).glob('**/surfaceproperties*.txt'):
        if surfprop_txt.name == SURFACEPROPERTIES_MANIFEST.name:
            continue
        ImportSurfaceProperties(surfprop_txt)

    print("Looks like we are done!")

def fix_wave_resource(old_value):
    soundchars = '*?!#><^@~+)(}$' + '`' # public\soundchars.h
    old_value = old_value.strip(soundchars)

    return f"sounds/{Path(old_value).with_suffix('.vsnd').as_posix()}"

def ImportSoundscape(file: Path):
    "scripts/soundscapes_*.vsc -> (n)[soundscapes/*/a.b.sndscape]"
    sndscape_folder = sh.EXPORT_CONTENT / soundscapes / file.stem.removeprefix('soundscapes').lstrip("_")
    sndscape_folder.MakeDir()

    soundscape_collection = KV.CollectionFromFile(file)
    fixups = {'wave': fix_wave_resource}

    def recursively_fixup(kv: VDFDict):
        for key, value in kv.iteritems(indexed_keys=True):
            if isinstance(value, VDFDict):
                recursively_fixup(value)
            elif (k:=key[1]) in fixups:
                kv[key] = fixups[k](value)

    recursively_fixup(soundscape_collection)  # change wav to vsnd
    
    for name, properties in soundscape_collection.items():
        sndscape_data = dict()
        sndscape_file = sndscape_folder / f'{name}.sndscape'
        sndscape_data = dict(properties)
        if not OVERWRITE_ASSETS and sndscape_file.exists():
            sh.status(f"Skipping {sndscape_file.local} [already-exist]")
            continue
        ...
        # https://developer.valvesoftware.com/wiki/Soundscape#Rules
        # soundscape format is not yet clear
        # source uses .wavs + volume + pitch
        # .sound assets are similar: .wavs + properties
        # so might need to convert play* properties to .sound assets
        """
        data =
        {
            dsp = 5
            fadetime = 1.0
            position = 5
            playrandom = 
            {
                sound = "sounds/soundscapes/name.sound"
            }
            playlooping =
            {
                sound = "sounds/soundscapes/name.sound"
                origin = [0, 0, 0]
            }
            playsoundscape =
            {
                soundscape = "soundscapes/name.sndscape"
                position = 6
            }
        }
        """
        sh.write(dict_to_kv3_text(dict(data=sndscape_data)), sndscape_file)
        print("+ Saved", sndscape_file.local)

    return sndscape_folder

"""
channel ['CHAN_VOICE']
volume [1, 0.3, '0.4, 0.7']
soundlevel ['SNDLVL_NORM', 0]
pitch ['PITCH_NORM', 150]
wave ['common/null.wav']
rndwave [VDFDict([('wave', '~player/footsteps/slosh1.wav'), ('wave', '~player/footsteps/slosh2.wav'), ('wave', '~player/footsteps/slosh3.wav'), ('wave', '~player/footsteps/slosh4.wav')])]
"""
def ImportGameSounds(asset_path: Path):
    "scripts/game_sounds*.txt -> (n)[sounds/*/a.b.sound]"
    game_sound_folder = sh.EXPORT_CONTENT / sounds / asset_path.stem.removeprefix('game_sounds_')
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
        if not OVERWRITE_ASSETS and sound_file.exists():
            sh.status(f"Skipping {sound_file.local} [already-exist]")
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
    return game_sound_folder

class CaseInsensitiveKey(str):
    def __hash__(self): return hash(self.lower())
    def __eq__(self, other: str): return self.lower() == other.lower()
class CaseInsensitiveDict(dict):
    def __setitem__(self, key, value): super().__setitem__(CaseInsensitiveKey(key), value)
    def __getitem__(self, key): return super().__getitem__(CaseInsensitiveKey(key))

def ImportSurfaceProperties(asset_path: Path):
    "scripts/surfaceproperties*.txt -> (n)[surfaces/*/name.surface]"
    
    surface_folder = sh.EXPORT_CONTENT / surfaces / asset_path.stem.removeprefix('surfaceproperties').lstrip("_")
    surface_folder.MakeDir()

    surface_collection = KV.CollectionFromFile(asset_path)

    for surface, properties in {**surface_collection}.items():
        surface_file = surface_folder / f'{surface}.surface'
        if not OVERWRITE_ASSETS and surface_file.exists():
            sh.status(f"Skipping {surface_file.local} [already-exist]")
            continue
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
