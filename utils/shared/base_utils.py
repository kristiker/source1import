import argparse, os, json
from pathlib import Path
import types
import zlib

DEBUG = False
def msg(*args, **kwargs):
    if DEBUG:
        print("@ DBG:", *args, **kwargs)

CORE = "core"
MOD = "hlvr"

from enum import Enum
class App(Enum):
    "Source 2 Application paths"
    ROOT = Path()
    CONTENT = Path("content")
    GAME = Path("game")
    BIN = GAME / Path("bin")

class IO:
    def __init__(self, scope: Path, inPath, outPath):
        self.SCRIPT_SCOPE = Path(scope) # doesn't really belong here
        self.IN_PATH, self.OUT_PATH = inPath, outPath

        self.arg_parser = argparse.ArgumentParser(usage = '-i "path/to/source1/game/root/" -o "path/to/source2/game/root" -f [optional] Force overwrite')
        self.arg_parser.add_argument('-i', default=self.IN_PATH, help="Input path. Can be a folder (recursive search) or file. Can skip using the -i option if you put the path @ the end of the commandline.")
        self.arg_parser.add_argument('-o', default=self.OUT_PATH, help="Output path. Can only be a folder. If omitted content will be output in the same place.")
        self.arg_parser.add_argument('-f', help="Force overwrite content that might have already been imported.", action="store_true")
        args_known, args_unknown = self.arg_parser.parse_known_args()

        if args_known.i:    self.IN_PATH = Path(args_known.i)
        elif args_unknown:  self.IN_PATH = Path(args_unknown[1])
        if args_known.o:    self.OUT_PATH = Path(args_known.o)
        else:               self.OUT_PATH = self.IN_PATH
        if not (self.IN_PATH or self.OUT_PATH):
            self._askforpaths()
            if not (self.IN_PATH or self.OUT_PATH):
                assert "Cannot continue without an input path"
    
        if args_known.f: self.SHOULD_OVERWRITE = True
        else: self.SHOULD_OVERWRITE = False

        self.IN_ROOT, self.IN_SUBSCOPE = self._fix_subscoped(self.IN_PATH)
        self.OUT_ROOT, _ = self._fix_subscoped(self.OUT_PATH)

        self.SEARCH_PATH = self.IN_ROOT / Path(self.SCRIPT_SCOPE) / Path(self.IN_SUBSCOPE)

        self.IMPORT_GAME = self.IN_ROOT # get_possibly_legacy()
        self.IMPORT_CONTENT = self.IN_ROOT

        self.SOURCE2_APP_ROOT = self.get_path_app(self.OUT_ROOT, App.ROOT)
        self.EXPORT_GAME = self.get_path_app(self.OUT_ROOT, App.GAME)
        self.EXPORT_CONTENT = self.get_path_app(self.OUT_ROOT, App.CONTENT)

        self.currentDir = Path(__file__).parent
        self.blacklist = self._get_blacklist()

    def get_path_app(self, path, get:App = App.CONTENT):
        path_components = path.parts

        for gc in ("content", "game"):
            if gc not in path_components[-3:-1]: # ('game', 'hlvr_addons') || ('Game Title', 'game')
                continue

            index_rightmost = len(path_components) - path_components[::-1].index(gc) - 1
            appPath = Path("/".join(path_components[:index_rightmost]))
            if get == App.ROOT: return appPath

            mod = Path("/".join(path_components[index_rightmost+1:]))
            return appPath / get.value / mod

    def _askforpaths(self) -> Path:
        #global IN_PATH, OUT_PATH
        print(fr"Please type in to the root of your mod/game/addon before /{self.SCRIPT_SCOPE}/." )
        print(fr"Remember: this directory is the one that contains the {self.SCRIPT_SCOPE} folder. For single files use the full path. To exit script type `quit`")
        print(fr"Example: HLA Mod     C:\Games\steamapps\common\Half-Life Alyx\game\portal2")
        print(fr"         HLA Addon   C:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\sfm_project")
        print(fr"         Outside Mod C:\Users\user3\Desktop\tf2")
        print()
        print(fr"         Single File C:\Games\steamapps\common\Left 4 Dead 2\left4dead2\materials\ads\burger_off.vmt")
        print()

        while not self.IN_PATH:
            print(f"Please type in the path containing your source 1 {self.SCRIPT_SCOPE} folder:")
            c = input(">>")
            if c in ('q', 'quit', 'exit', 'close'): quit()
            else: c = Path(c)
            if c.is_dir() or c.is_file():
                self.IN_PATH = c

        while not self.OUT_PATH:
            print("\nPlease type in the path that will contain your imported files (content/game) (enter blank to import in the same place)")
            c = input(">>")
            if c in ('q', 'quit', 'exit', 'close'): quit()
            c = Path(c)
            if c.is_dir() or c.is_file():
                self.OUT_PATH = c

    def _fix_subscoped(self, path: Path) -> Path:
        if str(self.SCRIPT_SCOPE) not in path.parts:
            return path, Path()
        index_rightmost = len(path.parts) - path.parts[::-1].index(str(self.SCRIPT_SCOPE)) - 1 #.index()
        root, subscope = "/".join(path.parts[:index_rightmost]), "/".join(path.parts[index_rightmost+1:])
        
        return Path(root), Path(subscope)

    def _get_blacklist(self):
        json_path = self.currentDir / Path("import_blacklist.json")
        try:
            with open(json_path, "r+") as fp:
                return json.load(fp).get(str(self.SCRIPT_SCOPE), [])
        except Exception as ex:
            print(type(ex), "COULDNT GET BLACKLIST", json_path)
            return []

