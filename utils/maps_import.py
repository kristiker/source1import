import sys
if sys.version_info.minor != 8:
    print("Python version 3.8 is required")
    sys.exit(1)
from shared.maps.clean import _load_solid
from typing import Literal, Union
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
    _VectorArray as vector_array,
    _Vector2Array as vector2_array,
    _Vector3Array as vector3_array,
    _Vector4Array as vector4_array,

)
from shared.datamodel import Vector2, Vector3, Vector4
string = str

"""
Silly vmf to vmap test
"""

# https://developer.valvesoftware.com/wiki/Valve_Map_Format

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
    boilerplate = dmx.load("utils/dev/empty.vmap.txt")
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
            if hasattr(v, 'get_element'):
                v = v.get_element(dm)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if hasattr(item, 'get_element'):
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
        print("Translating", k, v)
        if k not in self.__annotations__:
            return v
        _type = self.__annotations__[k]
        if issubclass(_type, list):
            if issubclass(_type, dmx._Array):
                #print(v, "->", v.split(), "-> make_array", _type)
                return dmx.make_array(v.split(), _type)
            else:
                #print(v, "->", v.split(), "-> vec[n]", _type)
                return _type(v.split())
        #print(v, "->", _type(v))
        
        return _type(v)

    @classmethod
    def FromKeyValues(cls, KV: KV):
        t = cls()
        baseDict = {}
        editorDict = {}
        for k, v in KV.items():
            if k == 'id':
                t.nodeID = t.Value_to_Value2('nodeID', v)
            elif k == 'name':
                t.name = v
            elif k in cls.__annotations__:
                print("caling v_v2")
                baseDict[k] = t.Value_to_Value2(k, v)
            elif not isinstance(v, dict):
                editorDict[k] = v
            else:
                print("Unknown editor object", k, type(v))
        t.__dict__.update(baseDict)
        if hasattr(t, 'entity_properties'):
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

    @classmethod
    def TRANSLATE(cls, versioninfo, visgroups,):
        ...

    class CMapGroup(_BaseNode):
        pass

    class CMapMesh(_BaseNode):
        class CDmePolygonMesh(_CustomElement):
            class CDmePolygonMeshDataArray(_CustomElement):
                size: int = 0
                streams: element_array = factory(element_array)
            class CDmePolygonMeshSubdivisionData(_CustomElement):
                subdivisionLevels: int_array = factory(int_array)
                streams: element_array = factory(element_array)

            # above element_array participant
            class CDmePolygonMeshDataStream(_CustomElement):
                standardAttributeName: str = "textureAxisU"#Literal[, ""]
                semanticName: str = "textureAxisU"
                semanticIndex: int = 0
                vertexBufferLocation: int = 0
                dataStateFlags: int = 0
                subdivisionBinding: dmx.Element = None#NullElement = 
                data: Union[vector2_array, vector3_array, vector4_array]

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

            def __post_init__(self):
                self.faceData.streams.extend([
                self.CDmePolygonMeshDataStream(
                    name='textureScale:0',
                    standardAttributeName='textureScale',
                    semanticName='textureScale',
                    data=vector2_array()
                ),
                self.CDmePolygonMeshDataStream(
                    name='textureAxisU:0',
                    standardAttributeName='textureAxisU',
                    semanticName='textureAxisU',
                    data=vector4_array([])
                ),
                self.CDmePolygonMeshDataStream(
                    name='textureAxisV:0',
                    standardAttributeName='textureAxisV',
                    semanticName='textureAxisV',
                    data=vector4_array([])
                ),
                self.CDmePolygonMeshDataStream(
                    name='materialindex:0',
                    standardAttributeName='materialindex',
                    semanticName='materialindex',
                    dataStateFlags=8,
                    data=int_array()
                ),
                self.CDmePolygonMeshDataStream(
                    name='flags:0',
                    standardAttributeName='flags',
                    semanticName='flags',
                    dataStateFlags=3,
                    data=int_array()
                ),
                self.CDmePolygonMeshDataStream(
                    name='lightmapScaleBias:0',
                    standardAttributeName='lightmapScaleBias',
                    semanticName='lightmapScaleBias',
                    dataStateFlags=1,
                    data=int_array()
                ),
            ])
            def add_face(self, id: int, textureScale: Vector2,
                textureAxisU: Vector4,
                textureAxisV: Vector4,
                materialindex: int, lightmapScaleBias: int
                ):
                self.faceData.streams[0].data.append(textureScale)
                self.faceData.streams[1].data.append(textureAxisU)
                self.faceData.streams[2].data.append(textureAxisV)
                self.faceData.streams[3].data.append(materialindex)
                self.faceData.streams[4].data.append(lightmapScaleBias)
                

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
        tintColor: color = factory(lambda: color([255,255,255,255]))
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

    class CMapEntity(_BaseEnt):
        hitNormal: vector3 = factory(lambda:vector3([0,0,1]))
        isProceduralEntity: bool = False

        @classmethod
        def FromKeyValues(cls, KV: KV):
            editorDict = {}
            if KV.get('editor') is not None:
                editorDict.update(KV.pop('editor'))
            
            if 'uniformscale' in KV:
                KV['scales'] = KV['uniformscale']
                del KV['uniformscale']
            rv = super(cls, cls).FromKeyValues(KV)
            #print(rv)
            rv.entity_properties.__dict__.update(editorDict)
            return rv

    nextDecalID: int = 0
    fixupEntityNames: bool = True
    mapUsageType: str = "standard"

    @classmethod
    def FromKeyValues(cls, KV: KV):
        children = []
        grouped_children = {}
        for (i, key), value in KV.items(indexed_keys=True):
            if key == 'solid':
                groupid, t_mesh = cls.translate_solid(value)
                if groupid != None:
                    grouped_children.setdefault(groupid, []).append(t_mesh)
                else:
                    children.append(t_mesh)
        base = super().FromKeyValues(KV) # Base worldspawn entity properties.
        world = cls(**base.__dict__)
        world.children.extend(children)
        return world
    
    @staticmethod
    def translate_solid(keyvalues):
        groupid = keyvalues.get('editor', {}).get('groupid')
        mesh = CMapWorld.CMapMesh.FromKeyValues(keyvalues)
        
        origin, vertex_data = _load_solid(keyvalues, 'worldspawn')

        mesh.origin = Vector3(list(origin))
        mesh.meshData.vertexData.size = len(vertex_data)
        mesh.meshData.vertexData.streams.append(
           mesh.meshData.CDmePolygonMeshDataStream(
                name='position:0',
                standardAttributeName='position',
                semanticName='position',
                dataStateFlags=3,
                data=vector3_array(
                    sorted(vertex_data, key=lambda v: {0:2, 1:3, 2:6, 3:1, 4:7, 5:1, 6:5, 7:4}[vertex_data.index(v)])
                )
            )
        )
        mesh.meshData.faceVertexData.streams.extend([
            mesh.meshData.CDmePolygonMeshDataStream(
                name='texcoord:0',
                standardAttributeName='texcoord',
                semanticName='texcoord',
                dataStateFlags=1,
                data=vector2_array([[1,1],[0,0],[1,-1],[0,0],[-1,-1],[0,0],[-1,1],[0,0]])
            ),
            mesh.meshData.CDmePolygonMeshDataStream(
                name='normal:0',
                standardAttributeName='normal',
                semanticName='normal',
                dataStateFlags=1,
                data=vector3_array([[0,0,1],[0,0,0],[0,0,1],[0,0,0],[0,0,1],[0,0,0],[0,0,1],[0,0,0]])
            ),
            mesh.meshData.CDmePolygonMeshDataStream(
                name='tangent:0',
                standardAttributeName='tangent',
                semanticName='tangent',
                dataStateFlags=1,
                data=vector4_array([[1,0,0,-1],[0,0,0,0],[1,0,0,-1],[0,0,0,0],[1,0,0,-1],[0,0,0,0],[1,0,0,-1],[0,0,0,0]])
            ),
        ])
        mesh.meshData.edgeData.streams.append(
            mesh.meshData.CDmePolygonMeshDataStream(
                name='flags:0',
                standardAttributeName='flags',
                semanticName='flags',
                dataStateFlags=3,
                data=int_array([0, 0, 0, 0])
            ),
        )
        # For each side...
        for (i, key), side_kv in keyvalues.items(indexed_keys=True):
            if key != 'side':
                continue
            # Texture Data
            mesh.meshData.materials.append(f"materials/{side_kv['material'].lower()}.vmat")
            usplit = side_kv['uaxis'].split()
            vsplit = side_kv['vaxis'].split()
            mesh.meshData.add_face(side_kv['id'],
                textureScale=Vector2((float(usplit[-1]), float(vsplit[-1]))),
                textureAxisU=Vector4([int(n.strip('[]')) for n in usplit[:-1]]),
                textureAxisV=Vector4([int(n.strip('[]')) for n in usplit[:-1]]),
                materialindex=len(mesh.meshData.materials),
                lightmapScaleBias=int(side_kv['lightmapscale'])
            )

        return groupid, mesh.get_element(vmap)
        
    @staticmethod
    def translate_ent(keyvalues):
        classname = keyvalues['classname']

        t_ent = CMapWorld.CMapEntity.FromKeyValues(keyvalues)
        print(vmap['world'], type(vmap['world']), vmap['world'].__dict__)
        vmap['world']['children'].append(
            t_ent.get_element(vmap)
        )
        return t_ent

