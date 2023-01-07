from pathlib import Path
from shutil import copyfile
import shared.base_utils2 as sh

EVERYTHING_TO_ROOT = False

IN_EXT = '.vcd'
SCENESIMAGE = 'scenes.image'

scenes_vrman_template = \
'''<!-- schema text {7e125a45-3d83-4043-b292-9e24f8ef27b4} generic {198980d8-3a93-4919-b4c6-dd1fb07a3a4b} -->
ResourceManifest_t
{
    string name = "Scenes Manifest"
    string[] resourceFileNameList =
    [
        <>
    ]
}'''

# ORGANIZED Structure
# _root.vcdlist    scenes/a.vcd, scenes/b.vcd
# d.vcdlist        scenes/d/d5.vcd, scenes/d/test.vcd
# test_magnificient.vcdlist   scenes/test/magnificient/test.vcd, scenes/test/magnificient/b.vcd
def main():
    print("Importing Scenes!")
    for vcd in sh.collect('scenes', IN_EXT, '', existing=True):
        path_parts = vcd.local.relative_to('scenes').parent.parts
        if EVERYTHING_TO_ROOT or len(path_parts) == 0:
            ImportVCD(vcd, '_root')
        else:
            ImportVCD(vcd, '_'.join(path_parts))

    print("Creating scenes.vrman!")

    scenes_vrman = sh.output('scenes/scenes.vrman')
    if not scenes_vrman.is_file():
        scenes_vrman.parent.MakeDir()
        with open(scenes_vrman, 'w') as fp:
            fp.write(scenes_vrman_template.replace("<>", ",\n        ".join(f'"scenes/{vcdlist}.vcdlist"' for vcdlist in vcdlist_entries_cache)))

    print("Looks like we are done!")

vcdlist_entries_cache = {}

def ImportVCD(vcd_in: Path, vcdlist_name: str):
    vcdlist = (sh.output('scenes') / vcdlist_name).with_suffix('.vcdlist')
    vcdlist.parent.MakeDir()
    vcd_out = sh.output(vcd_in)
    vcd_out.parent.MakeDir()

    if not vcd_out.is_file():
        copyfile(vcd_in, vcd_out)

    vcd_local = vcd_out.local.relative_to('scenes').as_posix()

    vcdlist_entries_cache.setdefault(vcdlist_name, [])

    if vcdlist.is_file():
        if not vcdlist_entries_cache.get(vcdlist_name):
            with open(vcdlist) as fp:
                # TODO: forward slashes, whitelines, etc
                vcdlist_entries_cache[vcdlist_name] = fp.read().splitlines()
        if vcd_local in vcdlist_entries_cache[vcdlist_name]:
            return vcdlist

    with open(vcdlist, 'a') as fp:
        fp.write(f'{vcd_local}\n')
        vcdlist_entries_cache[vcdlist_name].append(vcd_local)
        print(f"+ Appended VCD to {vcdlist.local}: {vcd_local}")

    return vcdlist

if __name__ == '__main__':
    sh.parse_argv()
    main()
