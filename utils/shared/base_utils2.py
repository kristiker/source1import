
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from types import GeneratorType
from typing import Iterable


IMPORT_CONTENT = None
IMPORT_GAME = None
EXPORT_GAME = None
EXPORT_CONTENT = None

IMPORT_CONTENT =    Path(r'D:\Games\steamapps\common\Half-Life Alyx\content\csgo')
IMPORT_GAME =       Path(r'D:\Games\steamapps\common\Half-Life Alyx\game\csgo')
EXPORT_CONTENT =    Path(r'D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo')
EXPORT_GAME =       Path(r'D:\Games\steamapps\common\Half-Life Alyx\game\hlvr_addons\csgo')

importing = Path()

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

@add_property(Path)
def local(self):
    try: return self.relative_to(_src())
    except ValueError:
        return self.relative_to(import_context['dest'])

def output(input, out_ext=None, dest=_dest()) -> Path:
    out = dest / input.local
    if out_ext is not None:
        return out.with_suffix(out_ext)
    return out

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
            asset_out.parent.mkdir(parents=True, exist_ok=True)
            rv = function(asset_in, asset_out, **kwargs)
            return rv
        return wrapper
    return inner_function

from json import load as load_json
def _get_blacklist(root):
    json_path = Path(__file__).parent / "import_blacklist.json"
    try:
        with open(json_path, "r") as fp:
            return load_json(fp).get(str(root), set())
    except Exception as ex:
        print(type(ex), "COULDNT GET BLACKLIST", json_path)
        return set()


def collect(root, inExt, outExt, existing:bool = False, outNameRule = None, searchPath = None, match = None, skiplist = None):
    if not isinstance(outExt, (set, tuple, list)):
        outExt = ((outExt),) # support multiple output extensions

    #files_with_ext = []
    if searchPath is None:  searchPath = (_src() / root)
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
            bSkipThis = False
            if outNameRule:
                possibleNameList = outNameRule(filePath)
            else: possibleNameList = filePath
            if not isinstance(possibleNameList, (list, GeneratorType)): possibleNameList = [possibleNameList] # support multiple output names
            #try:
            # Attempt to see if you have an iterable object.
            for filePath2 in possibleNameList: # try a number of possible outputs. default is list() which will give one output
                if bSkipThis: break
                for outExt_ in outExt:
                    if bSkipThis: break
                    if not existing and output(filePath2, outExt_, import_context['dest']).exists():
                        skipCountExists += 1
                        bSkipThis = True
            #except TypeError:
                # some_thing_which_may_be_a_generator isn't actually a generator
                # do something else

            for skip_match in skiplist:
                if bSkipThis: break
                if (skip_match.replace("\\", "/") in filePath2.as_posix()) or filePath2.match(skip_match):
                    skipCountBlacklist += 1
                    bSkipThis = True

            if bSkipThis: continue #del files_with_ext[files_with_ext.index(filePath)]
            yield filePath

        print(' '*4 + f"Skipped: " + f"{skipCountExists} already imported | "*(not existing) +\
                                 f"{skipCountBlacklist} found in blacklist"
        )

__last_status_len = 0
def status(text):
    global __last_status_len
    print(f'{" "*__last_status_len}\r{text}', end='\r')
    __last_status_len = len(text)