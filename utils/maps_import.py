
from dataclassy import dataclass, factory
import shared.base_utils2 as sh
import vdf
from pathlib import Path
import shared.datamodel as dmx
from shared.datamodel import (
    uint64,
    Vector3 as vector3,
    QAngle as qangle,
    Color as color,
    _ElementArray as element_array,
    _IntArray as int_array,
    _StrArray as string_array,
)

OVERWRITE_MAPS = False
#WRITE_TO_PREFAB = True

maps = Path("maps")

def main():
    print("Importing maps (entities only)!")
    for vmf_path in sh.collect(maps, ".vmf", ".vmap", OVERWRITE_MAPS):
        ImportVMFToVMAP(vmf_path)

    print("Looks like we are done!")

def ImportVMFToVMAP(vmf_path):

    vmap_path = sh.output(vmf_path, ".vmap")
    vmap_path.parent.MakeDir()

    sh.status(f'- Reading {vmf_path.local}')
    with open(vmf_path) as fp:
        vmf: vdf.VDFDict = vdf.load(fp, mapper=vdf.VDFDict, merge_duplicate_keys=False)#KV.CollectionFromFile(vmf_path, case_sensitive=True)

    out_vmap = create_fresh_vmap()
    vmap = out_vmap.root

    #merge_multiple_worlds() use latest properties
    for key, value in vmf.items():
        # dismiss excess base keys (exlcuding entity)
        if len(vmf.get_all_for(key)) > 1 or key in (base_vmf.world, base_vmf.entity):
            continue
        main_to_root(vmap, key, value)

    for vmfEntityKeyValues in vmf.get_all_for("entity"):
        t_ent = CMapWorld.CMapEntity.FromVMFEntity(vmfEntityKeyValues)
        vmap["world"]["children"].append(
            t_ent.get_element(vmap)
        )

    out_vmap.write(vmap_path, "keyvalues2", 4)
    print("+ Generated", vmap_path.local)
    return vmap_path

from enum import Enum
class base_vmf(str, Enum):
    versioninfo = "versioninfo"
    visgroups = "visgroups"
    viewsettings = "viewsettings"
    world = "world"
    entity = "entity"
    hidden = "hidden"
    cameras = "cameras"
    cordon = "cordon"
    cordons = "cordons"

def create_fresh_vmap() -> dmx.DataModel:
    boilerplate = dmx.load("utils/shared/empty.vmap.txt")
    boilerplate.prefix_attributes.type = "$prefix_element$"
    return boilerplate

@dataclass
class _CustomElement:
    name: str = ""
    def get_element(self, dm: dmx.DataModel) -> dmx.Element:
        "py object 2 datamodel element"
        el = dmx.Element(dm, self.name, self.__class__.__name__)
        for k, v in self.__dict__.items():
            if k == "name":
                continue
            if hasattr(v, "get_element"):
                v = v.get_element(dm)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if hasattr(item, "get_element"):
                        v[i] = item.get_element(dm)
            el[k] = v
        return el

class _BaseNode(_CustomElement):
    origin: vector3 = factory(lambda:vector3([0,0,0]))
    angles: qangle = factory(lambda:qangle([0,0,0]))
    scales: vector3 = factory(lambda:vector3([1,1,1]))
    nodeID: int = 0  # Increase with every instance
    referenceID: uint64 = uint64(0x0)  # idk
    children: element_array = factory(element_array)
    editorOnly: bool = False
    force_hidden: bool = False
    transformLocked: bool = False
    variableTargetKeys: string_array = factory(string_array)
    variableNames: string_array = factory(string_array)

    def Value_to_Value2(self, k, v):
        "generic KV1 str value to typed KV2 value"
        
        if k not in self.__annotations__:
            return v
        _type = self.__annotations__[k]

        if issubclass(_type, list):
            if issubclass(_type, dmx._Array):
                return dmx.make_array(v.split(), _type)
            else:
                return _type(v.split())
            
        return _type(v)

    @classmethod
    def FromKeyValues(cls, KV: vdf.VDFDict): # keyvalues of who's?
        t = cls()
        baseDict = {}
        editorDict = {}
        for k, v in KV.items():
            if k == "id":
                t.nodeID = t.Value_to_Value2("nodeID", v)
            elif k == "name":
                t.name = v
            elif k in cls.__annotations__:
                #print("caling v_v2")
                baseDict[k] = t.Value_to_Value2(k, v)
            elif not isinstance(v, dict):
                editorDict[k] = v
            #else:
            #    print("Unknown editor object", k, type(v))
        t.__dict__.update(baseDict)
        if hasattr(t, "entity_properties"):
            t.entity_properties.__dict__.update(editorDict)
        return t

