
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from types import GeneratorType
try:
    from keyvalues1 import KV
except ImportError:
    from shared.keyvalues1 import KV

import argparse
arg_parser = argparse.ArgumentParser(usage = "-src1gameinfodir <s1gameinfodir> -game <s2 mod> [<src1 file or folder>]") # -filter <substring> [optional] Filter for matching files
arg_parser.add_argument("-src1gameinfodir", "-i", help="An absolute path to S1 mod gameinfo.txt.")
arg_parser.add_argument("-game", "-e", help="Specify the S2 mod/addon to import into (ie. left4dead2_source2 or C:/../ep2).")
#arg_parser.add_argument("-filter", "-filelist_filter", help="Apply a substring filter to the import filelist")

_args_known, args_unknown = arg_parser.parse_known_args()

'-src1gameinfodir "D:/Games/steamapps/common/Half-Life Alyx/game/csgo" -game hlvr_addons/csgo'

from enum import Enum
class eEngineFolder(Enum):
    "Source 2 main folders"
    ROOT = Path()
    CONTENTROOT = Path("content")
    GAMEROOT = Path("game")
    SRC = Path("src")
    BIN = GAMEROOT / "bin"
    CORE_GAME = GAMEROOT / "core"

def update_root(s2_root):
    "Update ROOT, as well as paths deriving from it (GAMEROOT, CONTENTROOT, SRC...)"
    for folder in eEngineFolder:
        if s2_root is None:
            globals()[folder.name] = None
            continue
        globals()[folder.name] = s2_root / folder.value

update_root(None)  # Add ROOT, CONTENTROOT, CORE_GAME... to globals() as None
IMPORT_CONTENT = None
IMPORT_GAME = None
EXPORT_CONTENT = None
EXPORT_GAME = None
#IMPORT_LEAFIEST_GAME,IMPORT_LEAFIEST_CONTENT,EXPORT_LEAFIEST_GAME,EXPORT_LEAFIEST_CONTENT
search_scope = None

def in_source2_environment():
    return ROOT is not None

def parse_paths():
    global IMPORT_CONTENT, IMPORT_GAME, EXPORT_CONTENT, EXPORT_GAME
    global search_scope
    def error(*args, **kwargs):
        print("ERROR:", *args, **kwargs)
        raise SystemExit(1)
    if not _args_known.src1gameinfodir:
        raise SystemExit(1)
    in_path = Path(_args_known.src1gameinfodir)
    if not in_path.exists():
       error("src1 game path not found")
    if in_path.is_file() and in_path.name == 'gameinfo.txt':
        in_path = in_path.parent
    if not (in_path / 'gameinfo.txt').is_file():
        error(f"gameinfo.txt not found for src1 mod `{in_path.name}`")
    IMPORT_GAME = in_path
    if IMPORT_GAME.parent.name == 'game':  # Source 2 dir
        update_root(IMPORT_GAME.parents[1])
        IMPORT_CONTENT = CONTENTROOT / IMPORT_GAME.name
    if not _args_known.game:
        error(f"Missing required argument: -o\nUsage: {arg_parser.usage}")
    source2_mod = Path(_args_known.game)
    if source2_mod.is_absolute():
        if source2_mod.is_file():
            error("Cannot specify file as export game")
        for possible_rel in (GAMEROOT, CONTENTROOT):#, ROOT):
            if possible_rel is not None and source2_mod.is_relative_to(possible_rel):
                source2_mod = source2_mod.relative_to(possible_rel)
        if source2_mod.is_absolute():  # Relativity loop above didnt work
            for p_index, p in enumerate(source2_mod.parts[-3:-1]):
                if p in ('content', 'game'):  # has game/content at -2 or -3
                    p_index+=len(source2_mod.parts)-3
                    # Importing from a source 2 app into different source 2 app.
                    # Makes more sense to consider this as more appropriate root
                    update_root(Path(*source2_mod.parts[:p_index]))
                    source2_mod = Path(*source2_mod.parts[p_index:])
                    break
            if p not in ('content', 'game'):  # Export game has no game-content structure (sbox?)
                EXPORT_GAME = EXPORT_CONTENT = source2_mod
    elif not in_source2_environment():
        error("Please use absolute path as export path.")
    if len(source2_mod.parts) in (1, 2):
        EXPORT_GAME = GAMEROOT / source2_mod
        EXPORT_CONTENT = CONTENTROOT / source2_mod
    elif len(source2_mod.parts) == 3:
        # TEMP FIX FOR hlvr_addons
        EXPORT_GAME = GAMEROOT / source2_mod
        EXPORT_CONTENT = CONTENTROOT / source2_mod.relative_to(eEngineFolder.CONTENTROOT.value)
    elif EXPORT_GAME is EXPORT_CONTENT is None:
        error("Invalid export game", source2_mod)

    # Optionals

    # Unknowns
    if args_unknown:
        search_scope = Path(args_unknown[0])

