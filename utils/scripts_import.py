import shared.base_utils2 as sh
#from shared.base_utils2 import SBOX
from pathlib import Path
from shared.keyvalues1 import KV, VDFDict
from shared.keyvalues3 import KV3File
import itertools

SBOX = True
OVERWRITE_ASSETS = False

SOUNDSCAPES = True
GAMESOUNDS = True
SURFACES = True

scripts = Path('scripts')
SOUNDSCAPES_MANIFEST = scripts / "soundscapes_manifest.txt"
SURFACEPROPERTIES_MANIFEST = scripts / "surfaceproperties_manifest.txt"

soundscapes = Path('soundscapes')
sounds = Path('sounds')
surfaces = Path('surfaces')

def main():

    print("Importing Scripts!")

    if SOUNDSCAPES:
        print("Importing Soundscapes!") # soundscapes vsc, txt, and manifest...
        
        if SBOX:
            sh.import_context['dest'] = sh.EXPORT_CONTENT
            for soundscape_collection_path in itertools.chain(
                (sh.src(scripts)).glob('**/soundscapes_*.vsc'),
                (sh.src(scripts)).glob('**/soundscapes_*.txt')
            ):
                if soundscape_collection_path.name == SOUNDSCAPES_MANIFEST.name:
                    continue
                SoundscapeImporter.ImportSoundscapesToVdata(soundscape_collection_path)
        else:
            sh.import_context['dest'] = sh.EXPORT_GAME
            for soundscapes in itertools.chain(
                sh.collect("scripts", ".vsc", ".txt", OVERWRITE_ASSETS, match="soundscapes_*.vsc"),
                sh.collect("scripts", ".txt", ".txt", OVERWRITE_ASSETS, match="soundscapes_*.txt")
            ):
                if soundscapes.name == SOUNDSCAPES_MANIFEST.name:
                    SoundscapeImporter.ImportSoundscapeManifest(soundscapes)
                    continue
                SoundscapeImporter.ImportSoundscapes(soundscapes)

    sh.import_context['dest'] = sh.EXPORT_CONTENT

    if GAMESOUNDS:
        print("Importing Game Sounds!") # game sounds: scripts -> soundevents
        
        for file in (sh.src(scripts)).glob('**/game_sounds*.txt'):
            if file.name != 'game_sounds_manifest.txt':
                ImportGameSounds(file)

        if (boss:=sh.src(scripts)/'level_sounds_general.txt').is_file():
            ImportGameSounds(boss)

    if SURFACES:
        print("Importing Surfaces!") # surfaces: scripts -> surfaceproperties.vsurf

        manifest_handle = VsurfManifestHandler()
        for surfprop_txt in (sh.src(scripts)).glob('**/surfaceproperties*.txt'):
            if surfprop_txt.name == SURFACEPROPERTIES_MANIFEST.name:
                manifest_handle.read_manifest(surfprop_txt)
                continue

            folderOrFile = ImportSurfaceProperties(surfprop_txt)
            if not SBOX:
                manifest_handle.retrieve_surfaces(folderOrFile) # file only
        
        manifest_handle.after_all_converted()

    print("Looks like we are done!")

def fix_wave_resource(old_value):
    soundchars = '*?!#><^@~+)(}$' + '`' # public\soundchars.h
    old_value = old_value.strip(soundchars)

    return f"sounds/{Path(old_value).with_suffix('.vsnd').as_posix()}"

class SoundscapeImporter:
    fixups = {'wave': fix_wave_resource}
    @staticmethod
    def recursively_fixup(kv: VDFDict):
        for key, value in kv.iteritems(indexed_keys=True):
            if isinstance(value, VDFDict):
                SoundscapeImporter.recursively_fixup(value)
            elif (k:=key[1]) in SoundscapeImporter.fixups:
                kv[key] = SoundscapeImporter.fixups[k](value)

    @staticmethod
    def FixedUp(file: Path):
        kv = KV(file)
        soundscape_collection = KV.CollectionFromFile(file)
        SoundscapeImporter.recursively_fixup(soundscape_collection)  # change wav to vsnd
        return soundscape_collection

    @staticmethod
    def ImportSoundscapes(file: Path):
        new_soundscapes = ''
        for name, properties in SoundscapeImporter.FixedUp(file).items():
            if isinstance(properties, VDFDict):
                new_soundscapes += f"{name}{properties.ToString()}"
            else:
                new_soundscapes += f'{name}\t"{properties}"\n'
            continue

        newsc_path = sh.output(file, '.txt')
        newsc_path.parent.MakeDir()
        sh.write(newsc_path, new_soundscapes)
        print("+ Saved", newsc_path.local)
        return newsc_path
        #soundscapes_manifest.add("file", f'scripts/{newsc_path.name}')

    @staticmethod
    def ImportSoundscapesToVdata(file: Path):
        "scripts/soundscapes_*.vsc -> (n)[soundscapes/*/a.b.sndscape]"
        sndscape_folder = sh.EXPORT_CONTENT / soundscapes / file.stem.removeprefix('soundscapes').lstrip("_")
        sndscape_folder.MakeDir()

        for name, properties in SoundscapeImporter.FixedUp(file).items():
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
            sh.write(KV3File(data=sndscape_data).ToString(), sndscape_file)
            print("+ Saved", sndscape_file.local)
        return sndscape_folder

    @staticmethod
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