class Source(IO):

    def FullDir(self, relPath: Path):
        "materials/texture_color.tga -> C:/Users/User/Desktop/stuff/materials/texture_color.tga"
        return self.IN_ROOT / relPath

    def LocalDir(self, path: Path) -> Path:
        "C:/Users/User/Desktop/stuff/materials/texture_color.tga -> materials/texture_color.tga"
        if not isinstance(path, Path):
            path = Path(path)
        try: local = path.relative_to(self.OUT_ROOT)
        except ValueError:
            try: local = path.relative_to(self.IN_ROOT)
            except: local = path
        return local#.as_posix()

    def LocalDir_Legacy(self, path: Path) -> Path:
        "materials/textures/texture_color.tga -> textures/texture_color.tga"
        return path.relative_to(self.SCRIPT_SCOPE)

    def FixLegacyLocal(self, path: Path) -> Path:
        "environment maps/metal_generic_002 -> materials/environment maps/metal_generic_002"
        return self.SCRIPT_SCOPE / path
    
    def NoSpace(self, path: Path) -> Path: # hmmm
        "Replaces spaces with underscores on the final component of a path"
        return path.parent / Path(path.name.replace(" ", "_"))

    def Output(self, path: Path) -> Path:
        "Return proper output path for this input"
        return self.OUT_ROOT / self.LocalDir(path)

    def Input(self, path: Path) -> Path:
        return self.IN_ROOT / self.LocalDir(path)
    
    def ShouldOverwrite(self, path: Path, custVar: bool = False) -> bool:
        if (self.SHOULD_OVERWRITE or custVar) or not path.exists():
            return True
        return False

    def collect_files(self, inExt, outExt, existing:bool = False, outNameRule = None, customPath = None, customMatch = None, customSkip: list = []):
        if not isinstance(outExt, list): outExt = [outExt] # support multiple output extensions
        #if outName and not isinstance(outName, list): outName = [outName] # support multiple output names
        
        #files_with_ext = []
        searchPath = self.SEARCH_PATH if not customPath else customPath
        match = f'**/*{inExt}' if not customMatch else customMatch
        skipThese = self.blacklist if not customSkip else customSkip

        if searchPath.is_file():
            if searchPath.suffix == inExt:
                yield searchPath
            else: print(f"~ File is not a {inExt}")

        elif searchPath.is_dir():
            skipCountExists, skipCountBlacklist = 0, 0
            if not customMatch:
                print(f"\nSearching for %s{inExt} files... This may take a while..." % ("" if existing else "unexported "))
            else:
                print(f"\nSearching for files %s[ {customMatch} ]... This may take a while..." % ("" if existing else "unexported "))
            glob = searchPath.glob(match)

            for filePath in glob:
                bSkipThis = False
                if outNameRule: possibleNameList = outNameRule(filePath)
                else: possibleNameList = filePath
                if not isinstance(possibleNameList, (list, types.GeneratorType)): possibleNameList = [possibleNameList] # support multiple output names
                #try:
                # Attempt to see if you have an iterable object.
                for filePath2 in possibleNameList: # try a number of possible outputs. default is list() which will give one output
                    if bSkipThis: break
                    for outExt_ in outExt:
                        if bSkipThis: break
                        if not existing and self.Output(filePath2).with_suffix(outExt_).exists():
                            skipCountExists += 1
                            bSkipThis = True
                #except TypeError:
                    # some_thing_which_may_be_a_generator isn't actually a generator
                    # do something else

                for skip_match in skipThese:
                    if bSkipThis: break
                    if (skip_match.replace("\\", "/") in filePath2.as_posix()) or filePath2.match(skip_match):
                        skipCountBlacklist += 1
                        bSkipThis = True

                if bSkipThis: continue #del files_with_ext[files_with_ext.index(filePath)]
                yield filePath

            #if not existing: print(f"  Skipped: {skipCountExists} already existing | {skipCountBlacklist} found in blacklist")
            #else: print(f"  Skipped: {skipCountBlacklist} found in blacklist")

