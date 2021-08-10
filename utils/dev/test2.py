from pathlib import Path
import vdf

material1 = {
    "vertexlitgeneric": {
	    "F_SELF_ILLUM":	1,
	    "TextureColor":	"materials/ads/ad01.tga",
	    "TextureSelfIllumMask":	"materials/ads/ad01_a_selfillummask.tga",
    	"g_vSelfIllumTint":	"[0.100000 0.100000 0.100000 1.000000]",
    	"TextureRoughness":	"materials/default/default_rough_s1import.tga",
    	"SystemAttributes":
    	{
    		"PhysicsSurfaceProperties":	"world.glass"
    	},
    }
}

material2 = {
    "Layer0": {
	    "shader": "vertexlitgeneric.vfx",
	    "F_SELF_ILLUM":	1,
	    "TextureColor":	"materials/ads/ad01.tga",
	    "TextureSelfIllumMask":	"materials/ads/ad01_a_selfillummask.tga",
    	"g_vSelfIllumTint":	"[0.100000 0.100000 0.100000 1.000000]",
    	"TextureRoughness":	"materials/default/default_rough_s1import.tga",

    	"SystemAttributes":
    	{
    		"PhysicsSurfaceProperties":	"world.glass"
    	},
    }
}


###########################################
#
# EXPORT_GAME = D:\Games\steamapps\common\Half-Life Alyx\game\csgo
# EXPORT_CONTENT = D:\Games\steamapps\common\Half-Life Alyx\content\csgo
#
print()
CORE = "core"

from enum import Enum
class eAppPath(Enum):
    "Source 2 Application paths"
    ROOT = Path()
    #CONTENT = Path("content")
    #GAME = Path("game")
    CONTENTROOT = Path("content")
    GAMEROOT = Path("game")
    SRC = Path("src")
    EXECUTABLE = GAMEROOT / "bin"
    #GAMEBIN = GAME / "bin" # gamebin is for the game not engine (clientdll)

# pylint: disable=no-member
class Engine2Paths:
    def __init__(self, ROOT: Path):
        for folder in eAppPath:
            self.__setattr__(folder.name, ROOT / folder.value)


class Engine2:
    def __init__(self, root):
        self.paths = Engine2Paths(root)

ROOT = Path(r"C:\Users\kristi\Desktop\Source 2")
paths = Engine2Paths(ROOT)


class FileSystem:

    class FilePath:
        #def __init__(self):
        #    self.path = None

        def __str__(self):
            return self.path.as_posix()

# hlvr, core, hlvr_addons/csgo, dota_latvian
class Game(FileSystem.FilePath):
    games = []
    def __init__(self, name: str):
        self.name: str = name
        self.path = Path(name)

        self.is_addon: bool = False
        if Addon.is_addon(name):
            self.is_addon = True
            addon = Addon(name)
            self.path = addon.path
            self.name = addon.name
    
    #def __str__(self):
    #    return self.path.as_posix()

class Addon:
    addons = {}
    def __init__(self, name: str):
        self.path = Path(name)
        self.name = self.path.stem
        self.mother = str(self.path.parent).replace("_addons", "")

    @staticmethod
    def is_addon(name: str) -> bool:
        name = Path(name)
        if (len(name.parents) > 2) or not str(name.parent).endswith("_addons"):
            return False
        return True

print(Game("hlvr_addons/l4d2"))


class EXPORT(Engine2Paths):
    def __init__(self):
        self.GAME /= Path(game.name)
        self.CONTENT /= Path(game.name)

def fixPaths(path):
    path

fixPaths(r"D:\Games\steamapps\common\Half-Life Alyx\game\hlvr")

#pathin = r"D:\Games\steamapps\common\Half-Life Alyx\game\hlvr"

#print(paths.CONTENT) 

import pprint
pprint.pprint(paths.__dict__, depth=5, indent=4)

#ROOT.GAME = "x"
#Game = r"hlvr"
#ASSET_ROOT = r"hlvr_addons\csgo"

MOD = "hlvr"
ADDON = "csgo"


ADDON = MOD + "_addons"

Path.IMPORT_GAME =  Path(r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\\")
Path.EXPORT_GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\game\\"

class SourcePath(type(Path())):#, Path):
    def __init__(self, path: str):
        self.root2 = "materials"
        #Path.__init__(path)
        #super().__init__()

def GetGame(x):
    pass

"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\materials\models\brick.vmt" # material asset
"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\materials" # materials root
"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\gameinfo.gi" # mod gameinfo.gi
"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo.exe" # app exe
"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\bin" # engine bin

"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\materials\models\brick.vmt" # material asset
"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo\materials" # materials root
"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\gameinfo.gi" # mod gameinfo.gi
"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo.exe" # app exe
"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\bin" # engine bin

def main():
    GetGame(ROOT/ "game" / Path("core"))
    patt = SourcePath("materials/models/lol") / SourcePath("lul") #"materials" / Path("models") #
    print(type(patt), patt, patt.IMPORT_GAME)
    xx2 = Path(fr"{Path.IMPORT_GAME}\csgo\materials\models\x.mdl")
    print("Local", xx2.LocalDir())

from functools import wraps
def add_method(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, func.__name__, wrapper)
        return func
    return decorator

@add_method(Path)
def LocalDir(self):
    try: local = self.relative_to(Path.IMPORT_GAME)
    except ValueError:
        try: local = self.relative_to(Path.EXPORT_GAME)
        except: local = self
    return local#.as_posix()



@add_method(Path)
def RelDir(self, to: list = [Path.IMPORT_GAME, Path.EXPORT_GAME]):
    for path in to:
        try:
            return self.relative_to(path)
        except ValueError:
            continue
    raise ValueError

print('---')
main()
print('----')




#def main():
#    #global vmt, vmat
#    #vmt = ValveMaterial(1, kv = material1)
#    #vmat = ValveMaterial(2, kv = material2)
#    #Import()
#
#    #print(vmt.KeyValues)
#    #for i in vmt.properties():
#    #    print (i)
#    print("XDDD")
#    x = InputPath("materials/models/car.vmat")
#    #print(x)
#
#    #x = Path("materials/models/car.vmat")
#    print(type(x))
#main()
# %%
