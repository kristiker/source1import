import sys, os
from types import ModuleType
from typing import Any, Callable
from pathlib import Path
import itertools

WINDOWS = os.name == "nt"
VTF_PRESENT = Path("source_game/materials/ads/ad01.vtf").is_file()

CAN_DECOMPILE_VTF = WINDOWS and VTF_PRESENT
print("Can decompile VTF:", CAN_DECOMPILE_VTF)

os.chdir(Path(__file__).parent)
sys.path.append("../utils")

import functools
def workflow(*modules: tuple[ModuleType, dict[str, Any]]):
    def inner(f: Callable):
        out = Path(f"source2_{f.__name__}_game").resolve()
        for file in out.glob("**/*"):
            if file.is_file():
                if file.suffix == ".tga" and not CAN_DECOMPILE_VTF:
                    continue
                # delete the missed .tga (product of materials_import)
                if file.name.endswith(".sheet.json") and not CAN_DECOMPILE_VTF:
                    atlas = Path(file.parent, file.name.removesuffix(".sheet.json") + ".tga")
                    if atlas.is_file():
                        atlas.unlink()
                file.unlink()

        @functools.wraps(f)
        def wrapper():
            for module, options in modules:
                module.sh.MOCK = True
                module.sh.update_destmod(module.sh.eS2Game(f.__name__))
                module.sh.args_known.src1gameinfodir = "source_game"
                module.sh.parse_in_path()
                module.sh.parse_out_path(out)
                if module == materials_import:
                    #module.sh.filter_ = r"*materials/fedio/models/dxconditionals.vmt"
                    ...
                #else:
                #    continue
                for name, value in options.items():
                    if hasattr(module, name):
                        setattr(module, name, value)
                if module == vtf_to_tga and not WINDOWS:
                    continue
                f(module)
                if module == models_import:
                    # delete these copied files that have no changes
                    # in smd the bone names are changed
                    for file in itertools.chain(
                        module.sh.output("models").rglob('*.qc'),
                        module.sh.output("models").rglob('*.qci'),
                        module.sh.output("models").rglob('*.smd'),
                        module.sh.output("models").rglob('*.dmx'),
                        module.sh.output("models").rglob('*.fbx'),
                        module.sh.output("models").rglob('*.vta'),
                    ):
                        file.unlink()
        return wrapper
    return inner

import materials_import
import particles_import
import scripts_import
import scenes_import
import maps_import
import models_import
import vtf_to_tga


@workflow(
    (vtf_to_tga, {}),
    (materials_import, {}),
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
    (maps_import, {}),
    (models_import, {
        "IMPORT_MDL": True,
        "IMPORT_QC": True,
        "COPY_FROM_SRC1_DIR": True,
    }),
    (scenes_import, {}),
)
def hlvr(module: ModuleType):
    module.main()



@workflow(
    (vtf_to_tga, {}),
    (materials_import, {}),
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
    (vtf_to_tga, {}),
    (materials_import, {}),
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

@workflow(
    (vtf_to_tga, {}),
    (materials_import, {}),
)
def steamvr(module: ModuleType):
    module.main()

@workflow(
    (vtf_to_tga, {}),
    (materials_import, {})
)
def cs2(module: ModuleType):
    module.main()

hlvr()
sbox()
adj()
steamvr()
cs2()
