import sys, os
from types import ModuleType
from typing import Any, Callable
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.append("../utils")

import functools
def workflow(*modules: tuple[ModuleType, dict[str, Any]]):
    def inner(f: Callable):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for module, options in modules:
                module.sh.update_destmod(module.sh.eS2Game(f.__name__))
                module.sh.args_known.src1gameinfodir = "source_game"
                module.sh.parse_in_path()
                module.sh.parse_out_path(Path(f"source2_{f.__name__}_game").resolve())
                for name, value in options.items():
                    if hasattr(module, name):
                        setattr(module, name, value)
                f(module)
        return wrapper
    return inner

import particles_import
import scripts_import
import scenes_import



@workflow(
    (particles_import, {
        "OVERWRITE_PARTICLES": True,
        "OVERWRITE_VSNAPS": True,
        "BEHAVIOR_VERSION": 12,
    }),
    (scripts_import, {
        "OVERWRITE_ASSETS": True,
        "SOUNDSCAPES": True,
        "GAMESOUNDS": True,
        "SURFACES": True,
        "MISCELLANEOUS": True,
    }),
    (scenes_import, {}),
)
def hlvr(module: ModuleType):
    module.main()



@workflow(
    (scripts_import, {
        "OVERWRITE_ASSETS": True,
        "SOUNDSCAPES": True,
        "GAMESOUNDS": True,
        "SURFACES": True,
        "MISCELLANEOUS": False,
    }),
)
def sbox(module: ModuleType):
    module.main()



@workflow(
    (scripts_import, {
        "OVERWRITE_ASSETS": True,
        "SOUNDSCAPES": False,
        "GAMESOUNDS": False,
        "SURFACES": False,
        "MISCELLANEOUS": True,
    }),
)
def adj(module: ModuleType):
    module.main()


hlvr()
sbox()
adj()