def get_crc(fpath: Path):
    crc = 0
    with open(fpath, 'rb', 65536) as ins:
        for _ in range(int((os.stat(fpath).st_size / 65536)) + 1):
            crc = zlib.crc32(ins.read(65536), crc)
    return '%08X' % (crc & 0xFFFFFFFF)

def combine_files(*items):
     for lst in items:
        yield from lst

from re import split as regexsplit
def getKV(kvfilepath: Path) -> dict:
    KeyValues = {}
    with open(kvfilepath, 'r') as kvfile:
        for line in kvfile:
            line = line.strip().split("//", 1)[0].lower()
            if not line or line.startswith('/'): continue
            if skipNextLine:
                if "]" in line or "}" in line:
                    skipNextLine = False
                continue
            else:
                words = []
                # doesn't split inside qotes
                words = regexsplit(r'\s', line, maxsplit=1) #+(?=(?:[^"]*"[^"]*")*[^"]*$)
                words = list(filter(len, words))
                if not words: return
                key = words[0].strip('"').lower()
                if not key.startswith('$'): return
                val = words[1].lower().strip().strip('"')
                KeyValues[key] = val
            if "}" in line:break
    return KeyValues

def GetJson(jsonPath: Path, bCreate: bool = False) -> dict:
    if not jsonPath.exists():
        if bCreate: open(jsonPath, 'a').close()
        return {}
    with open(jsonPath) as fp:
        try:
            return json.load(fp)
        except json.decoder.JSONDecodeError:
            return {}

def UpdateJson(jsonPath: Path, update: dict) -> dict:
    with open(jsonPath, 'w+') as fp:
        try: stored = json.load(fp)
        except json.decoder.JSONDecodeError:
            stored = {}
        stored.update(update)
    
        json.dump(update, fp, sort_keys=True, indent=4)
    return #stored


from functools import wraps
def add_method(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, func.__name__, wrapper)
        return func
    return decorator

if not hasattr(Path, 'is_relative_to'):
    @add_method(Path)
    def is_relative_to(path: Path, rel_path: Path) -> bool: # Borrowed from 3.9
        """Return True if the path is relative.
        """
        try:
            path.relative_to(rel_path)
            return True
        except ValueError:
            return False
    Path.is_relative_to = is_relative_to #pylint complaining

@add_method(Path)
def MakeDir(self):
    "Creates directory tree"
    self.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print("Hi")
    fs = Source("materials", r"D:\Games\steamapps\common\Half-Life Alyx\game\csgo\materials", r"D:\Games\steamapps\common\Half-Life Alyx\content\csgo_imported\materials")
    path = Path(r"materials\models\weapons\rif_ak47\ak47.vmt")
    print("FullDir\t\t", fs.FullDir(path))
    print("LocalDir\t", fs.LocalDir(path))
    print("LocalDir_Legacy\t", fs.LocalDir_Legacy(path))
    print("NoSpace\t\t", fs.NoSpace(path.with_name("aaaa .vmt")))
    print("FixLegacyLocal\t", fs.FixLegacyLocal(path))
    print("Input\t\t", fs.Input(path))
    print("Output\t\t", fs.Output(path))
    input()
    quit()