if __name__ == '__main__':
    print(f"{parse_paths()}\n{ROOT=}\n{IMPORT_CONTENT=}\n{IMPORT_GAME=}\n{EXPORT_CONTENT=}\n{EXPORT_GAME=}")
    raise SystemExit

parse_paths()
importing = Path()

# default import context
import_context = {
    'mod': None,
    'recurse': True,
    'importfunc': 'integ',
    'src': IMPORT_GAME,
    'dest': EXPORT_CONTENT,
    'ignoresource2namefixup': False,
    'getSkinningFromLod0': False,
}
_mod = lambda: import_context['mod']
_recurse = lambda: import_context['recurse']
_src = lambda: import_context['src']
_dest = lambda: import_context['dest']

class KVUtilFile(KV):
    @classmethod
    def RemapTable(cls):
        cls.path = EXPORT_CONTENT / "source1import_name_remap_table.txt"
        keyName = "name_remap_table"

        def remap(self, extType: str, s1Name: str, s2Remap: str):
            # Remap. Don't remap and WARN if already remapped.
            if not isinstance(self.get(extType), dict):
                self[extType] = {}

            exist = self[extType].setdefault(s1Name, s2Remap)
            if exist != s2Remap:
                WARN(f"Remap entry for '{s1Name}' -> '{s2Remap}' conflicts with existing value of '{exist}' (ignoring)")

        cls.remap = remap
        rv = cls(keyName)
        if cls.path.is_file():
            rv.update(cls.FromFile(cls.path, case_sensitive=True))
        return rv

    def save(self):
        return super().save(self.path, quoteKeys=True)

RemapTable = KVUtilFile.RemapTable()

class Importable:
    src: Path = import_context['src']
    dest: Path = import_context['dest']
    _currentpath: Path = None
    params: dict

    @property
    def path(self):
        return self._currentpath

from functools import wraps
def add_property(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, func.__name__, property(fget=wrapper))
        return func
    return decorator

def add_method(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, func.__name__, wrapper)
        return func
    return decorator

@add_property(Path)
def local(self):
    try: return self.relative_to(_src())
    except ValueError:
        return self.relative_to(import_context['dest'])

@add_property(Path)
def legacy_local(self):
    return self.relative_to(_src() / importing)

@add_method(Path)
def without_spaces(self, repl = '_') -> Path:
    return self.parent / self.name.replace(' ', repl)

@add_method(Path)
def lowercase(self) -> Path:
    return Path(*(str(part).lower() for part in self.parts))

@add_method(Path)
def MakeDir(self):
    "parents=True, exist_ok=True"
    self.mkdir(parents=True, exist_ok=True)

def src(local_path) -> Path:
    return _src() / local_path

def output(input, out_ext=None, dest=_dest()) -> Path:
    try: out = dest / input.local
    except Exception: out = dest / input
    #out = source2namefixup(out)
    if out_ext is not None:
        return out.with_suffix(out_ext)
    return out

def source2namefixup(path):
    return path.parent / path.name.lower().replace(' ', '_')

#def overwrite_allowed(path, bAllowed=import_context['overwrite']):
#    return path.exists() and bAllowed

