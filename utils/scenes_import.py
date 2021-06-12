from pathlib import Path
from shutil import copyfile
import shared.base_utils2 as sh

EVERYTHING_TO_ROOT = False

IN_EXT = '.vcd'
SCENESIMAGE = 'scenes.image'

scenes_content = \
'''<!-- schema text {7e125a45-3d83-4043-b292-9e24f8ef27b4} generic {198980d8-3a93-4919-b4c6-dd1fb07a3a4b} -->
ResourceManifest_t
{
    string name = "Scenes Manifest"
    string[] resourceFileNameList =
    [
        "scenes/_root.vcdlist"
    ]
}'''

def _ensure_scenes_vrman():
    scenes_vrman = sh._dest() / 'scenes/scenes.vrman'
    if not scenes_vrman.exists():
        scenes_vrman.parent.mkdir(exist_ok=True, parents=True)
        with open(scenes_vrman, 'w') as fp:
            fp.write(scenes_content)

vcdlist_entries_cache = {}

@sh.s1import()
def ImportVCD(vcd_in: Path, vcd_out: Path, to='_root.vcdlist'):
    
    _ensure_scenes_vrman()
    
    vcdlist = sh._dest() / 'scenes' / to
    vcdlist.parent.mkdir(exist_ok=True, parents=True)

    if not vcd_out.exists():
        copyfile(vcd_in, vcd_out)

    vcd_local = vcd_out.local.relative_to('scenes').as_posix()

    vcdlist_entries_cache.setdefault(to, [])

    if vcdlist.exists():
        if not vcdlist_entries_cache.get(to):
            with open(vcdlist) as fp:
                # TODO: forward slashes, whitelines, etc
                vcdlist_entries_cache[to] = fp.read().splitlines()
        if vcd_local in vcdlist_entries_cache[to]:
            return vcdlist

    with open(vcdlist, 'a') as fp:
        fp.write(f'{vcd_local}\n')
        vcdlist_entries_cache[to].append(vcd_local)
        print(f"+ Appended VCD to scenes/{to}: {vcd_local}")

    return vcdlist

# ORGANIZED Structure
# _root.vcdlist    scenes/a.vcd, scenes/b.vcd
# d.vcdlist        scenes/d/d5.vcd, scenes/d/test.vcd
# test_magnificient.vcdlist   scenes/test/magnificient/test.vcd, scenes/test/magnificient/b.vcd

if __name__ == '__main__':
    for vcd in sh.collect('scenes', IN_EXT, '', existing=True):
        ImportVCD(vcd)

    print("Looks like we are done!")