class _BaseEnt(_BaseNode):#(_T):
    class DmePlugList(_CustomElement):
        names: string_array = factory(string_array)
        dataTypes: int_array = factory(int_array)
        plugTypes: int_array = factory(int_array)
        descriptions: string_array = factory(string_array)
    
    class EditGameClassProps(_CustomElement):
        # Everything is a string
        def __init__(self, **kv: str):
            self.__dict__.update(**kv)

    relayPlugData: DmePlugList = factory(DmePlugList)
    connectionsData: element_array = factory(element_array)
    entity_properties: EditGameClassProps = factory(EditGameClassProps)


class CMapWorld(_BaseEnt):

    class CMapGroup(_BaseNode):
        pass

    class CMapEntity(_BaseEnt):
        hitNormal: vector3 = factory(lambda:vector3([0,0,1]))
        isProceduralEntity: bool = False

        @classmethod
        def FromVMFEntity(cls, KV: vdf.VDFDict):
            classname = KV.get("classname")
            editorDict = {}
            if KV.get("editor") is not None:
                editorDict.update(KV.pop("editor"))
            
            # Add your translations here
            # TODO: not here

            if classname in ("info_player_terrorist", "info_player_counterterrorist"):
                KV["classname"] = "info_player_spawn"

            if classname == "prop_static":
                # color and alpha are merged into a vec4
                if "color" in KV:
                    KV["rendercolor"] = f'{KV.pop("color")} {KV.pop("renderamt")}'
                if "rendercolor" in KV:
                    KV["rendercolor"] = f'{KV.pop("rendercolor")} {KV.pop("renderamt")}'

                # from ('uniformscale' '1') to ('scales', '1 1 1')
                if "uniformscale" in KV:
                    KV["scales"] = " ".join([KV.pop("uniformscale")]*3)
                
                if "model" in KV:
                    KV["model"] = Path(KV["model"]).with_suffix(".vmdl").as_posix()
            
            if classname == "etc":
                ...

            rv = super(cls, cls).FromKeyValues(KV)
            rv.entity_properties.__dict__.update(editorDict)
            return rv

    nextDecalID: int = 0
    fixupEntityNames: bool = True
    mapUsageType: str = "standard"

    @classmethod
    def FromVMFWorld(cls, worldKV: vdf.VDFDict):
        for (i, key), value in worldKV.items(indexed_keys=True):
            if key in ("solid", "group", "hidden"):
                continue
        base = super().FromKeyValues(worldKV) # Base worldspawn entity properties.
        world = cls(**base.__dict__)
        return world

RootDict = {
    "versioninfo":{
        "prefab": ("isprefab", bool),
    },
    "visgroups":{},
    "viewsettings":{
        "bShowGrid": ("showgrid", bool),
        "nGridSpacing": ("gridspacing", float),
        "bShow3DGrid": ("show3dgrid", bool),
    },
    "world":{},"entity":{},"hidden":{},"cameras":{},"cordon":{},"cordons":{},
}
def main_to_root(vmap, main_key: str, sub):
    for t in RootDict[main_key]:
        if t in sub:
            replacement, _type = RootDict[main_key][t]
            vmap[replacement] = _type(sub[t])

if __name__ == '__main__':
    sh.parse_argv()
    main()
