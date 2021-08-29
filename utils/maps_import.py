from dataclassy import dataclass, factory
import shared.base_utils2 as sh
from shared.keyvalues1 import KV
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
string = str

@sh.s1import('.vmf')
def ImportVMFtoVMAP_TXT(vmf_path, vmap_path, move_s1_assets = False):
    print(vmf_path)    
    print('+ Generated', vmap_path.local)
    return vmap_path

from enum import Enum
class m(str, Enum):
    versioninfo = 'versioninfo'
    visgroups = 'visgroups'
    viewsettings = 'viewsettings'
    world = 'world'
    entity = 'entity'
    hidden = 'hidden'
    cameras = 'cameras'
    cordon = 'cordon'
    cordons = 'cordons'

def create_fresh_vmap():
    #out_vmap.prefix_attributes
    #out_vmap.add_element("", "$prefix_element$")['map_asset_references'] = dmx.make_array([], str)
    #rv.root = rv.add_element("s1imported_map", "CMapRootElement")
    boilerplate = dmx.load("utils/dev/empty.vmap.txt")
    boilerplate.prefix_attributes.type = "$prefix_element$"
    #vmap = dmx.DataModel('vmap', 29)
    #vmap.root = vmap.add_element("s1imported_map", "CMapRootElement")
    #vmap.root.update(boilerplate.root)
    
    return boilerplate
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
def main_to_root(main_key: str, sub):
    for t in RootDict[main_key]:
        if t in sub:
            replacement, _type = RootDict[main_key][t]
            vmap[replacement] = _type(sub[t])

class _SubElement:
    def __new__(cls, *args):
        if cls is not _SubElement:
            print("_SubElement -> ", cls.__name__)
            dc = super(_SubElement, cls).__new__(cls, *args)
            el = dmx.Element(vmap, "", elemtype=cls.__name__)
            el.update(dc.__dict__)
            return el
        return super(_SubElement, cls).__new__(cls, *args)

class EditGameClassProps(_SubElement):
    # Everything is a string
    def __init__(self, **kv: str):
        self.__dict__.update(**kv)

@dataclass
class DmePlugList(_SubElement):
    names: string_array = factory(string_array)
    dataTypes: int_array = factory(int_array)
    plugTypes: int_array = factory(int_array)
    descriptions: string_array = factory(string_array)

@dataclass
class _BaseEnt:#(_T):
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
    relayPlugData: DmePlugList = factory(DmePlugList)
    connectionsData: element_array = factory(element_array)
    entity_properties: EditGameClassProps = factory(EditGameClassProps)

    def Value_to_Value2(self, k, v):
        "generic KV1 str value to typed KV2 value"
        print("Translating", k, v)
        if k not in self.__annotations__:
            return v
        _type = self.__annotations__[k]
        if issubclass(_type, list):
            if issubclass(_type, dmx._Array):
                print(v, "->", v.split(), "-> make_array", _type)
                return dmx.make_array(v.split(), _type)
            else:
                print(v, "->", v.split(), "-> vec[n]", _type)
                return _type(v.split())
        print(v, "->", _type(v))
        
        return _type(v)

    @classmethod
    def FromKeyValues(cls, KV: KV):
        t = cls()
        baseDict = {}
        editorDict = {}
        for k, v in KV.items():
            if k in ('id', 'name'):
                continue
            elif k in cls.__annotations__:
                print("caling v_v2")
                baseDict[k] = t.Value_to_Value2(k, v)
            elif not isinstance(v, dict):
                editorDict[k] = v
            else:
                print("Unknown editor object", k, type(v))
        t.__dict__.update(baseDict)
        t.entity_properties.update(editorDict)
        return t

