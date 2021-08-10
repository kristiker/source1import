import shared.base_utils2 as sh
if __name__ is None:
    import utils.shared.base_utils2 as sh
from pathlib import Path

s1import = sh.s1import

sh.import_context['dest'] = sh.EXPORT_CONTENT

x = Path(r'D:\Games\steamapps\common\Half-Life Alyx\game\csgo\panorama\thing.xml')
#x.lives_in = sh.IMPORT_GAME



@s1import('.vxml')
def importxtoy(asset_in, asset_out, **s1import):
    print(asset_in)
    #print(asset_out)
    return asset_out

print(importxtoy(x))
sh.import_context['dest'] = sh.EXPORT_GAME
print()
print(importxtoy(x))

#z = sh.Importable()
#print(z)

#print(x, x.local())