'(%f %f %f) (%f %f %f) (%f %f %f)'
def translate_world(keyvalues):
    t_world = CMapWorld.FromKeyValues(keyvalues)#dmx.Element(vmap, 's1imported_world', 'CMapWorld')
    #print("|||||||||||||||||||||")
    #print(t_world)
    #print("--->>>>>>>>>>>>>>>>>")
    #print(t_world.get_element(vmap).items())
    #print("____________________")

    """Update the prefab empty world with our vmf translated world"""
    vmap['world'].update(t_world.get_element(vmap).items())

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

if __name__ == "__main__":
    #print('Source 2 VMAP TXT Generator!')

    vmf = KV.CollectionFromFile("utils/dev/literal_box.vmf", case_sensitive=True)
    vmap_dmx = dmx.load("utils/dev/box.vmap.txt")
    if False: # codegen
        # TODO: default factory value lambda:
        for k, v in vmap_dmx.root['world']['children'][0]['meshData']['edgeData']['streams'][0].items():
            print(f"{k}: {type(v).__name__} = {v if not issubclass(type(v), list) else 'factory('+ type(v).__name__+')'}")
        quit()
    elif True:
        out_vmap = create_fresh_vmap()
        vmap = out_vmap.root
        
        i, mesh = CMapWorld.translate_solid(vmf['world']['solid'])
    
        print()
        print()
        #print(vmap.get_kv2())

        vmap['world']['children'].append(
            #CMapWorld.CMapGroup.get_element(vmap)
            mesh
        )
        out_vmap.write("utils/dev/test.vmap.txt", 'keyvalues2', 4)
        #print(vmap.get_kv2())
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
        CMapWorld.translate_ent(value)

    out_vmap.write("utils/dev/out.vmap.txt", 'keyvalues2', 4)
