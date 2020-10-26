import argparse, os, json # pylint: disable=unused-import
from pathlib import Path
from enum import Enum
import types

class App(Enum):
    "Source 2 Application paths"
    CONTENT = Path("content")
    GAME = Path("game")
    BIN = GAME / Path("bin")

class IO:
    def __init__(self, scope: Path, inPath, outPath):
        self.SCRIPT_SCOPE = Path(scope) # doesn't really belong here
        self.IN_PATH, self.OUT_PATH = inPath, outPath

        self.arg_parser = argparse.ArgumentParser()
        self.arg_parser.add_argument('-i', default=self.IN_PATH, help="Input path. Can be a folder (recursive search) or file.")
        self.arg_parser.add_argument('-o', default=self.OUT_PATH, help="Output path. If omitted content will be output in the same place.")
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

        self.EXPORT_GAME = self.get_path_app(self.OUT_ROOT, App.GAME)
        self.EXPORT_CONTENT = self.get_path_app(self.OUT_ROOT, App.CONTENT)

        #self.currentDir = Path().cwd() #TODO: fix this shit so that it's actually reliable
        self.currentDir = Path(__file__).parent
        self.blacklist = self._get_blacklist()

        print(f"\nIN_PATH  {self.IN_PATH}\nOUT_PATH {self.OUT_PATH}")
        print(f"SEARCH   {self.SCRIPT_SCOPE.name.capitalize()}\nOVERWRITE", ("Yes" if self.SHOULD_OVERWRITE else "No"))

    def get_path_app(self, path, get:App = App.CONTENT):
        path_components = path.parts

        for gc in ("content", "game"):
            if gc not in path_components:
                return

            index_rightmost = len(path_components) - path_components[::-1].index(gc) - 1
            appPath = Path("/".join(path_components[:index_rightmost]))
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
        print(fr"         Single File C:\Games\steamapps\common\Left 4 Dead 2\left4dead2\{self.SCRIPT_SCOPE}\ads\burger_off.vmt")
        print()

        while not self.IN_PATH:
            print(f"Please type in the path containing your source 1 {self.SCRIPT_SCOPE} folder:")
            c = input(">>")
            if c in ('q', 'quit', 'exit', 'close'): quit()
            else: c = Path(c)
            if c.is_dir() or c.is_file():
                self.IN_PATH = c

        while not self.OUT_PATH:
            print("Please type in the path that will contain your imported content (enter blank to import in the same place)")
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
                return json.load(fp)[str( self.SCRIPT_SCOPE)]
        except: return []

class Source(IO):
    def __init__(self, scope = "", inPath = None, outPath = None):
        IO.__init__(self, scope, inPath, outPath)

    def FullDir(self, relPath: Path):
        "materials/texture_color.tga -> C:/Users/User/Desktop/stuff/materials/texture_color.tga"
        return self.IN_ROOT / relPath

    def LocalDir(self, path: Path) -> Path:
        "C:/Users/User/Desktop/stuff/materials/texture_color.tga -> materials/texture_color.tga"
        try: local = path.relative_to(self.OUT_ROOT)
        except:
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

    def MakeDir(self, path: Path):
        "Creates directory tree if nonexistent"
        #if path.is_file():
        #    print("IS file")
        #path.parent.mkdir(parents=True, exist_ok=True)
        path.mkdir(parents=True, exist_ok=True)
        #elif path.is_dir():
        #    print("IS fiaaale")
        #    path.mkdir(parents=True, exist_ok=True)
    
    def ShouldOverwrite(self, path: Path, custVar: bool = False) -> bool:
        if (self.SHOULD_OVERWRITE or custVar) or not path.exists():
            return True
        return False

    def IsInside(self, path: Path, rel_path: Path) -> bool:
        """Return True if the path is relative.
        """
        try:
            path.relative_to(rel_path)
            return True
        except ValueError:
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

            if not existing: print(f"  Skipped: {skipCountExists} already existing | {skipCountBlacklist} found in blacklist")
            else: print(f"  Skipped: {skipCountBlacklist} found in blacklist")


def IsInside(path: Path, rel_path: Path) -> bool:
    """Return True if the path is relative.
    """
    try:
        path.relative_to(rel_path)
        return True
    except ValueError:
        return False
Path.is_relative_to = IsInside

def combine_files(*items):
     for lst in items:
        yield from lst
