

'''
<!-- schema text {7e125a45-3d83-4043-b292-9e24f8ef27b4} generic {198980d8-3a93-4919-b4c6-dd1fb07a3a4b} -->
ResourceManifest_t
{
    string name = "Scenes Manifest"
    string[] resourceFileNameList =
    [
        "scenes/_root.vcdlist"
    ]
}
'''
if __name__ is None:
    from utils.shared import base_utils as sh
from shared import base_utils as sh

PATH_TO_CONTENT_ROOT = r"D:\Games\steamapps\common\Half-Life Alyx\game\csgo"
PATH_TO_NEW_CONTENT_ROOT = r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo"

IN_EXT = '.vcd'
SCENESIMAGE = 'scenes.image'

fs = sh.Source('scenes', PATH_TO_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT)


for vcd in fs.collect_files(IN_EXT, '', existing=True):
    print(vcd)