@dataclass
class CMapWorld(_BaseEnt):
    @dataclass
    class CMapMesh(_BaseEnt):
        @dataclass
        class CDmePolygonMesh(_SubElement):
            @dataclass
            class CDmePolygonMeshDataArray(_SubElement):
                size: int = 8
                streams: element_array = factory(element_array)
            @dataclass
            class CDmePolygonMeshSubdivisionData(_SubElement):
                subdivisionLevels: int_array = factory(int_array)
                streams: element_array = factory(element_array)

            @dataclass  # above element_array participant
            class CDmePolygonMeshDataStream(_SubElement):
                ...

            vertexEdgeIndices: int_array = factory(int_array)
            vertexDataIndices: int_array = factory(int_array)
            edgeVertexIndices: int_array = factory(int_array)
            edgeOppositeIndices: int_array = factory(int_array)
            edgeNextIndices: int_array = factory(int_array)
            edgeFaceIndices: int_array = factory(int_array)
            edgeDataIndices: int_array = factory(int_array)
            edgeVertexDataIndices: int_array = factory(int_array)
            faceEdgeIndices: int_array = factory(int_array)
            faceDataIndices: int_array = factory(int_array)
            materials: string_array = factory(string_array)
            vertexData: CDmePolygonMeshDataArray = factory(CDmePolygonMeshDataArray)
            faceVertexData: CDmePolygonMeshDataArray = factory(CDmePolygonMeshDataArray)
            edgeData: CDmePolygonMeshDataArray = factory(CDmePolygonMeshDataArray)
            faceData: CDmePolygonMeshDataArray = factory(CDmePolygonMeshDataArray)
            subdivisionData: CDmePolygonMeshSubdivisionData = factory(CDmePolygonMeshSubdivisionData)

        cubeMapName: str = ""
        lightGroup: str = ""
        visexclude: bool = False
        renderwithdynamic: bool = False
        disableHeightDisplacement: bool = False
        fademindist: float = -1.0
        fademaxdist: float = 0.0
        bakelighting: bool = True
        precomputelightprobes: bool = True
        renderToCubemaps: bool = True
        disableShadows: bool = False
        smoothingAngle: float = 40.0
        tintColor: color = factory(color)
        renderAmt: int = 255
        physicsType: str = "default"
        physicsGroup: str = ""
        physicsInteractsAs: str = ""
        physicsInteractsWith: str = ""
        physicsInteractsExclude: str = ""
        meshData: CDmePolygonMesh = factory(CDmePolygonMesh)
        useAsOccluder: bool = False
        physicsSimplificationOverride: bool = False
        physicsSimplificationError: float = 0.0

    @dataclass
    class CMapEntity(_BaseEnt):
        hitNormal: vector3 = factory(lambda:vector3([0,0,1]))
        isProceduralEntity: bool = False

        @classmethod
        def FromKeyValues(cls, KV: KV):
            editorDict = {}
            if KV.get('editor') is not None:
                editorDict.update(KV.pop('editor'))
            rv = super(cls, cls).FromKeyValues(KV)
            print(rv)
            rv.entity_properties.update(editorDict)
            return rv

    nextDecalID: int = 0
    fixupEntityNames: bool = True
    mapUsageType: str = "standard"

    @classmethod
    def FromKeyValues(cls, KV: KV):
        editorDict = {}
        if KV.get('editor') is not None:
            editorDict.update(KV.pop('editor'))

        return super(cls, cls).FromKeyValues(KV)
    
    def translate_solid(s):
        ...
        

def translate_ent(keyvalues):
    classname = keyvalues['classname']

    t_ent = dmx.Element(vmap, '', 'CMapEntity')
    t_keyvalues = CMapWorld.CMapEntity.FromKeyValues(keyvalues).__dict__
    t_ent.update(t_keyvalues)

    vmap['world']['children'].append(t_ent)
    return t_ent

'(%f %f %f) (%f %f %f) (%f %f %f)'
def translate_world(keyvalues):
    t_world = CMapWorld.FromKeyValues(keyvalues).__dict__#dmx.Element(vmap, 's1imported_world', 'CMapWorld')
    t_world["nodeID"] = 1
    t_world["referenceID"] = uint64(0x0)

    vmap['world'].update(t_world)


if __name__ == "__main__":
    #print('Source 2 VMAP TXT Generator!')

    vmf = KV.CollectionFromFile("utils/dev/box.vmf", case_sensitive=True)
    vmap_dmx = dmx.load("utils/dev/box.vmap.txt")
    if False: # codegen
        # TODO: default factory value lambda:
        for k, v in vmap_dmx.root['world']['children'][0]['meshData']['subdivisionData'].items():
            print(f"{k}: {type(v).__name__} = {v if not issubclass(type(v), list) else 'factory('+ type(v).__name__+')'}")
        quit()
    out_vmap = create_fresh_vmap()
    vmap = out_vmap.root

    #merge_multiple_worlds() use latest properties
    for (i, key), value in vmf.items(indexed_keys=True):
        # dismiss excess main keys (exlcuding entity)
        if i >= 1 or key in (m.world, m.entity):
            continue
        main_to_root(key, value)

        #if key == m.entity:
        #    add_ent_to_world()
        #print(i, key, type(value))
    
    translate_world(vmf.get(m.world))

    for (i, key), value in vmf.items(indexed_keys=True):
        if key != m.entity:
            continue
        translate_ent(value)

    out_vmap.write("utils/dev/out.vmap.txt", 'keyvalues2', 4)