"""
channel ['CHAN_VOICE']
volume [1, 0.3, '0.4, 0.7']
soundlevel ['SNDLVL_NORM', 0]
pitch ['PITCH_NORM', 150]
wave ['common/null.wav']
rndwave [VDFDict([('wave', '~player/footsteps/slosh1.wav'), ('wave', '~player/footsteps/slosh2.wav'), ('wave', '~player/footsteps/slosh3.wav'), ('wave', '~player/footsteps/slosh4.wav')])]
"""
def ImportGameSounds(asset_path: Path):
    """
    VALVE: scripts/game_sounds*.txt -> soundevents/game_sounds*.vsndevts
    SBOX: scripts/game_sounds*.txt -> (n)[sounds/*/a.b.sound]
    """
    vsndevts_file = sh.EXPORT_CONTENT / "soundevents" / asset_path.local.relative_to(scripts).with_suffix('.vsndevts')
    out_sound_folder = sh.EXPORT_CONTENT / sounds / asset_path.stem.removeprefix('game_sounds_')
    if not SBOX:
        vsndevts_file.parent.MakeDir()
    else:
        out_sound_folder.MakeDir()
    
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
    
    def _handle_range(k, v) -> "median, deviation":
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
    kv3 = KV3File()

    for gamesound, gs_data in kv.items(): # "weapon.fire", {}
        
        if not SBOX and gamesound[0].isdigit():
            gamesound = '_' + gamesound

        # Valve
        out_kv = dict(type='src1_3d') # why 3d?
        
        # SBOX
        sound_file = out_sound_folder / f'{gamesound}.sound'
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
        for (i, k), v in gs_data.items(indexed_keys=True):
            out_k, out_v = k, v
            ## Turns out you can have multiple 'wave' in counter strike global offensive!
            # instead of using rndwave {} !!
            if k == 'wave':
                fixed_wav = fix_wave_resource(v)
                if i != 0:
                    if i == 1:
                        out_kv['vsnd_files'] = [out_kv['vsnd_files'], ]
                    else:
                        out_kv['vsnd_files'].append(fixed_wav)
                    continue
                if out_v == "sounds/common/null.vsnd" and not SBOX:
                    continue
                out_k, out_v = 'vsnd_files', fixed_wav
                sound_data['sounds'].append(fix_wave_resource(v))

            elif k == 'rndwave':
                out_k, out_v = 'vsnd_files', []
                for rndwave_k, rndwave_v in v.items(indexed_keys=True):
                    if rndwave_k[1] != 'wave':
                        continue
                    res = fix_wave_resource(rndwave_v)
                    if res != 'sounds/common/null.vsnd':
                        out_v.append(res)
                        sound_data['sounds'].append(res)
                
                if not len(out_v) and not SBOX: continue

            elif k in ('volume', 'pitch', 'soundlevel'):
                if range:=_handle_range(k, v):
                    out_kv.update({k:range[0], k+"_rand_min":-range[1], k+"_rand_min":range[1],})
                    sound_data[k] = range[0]
                    sound_data[k+'random'] = range[1]
                    continue
                if k == 'volume':
                    if v == 'VOL_NORM':
                        if SBOX:
                            continue
                        out_v = 1.0  # aka just continue? (default)
                    out_v = sound_data[k] = float(v)
                elif k == 'pitch':
                    if type(v) is str:
                        v = PITCH.get(v, 100)
                    # Normalize pitch
                    out_v = sound_data[k] = v / 100
                elif k == 'soundlevel':
                    if SBOX:
                        ...
                    elif type(v) is not str:
                        ...
                    else:
                        if (out_v:=SNDLVL.get(v)) is None:
                            out_v = 75
                            if v.startswith('SNDLVL_'):
                                try:
                                    out_v = int(v[7:-2])
                                except Exception:
                                    print(v[7:])
                            else: print(v)
            if not SBOX:
                if k == 'delay_msec': out_k, out_v = 'delay', v/1000
                elif k == 'ignore_occlusion': out_k, out_v = 'occlusion_scale', (1 if not v else 0)#'sa_enable_occlusion'
                elif k == 'operator_stacks':  # this only exists in globul offensif
                    ...
                    continue
                elif k in ('soundentry_version', 'alert', 'hrtf_follow','gamedata',): # skiplist
                    continue
                else:
                    continue 
            
            out_kv[out_k] = out_v
        
        if out_kv == dict(type='src1_3d'):  # empty
            out_kv = None
        
        if SBOX:
            sh.write(KV3File(data=sound_data).ToString(), sound_file)
            print("+ Saved", sound_file.local)
        else:
            kv3[gamesound] = out_kv
    
    if SBOX:
        return out_sound_folder
    else:
        sh.write(vsndevts_file, kv3.ToString())

        print("+ Saved", vsndevts_file.local)
        return vsndevts_file