def s1import(out_ext=None, **ctx):
    if not ctx: ctx = import_context
    def inner_function(function):
        @wraps(function)
        def wrapper(asset_in: Path, asset_out: Path = None, **kwargs):
            for k in kwargs.copy():
                if k in import_context:
                    ctx[k] = kwargs[k]
                    kwargs.pop(k)
            if asset_out is None:
                asset_out = output(asset_in, out_ext, ctx['dest'])
            asset_out.parent.MakeDir()
            rv = function(asset_in, asset_out, **kwargs)
            return rv
        return wrapper
    return inner_function

def collect(root, inExt, outExt, existing:bool = False, outNameRule = None, searchPath = None, match = None, skiplist = None):
    if not isinstance(outExt, (set, tuple, list)):
        outExt = ((outExt),) # support multiple output extensions

    if searchPath is None:
        searchPath = (_src() / root)
        if search_scope is not None:
            try: searchPath = searchPath / search_scope.relative_to(root)
            except Exception: searchPath = searchPath / search_scope
    if skiplist is None:    skiplist = _get_blacklist(root)

    if searchPath.is_file():
        if searchPath.suffix == inExt:
            yield searchPath
        else: print(f"~ File suffix is not a {inExt}")

    elif searchPath.is_dir():
        skipCountExists, skipCountBlacklist = 0, 0
        print(f'\n- Searching %sfor%s %s files...' % (
            "non-recursively "*(not _recurse()),
            " unimported"*(not existing),
            f"[ {match} ]" if match else inExt,
        ))
        if match is None:
            match = ('**/'*_recurse()) + '*' + inExt  

        for filePath in searchPath.glob(match):
            skip_reason = ''
            if outNameRule:
                possibleNameList = outNameRule(filePath)
            else: possibleNameList = filePath
            if not isinstance(possibleNameList, (list, GeneratorType)): possibleNameList = [possibleNameList] # support multiple output names

            for filePath2 in possibleNameList: # try a number of possible outputs. default is list() which will give one output
                if skip_reason: break
                for outExt_ in outExt:
                    if skip_reason: break
                    if not existing and output(filePath2, outExt_, import_context['dest']).exists():
                        skipCountExists += 1
                        skip_reason = 'already-exist'

            for skip_match in skiplist:
                if skip_reason: break
                if (skip_match.replace("\\", "/") in filePath2.as_posix()) or filePath2.match(skip_match):
                    skipCountBlacklist += 1
                    skip_reason = 'blacklist'

            if skip_reason:
                status(f"- skipping [{skip_reason}]: {filePath2.local.as_posix()}")
                continue #del files_with_ext[files_with_ext.index(filePath)]
            yield filePath

        print()
        print(' '*4 + f"Skipped: " + f"{skipCountExists} already imported | "*(not existing) +\
                                 f"{skipCountBlacklist} found in blacklist"
        )
    else:
        print("ERROR while searching: Does not exist:", searchPath)

def write(content: str, path: Path):
    with open(path, 'w') as fp:
        fp.write(content)

DEBUG = False
def msg(*args, **kwargs):
    if DEBUG:
        print("@ DBG:", *args, **kwargs)

def warn(*args, **kwargs): print("WARNING:", *args, **kwargs)
def WARN(*args, **kwargs):  # TODO: source1importwarnings_lastrun.txt
    print("*** WARNING:", *args, **kwargs)

__last_status_len = 0
def status(text):
    global __last_status_len
    print(f'{" "*__last_status_len}\r{text}', end='\r')
    __last_status_len = len(text)

from os import stat
from zlib import crc32
def get_crc(fpath: Path):
    crc = 0
    with open(fpath, 'rb', 65536) as ins:
        for _ in range(int((stat(fpath).st_size / 65536)) + 1):
            crc = crc32(ins.read(65536), crc)
    return '%08X' % (crc & 0xFFFFFFFF)

import json
def _get_blacklist(root):
    json_path = Path(__file__).parent / "import_blacklist.json"
    try:
        with open(json_path, "r") as fp:
            return json.load(fp).get(str(root), set())
    except Exception as ex:
        print(type(ex), "COULDNT GET BLACKLIST", json_path)
        return set()

def GetJson(jsonPath: Path, bCreate: bool = False) -> dict:
    if not jsonPath.is_file():
        if bCreate:
            jsonPath.parent.MakeDir()
            open(jsonPath, 'a').close()
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