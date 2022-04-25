#
# .OLD_EXT -> .NEW_EXT for content inside files
# csgo soundscapes:
# "wave" ambient\dust2\wind_sand_01.wav" -> "wave" "sounds\ambient\dust2\wind_sand_01.vsnd" 
#

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
    manifest_handle = VsurfManifestHandler()
    for surfprop_txt in sh.collect("scripts", ".txt", ".txt", OVERWRITE_SCRIPTS, match="surfaceproperties*.txt"):
        if surfprop_txt.name == SURFACEPROPERTIES_MANIFEST.name:
            manifest_handle.read_manifest(surfprop_txt)
            continue
        manifest_handle.retrieve_surfaces(
            ImportSurfaceProperties(surfprop_txt)
        )
    manifest_handle.after_all_converted()

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
    'audiosounds':('bulletimpact','scraperough','scrapesmooth','impacthard','impactsoft','rolling','break','strain',),
    'audioparams': ('audioreflectivity','audiohardnessfactor','audioroughnessfactor','scrapeRoughThreshold','impactHardThreshold',),
}

def ImportSurfaceProperties(asset_path: Path):
    "scripts/surfaceproperties*.txt -> surfaceproperties/surfaceproperties*.vsurf"
    vsurf_file: Path = sh.EXPORT_CONTENT / "surfaceproperties" / asset_path.local.relative_to(scripts).with_suffix('.vsurf')
    vsurf_file.parent.MakeDir()

    
    kv = KV.CollectionFromFile(asset_path)
    vsurf = dict(SurfacePropertiesList = [])

    for surface, properties in {**kv}.items():
        new_surface = dict(surfacePropertyName = surface)
        unsupported_params = {}
        for key, value in properties.items():
            context = next((ctx for ctx, group in vsurf_base_params.items() if key in group), None)
            if context is not None:
                new_surface.setdefault(context, {})[key] = value
            elif key in ('base'):
                new_surface[key] = value
            else:
                unsupported_params[key] = value

        # Add default base
        if 'base' not in new_surface:
            if surface not in ('default', 'player'):
                new_surface['base'] = 'default'

        # Add unsupported parameters last
        if unsupported_params:
            new_surface['legacy_import'] = unsupported_params

        vsurf['SurfacePropertiesList'].append(new_surface)
    
    sh.write(dict_to_kv3_text(vsurf), vsurf_file)
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
        self.all_surfaces.__setitem__(*rv)

    def after_all_converted(self):
        # Only include surfaces from files that are on manifest.
        # Last file has override priority
        if not (self.manifest_files and self.all_surfaces):
            return
        vsurf_path = next(iter(self.all_surfaces)).with_stem('surfaceproperties')
        vsurf = dict(SurfacePropertiesList = [])
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

        sh.write(dict_to_kv3_text(vsurf), vsurf_path)
        print("+ Saved", vsurf_path.local)


if __name__ == '__main__':
    sh.parse_argv()
    main()  

def ImportUpdateResourceRefs(asset_path: Path):
    ...
    # this func is for other generic scripts to update their resource refs
    # eg. search for each value and see if its a ref and replace each
    # after that just integ
def ImportUpdateResourceRefs_ProcessKVEscapeSeqs():...