vsurf_base_params = {
    'physics': ('density','elasticity','friction','dampening','thickness',),
    'audiosounds':('bulletimpact','scraperough','scrapesmooth','impacthard','impactsoft','rolling','break','strain',),
    'audioparams': ('audioreflectivity','audiohardnessfactor','audioroughnessfactor','scrapeRoughThreshold','impactHardThreshold',),
}

class CaseInsensitiveKey(str):
    def __hash__(self): return hash(self.lower())
    def __eq__(self, other: str): return self.lower() == other.lower()
class CaseInsensitiveDict(dict):
    def __setitem__(self, key, value): super().__setitem__(CaseInsensitiveKey(key), value)
    def __getitem__(self, key): return super().__getitem__(CaseInsensitiveKey(key))

def ImportSurfaceProperties(asset_path: Path):
    """
    VALVE: scripts/surfaceproperties*.txt -> surfaceproperties/surfaceproperties*.vsurf
    SBOX: scripts/surfaceproperties*.txt -> (n)[surfaces/*/name.surface]
    """
    
    vsurf_file: Path = sh.EXPORT_CONTENT / "surfaceproperties" / asset_path.local.relative_to(scripts).with_suffix('.vsurf')
    surface_folder = sh.EXPORT_CONTENT / surfaces / asset_path.stem.removeprefix('surfaceproperties').lstrip("_")
    
    if not SBOX:
        if vsurf_file.is_file() and not OVERWRITE_ASSETS:
            return sh.skip('already-exist', vsurf_file)
        vsurf_file.parent.MakeDir()
    else:
        surface_folder.MakeDir()

    surface_collection = KV.CollectionFromFile(asset_path)
    vsurf = KV3File(SurfacePropertiesList = [])

    for surface, properties in {**surface_collection}.items():
        new_surface = dict(surfacePropertyName = surface)
        unsupported_params = {}
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
            # Valve
            context = next((ctx for ctx, group in vsurf_base_params.items() if key in group), None)
            if context is not None:
                new_surface.setdefault(context, {})[key] = value
            elif key in ('base'):
                new_surface[key] = value
            else:
                unsupported_params[key] = value

            # SBOX
            key = {'stepleft':'footleft','stepright':'footright','base':'basesurface'}.get(key, key)
            if key in surface_data: # needs to be a counterpart
                if key == "basesurface":
                    value = f"{surface_folder.relative_to(sh.EXPORT_CONTENT).as_posix()}/{value}.surface"
                surface_data[key] = value
            elif key in surface_data["Sounds"]:
                surface_data["Sounds"][key] = value

        if SBOX:
            sh.write(KV3File(data=surface_data).ToString(), surface_file)
            print("+ Saved", surface_file.local)
        else:
            # Add default base
            if 'base' not in new_surface:
                if surface not in ('default', 'player'):
                    new_surface['base'] = 'default'

            # Add unsupported parameters last
            if unsupported_params:
                new_surface['legacy_import'] = unsupported_params

            vsurf['SurfacePropertiesList'].append(new_surface)

    if SBOX:
        return surface_folder
    else:
        sh.write(vsurf_file, vsurf.ToString())
        print("+ Saved", vsurf_file.local)

        return vsurf_file, vsurf['SurfacePropertiesList']

class VsurfManifestHandler:
    """
    * source only reads files listed in manifest
    * source2 only reads a single `surfaceproperties.vsurf` file.
    -
    --> write surfaces to main file as per rules of manifest
    """
    def __init__(self):
        self.manifest_files = []
        self.all_surfaces: dict[Path, list] = {}

    def read_manifest(self, manifest_file: Path):
        self.manifest_files.extend(KV.FromFile(manifest_file).get_all_for('file'))

    def retrieve_surfaces(self, rv: tuple[Path, list]):
        if rv is not None:
            self.all_surfaces.__setitem__(*rv)

    def after_all_converted(self):
        # Only include surfaces from files that are on manifest.
        # Last file has override priority
        if not (self.manifest_files and self.all_surfaces):
            return
        vsurf_path = next(iter(self.all_surfaces)).with_stem('surfaceproperties')
        vsurf = KV3File(SurfacePropertiesList = [])
        for file in self.manifest_files[::-1]:
            file = vsurf_path.parents[1] / 'surfaceproperties' / Path(file).with_suffix('.vsurf').name
            for surfaceproperty in self.all_surfaces.get(file, ()):
                if not surfaceproperty:
                    break
                # ignore if this surface is already defined
                if not any(
                    surfaceproperty2['surfacePropertyName'].lower() == surfaceproperty['surfacePropertyName'].lower()
                        for surfaceproperty2 in vsurf['SurfacePropertiesList']):
                    vsurf['SurfacePropertiesList'].append(surfaceproperty)

        sh.write(vsurf_path, vsurf.ToString())
        print("+ Saved", vsurf_path.local)

if __name__ == '__main__':
    sh.parse_argv()
    main()  
