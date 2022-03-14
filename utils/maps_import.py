from itertools import islice, tee, zip_longest
import os
import sys

from prettytable import PrettyTable

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
import shared.dcel as dcel
string = str

"""
Silly vmf to vmap test 🔨
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
        """Group of CMapMesh-es"""
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
                NAME = Literal["position","textureScale","textureAxisU","textureAxisV","materialindex","flags","lightmapScaleBias","texcoord","normal","tangent"]
                standardAttributeName: NAME = ""
                semanticName: NAME = ""
                semanticIndex: int = 0
                vertexBufferLocation: int = 0
                dataStateFlags: int = 0
                subdivisionBinding: dmx.Element = None#NullElement = 
                data: Union[vector2_array, vector3_array, vector4_array]
                def __post_init__(self):
                    if not self.standardAttributeName:
                        self.standardAttributeName = self.name[:-2]
                    if not self.semanticName:
                        self.semanticName = self.name[:-2]


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
                self.vertexData.streams.append(
                    self.CDmePolygonMeshDataStream(
                        name='position:0',
                        dataStateFlags=3,
                        data=vector3_array()
                    )
                )
                self.faceData.streams.extend([
                    self.CDmePolygonMeshDataStream(
                        name='textureScale:0',
                        data=vector2_array()
                    ),
                    self.CDmePolygonMeshDataStream(
                        name='textureAxisU:0',
                        data=vector4_array([]) # x x x shift
                    ),
                    self.CDmePolygonMeshDataStream(
                        name='textureAxisV:0',
                        data=vector4_array([]) # x x x shift
                    ),
                    self.CDmePolygonMeshDataStream(
                        name='materialindex:0',
                        dataStateFlags=8,
                        data=int_array()
                    ),
                    self.CDmePolygonMeshDataStream(
                        name='flags:0',
                        dataStateFlags=3,
                        data=int_array()
                    ),
                    self.CDmePolygonMeshDataStream(
                        name='lightmapScaleBias:0',
                        dataStateFlags=1,
                        data=int_array()
                    ),
                ])
                self.faceVertexData.streams.extend([
                    self.CDmePolygonMeshDataStream(
                        name='texcoord:0',
                        dataStateFlags=1,
                        data=vector2_array()
                    ),
                    self.CDmePolygonMeshDataStream(
                        name='normal:0',
                        dataStateFlags=1,
                        data=vector3_array()
                    ),
                    self.CDmePolygonMeshDataStream(
                        name='tangent:0',
                        dataStateFlags=1,
                        data=vector4_array()
                    ),
                ])
                self.edgeData.streams.append(
                    self.CDmePolygonMeshDataStream(
                        name='flags:0',
                        dataStateFlags=3,
                        data=int_array()
                    )
                )

            def __repr__(self):
                e = PrettyTable(['E', 'O', 'N', 'F', 'V->D'])
                for i, v in enumerate(self.edgeVertexIndices):
                    arc = f"{v}->{self.edgeVertexIndices[self.edgeOppositeIndices[i]]}"
                    e.add_row([i, self.edgeOppositeIndices[i], self.edgeNextIndices[i], self.edgeFaceIndices[i], arc])
                return str(e)

            @property
            def halfList(self):
                "All halves, proper order."
                half_edges: list[dcel.half_edge] = []
                for i, (v0, v1) in enumerate(zip_longest(*[iter(self.edgeVertexIndices)]*2)):
                    half_edges.append(dcel.half_edge(origin=dcel.vertex(idx=v0,position=None), incident_face=dcel.face(self.edgeFaceIndices[2*i])))
                    half_edges.append(dcel.half_edge(origin=dcel.vertex(idx=v1,position=None), incident_face=dcel.face(self.edgeFaceIndices[2*i+1])))

                    # edgeOppositeIndices always the same, skip it
                    half_edges[i].opposite = half_edges[i+1]
                    half_edges[i+1].opposite = half_edges[i]
                
                for this_is_next_of, this in enumerate(self.edgeNextIndices):
                    half_edges[this].next = half_edges[this_is_next_of]
                
                return half_edges

            @classmethod
            def FromDCEL(cls, dcel: dcel.DCEL):
                """Code friendly Linked-list structure to array based serializable structure"""
                a = cls(name='meshData')
                vertex_count = dcel.vert_count
                edge_count = dcel.edge_count
                half_edge_count = dcel.edge_count*2
                face_count = dcel.face_count

                a.vertexEdgeIndices += [*range(vertex_count)]
                a.vertexDataIndices += [*range(vertex_count)]

                # prefill
                #a.edgeNextIndices = [None] * dcel.edge_count*2
                opposites = [None] * dcel.edge_count*2
                
                el = dcel.edgeList
                print(el)
                ## Start with an edge pointing at 0, incident to face0
                el.insert(1, el.pop(0))
                el.insert(1, el.pop())
                el = el[::-1]
                #el.insert(3, el.pop())
                #el.insert(0, el.pop())
                #el.append(el.pop(2))

                #el.insert(0, el.pop())
                #for i, edge in enumerate(dcel.edgeList):
                _order = []
                def this_specific_order(el):
                    for i in range(len(el)):
                        yield i, el[i]

                for i, edge in this_specific_order(el):
                    if i:
                        # Flip because we are clockwise, vmap has it counter-cw
                        edge = edge.opposite

                    #print(edge)
                    assert edge != edge.opposite
                    assert edge == edge.opposite.opposite
                    assert edge.opposite == edge.opposite.opposite.opposite
                    _order.append(edge)
                    _order.append(edge.opposite)
                    a.edgeVertexIndices.append(edge.origin.idx)
                    a.edgeVertexIndices.append(edge.opposite.origin.idx)
                    opposites[2*i]= 1 if not i else 2*i+1
                    opposites[2*i+1] = 2*i
                    a.edgeFaceIndices.append(max(edge.incident_face.idx, -1))
                    a.edgeFaceIndices.append(max(edge.opposite.incident_face.idx, -1))
                
                a.edgeOppositeIndices += opposites
                
                for i, edge in this_specific_order(el):
                    if i:
                        edge = edge.opposite
                    a.edgeNextIndices.append(_order.index(edge.previous)) 
                    a.edgeNextIndices.append(_order.index(edge.opposite.previous))
                    #a.edgeNextIndices[2*i] = _order.index(edge.previous)
                    #a.edgeNextIndices[2*i+1] = _order.index(edge.opposite.previous)

                # edgeDataIndices
                for n in range(edge_count):
                    a.edgeDataIndices += [n,n]
                # edgeVertexDataIndices
                a.edgeVertexDataIndices += [n for n in range(half_edge_count)]
                # faceEdgeIndices
                a.faceEdgeIndices.append(8)
                a.faceEdgeIndices.append(9)
                # faceDataIndices
                a.faceDataIndices+= [n for n in range(face_count)]
                self = a
                self.materials.append("materials/dev/reflectivity_30.vmat")
                # vertexData
                self.vertexData.size = vertex_count
                self.vertexData.streams[0].data += [ # position
                    Vector3("-3.5 -3.5 0".split()),
                    Vector3("3.5 -3.5 0".split()),
                    Vector3("-3.5 3.5 0".split()),
                    Vector3("3.5 3.5 0".split())
                ]
                # faceVertexData
                self.faceVertexData.size = half_edge_count
                self.faceVertexData.streams[0].data += [ # texcoord
                    Vector2("1 1".split()),
                    Vector2("0 0".split()),
                    Vector2("0 0".split()),
                    Vector2("0 0".split()),
                    Vector2("0 0".split()),
                    Vector2("0 1".split()),
                    Vector2("0 0".split()),
                    Vector2("1 0".split()),
                    Vector2("1 1".split()),
                    Vector2("0 0".split())
                ]
                self.faceVertexData.streams[1].data += [ # normal
                    Vector3("0 0 1".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("0 0 1".split()),
                    Vector3("0 0 1".split())
                ]
                self.faceVertexData.streams[2].data += [ # tangent
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("1 0 0 -1".split()),
                ]

                # edgeData
                self.edgeData.size = edge_count
                for n in range(edge_count):
                    self.edgeData.streams[0].data.append(0)

                # faceData
                self.faceData.size = face_count
                self.faceData.streams[0].data.append(Vector2("0.0137 0.0137".split()))
                self.faceData.streams[0].data.append(Vector2("0.0137 0.0137".split()))
                self.faceData.streams[1].data.append(Vector4("1 0 0 256".split()))
                self.faceData.streams[1].data.append(Vector4("1 0 0 256".split()))
                self.faceData.streams[2].data.append(Vector4("0 -1 0 256".split()))
                self.faceData.streams[2].data.append(Vector4("0 -1 0 256".split()))
                self.faceData.streams[3].data.append(0)
                self.faceData.streams[4].data.append(0)
                self.faceData.streams[5].data.append(0)
                self.faceData.streams[3].data.append(0)
                self.faceData.streams[4].data.append(0)
                self.faceData.streams[5].data.append(0)

                # subdivisionData
                for n in range(half_edge_count):
                    self.subdivisionData.subdivisionLevels.append(0)
                return a

            @classmethod
            def SampleTriangle(self):
                """
                test if you can even create a hammer polygon
                
                data from utils/dev/sample_triangle.vmap.txt
                """
                self = self(name='meshData')
                self.vertexEdgeIndices += [0, 3, 5]
                self.vertexDataIndices += [0, 1, 2]
                self.edgeVertexIndices += [1, 0, 1, 2, 2, 0]
                self.edgeOppositeIndices+=[1, 0, 3, 2, 5, 4]
                self.edgeNextIndices +=   [3, 4, 1, 5, 2, 0]
                self.edgeFaceIndices +=   [0,-1,-1, 0,-1, 0]
                # edgeDataIndices
                for n in range(3):
                    self.edgeDataIndices += [n,n]
                # edgeVertexDataIndices
                self.edgeVertexDataIndices += [n for n in range(6)]
                # faceEdgeIndices
                self.faceEdgeIndices.append(3)
                # faceDataIndices
                self.faceDataIndices.append(0)
                # materials
                self.materials.append("materials/dev/reflectivity_30.vmat")
                # vertexData
                self.vertexData.size = 3
                self.vertexData.streams[0].data += [
                    Vector3("-3 -3 0".split()),
                    Vector3("3 -3 0".split()),
                    Vector3("-3 3 0".split())
                ]
                # faceVertexData
                self.faceVertexData.size = 6
                for _ in range(6):
                    self.faceVertexData.streams[0].data.append(Vector2("0 0".split())) # texcoord
                self.faceVertexData.streams[1].data += [ # normal
                    Vector3("0 0 1".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 1".split())
                ]
                self.faceVertexData.streams[2].data += [ # tangent
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("1 0 0 -1".split())
                ]
                # edgeData
                for n in range(3):
                    self.edgeData.size+=1
                    self.edgeData.streams[0].data.append(0)
                # faceData
                self.faceData.size +=1
                self.faceData.streams[0].data.append(Vector2("0.25 0.25".split()))
                self.faceData.streams[1].data.append(Vector4("1 0 0 0".split()))
                self.faceData.streams[2].data.append(Vector4("0 -1 0 0".split()))
                self.faceData.streams[3].data.append(0)
                self.faceData.streams[4].data.append(0)
                self.faceData.streams[5].data.append(0)
                # subdivisionData
                for n in range(6):
                    self.subdivisionData.subdivisionLevels.append(0)

                return self

            @classmethod
            def SampleQuad(self):
                """
                sample hammer quad
                
                data from utils/dev/sample_quad.vmap.txt
                """
                self = self(name='meshData')
                if False:
                    self.vertexEdgeIndices +=   [0, 1, 2, 3]
                    self.vertexDataIndices +=   [0, 1, 2, 3]
                    self.edgeVertexIndices +=   [1, 0, 3, 2, 2, 0, 1, 3]
                    self.edgeOppositeIndices += [1, 0, 3, 2, 5, 4, 7, 6]
                    self.edgeNextIndices +=     [7, 4, 6, 5, 2, 0, 1, 3]
                    #[7, 4, 6, 5, 2, 8, 1, 9, 3, 0]
                    self.edgeFaceIndices +=     [0,-1,-1, 0,-1, 0,-1, 0]
                else:
                    PolygonMesh = dcel.e0.asArray()
                    self.vertexEdgeIndices += PolygonMesh.vertexEdgeIndices
                    self.vertexDataIndices += PolygonMesh.vertexDataIndices
                    self.edgeVertexIndices += PolygonMesh.edgeVertexIndices
                    self.edgeOppositeIndices += PolygonMesh.edgeOppositeIndices
                    self.edgeNextIndices += PolygonMesh.edgeNextIndices
                    self.edgeFaceIndices += PolygonMesh.edgeFaceIndices
                # edgeDataIndices
                for n in range(4):
                    self.edgeDataIndices += [n,n]
                # edgeVertexDataIndices
                self.edgeVertexDataIndices += [n for n in range(8)]
                # faceEdgeIndices
                self.faceEdgeIndices.append(3)
                # faceDataIndices
                self.faceDataIndices.append(0)
                # materials
                self.materials.append("materials/dev/reflectivity_30.vmat")
                # vertexData
                self.vertexData.size = 4
                self.vertexData.streams[0].data += [ # position
                    Vector3("-3.5 -3.5 0".split()),
                    Vector3("3.5 -3.5 0".split()),
                    Vector3("-3.5 3.5 0".split()),
                    Vector3("3.5 3.5 0".split())
                ]
                # faceVertexData
                self.faceVertexData.size = 8
                self.faceVertexData.streams[0].data += [ # texcoord
                    Vector2("1 1".split()),
                    Vector2("0 0".split()),
                    Vector2("0 0".split()),
                    Vector2("0 0".split()),
                    Vector2("0 0".split()),
                    Vector2("0 1".split()),
                    Vector2("0 0".split()),
                    Vector2("1 0".split())
                ]
                self.faceVertexData.streams[1].data += [ # normal
                    Vector3("0 0 1".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("0 0 0".split()),
                    Vector3("0 0 1".split())
                ]
                self.faceVertexData.streams[2].data += [ # tangent
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 0 0 0".split()),
                    Vector4("1 0 0 -1".split())
                ]

                # edgeData
                for n in range(4):
                    self.edgeData.size+=1
                    self.edgeData.streams[0].data.append(0)

                # faceData
                self.faceData.size +=1
                self.faceData.streams[0].data.append(Vector2("0.0137 0.0137".split()))
                self.faceData.streams[1].data.append(Vector4("1 0 0 256".split()))
                self.faceData.streams[2].data.append(Vector4("0 -1 0 256".split()))
                self.faceData.streams[3].data.append(0)
                self.faceData.streams[4].data.append(0)
                self.faceData.streams[5].data.append(0)

                # subdivisionData
                for n in range(8):
                    self.subdivisionData.subdivisionLevels.append(0)
                
                return self

 
            @classmethod
            def SampleJoinedTriangles(self):
                """
                sample joined triangles, similar to quad but with an extra edge
                
                """
                self = self.FromDCEL(dcel.e2)
                self.edgeVertexIndices.clear();self.edgeVertexIndices +=   [1, 0, 3, 2, 2, 0, 1, 3, 1, 2]
                self.edgeOppositeIndices.clear();self.edgeOppositeIndices += [1, 0, 3, 2, 5, 4, 7, 6, 9, 8]
                self.edgeNextIndices.clear();self.edgeNextIndices +=     [9, 4, 6, 8, 2, 0, 1, 3, 7, 5]#[7, 4, 6, 5, 2, 0, 1, 3]
                #[7, 4, 6, 5, 2, 8, 1, 9, 3, 0]
                self.edgeFaceIndices.clear();self.edgeFaceIndices +=     [1,-1,-1, 0,-1, 1,-1, 0, 0, 1]
                return self

            @classmethod
            def SampleBox(self):
                """
                sample hammer box
                
                data from utils/dev/literal_box_hammer_export.txt
                """
                self = self(name='meshData')
                self.vertexEdgeIndices += [14,23,18,22,10, 6,16, 7]
                self.vertexDataIndices += [0, 1, 2, 3, 4, 5, 6, 7]
                self.edgeVertexIndices += [6, 0, 2, 6, 3, 2, 7, 5, 4, 5, 1, 4, 7, 1, 4, 0, 5, 6, 7, 2, 3, 0, 1, 3]
                self.edgeOppositeIndices+=[1, 0, 3, 2, 5, 4, 7, 6, 9, 8,11,10,13,12,15,14,17,16,19,18,21,20,23,22]
                self.edgeNextIndices +=   [2,14, 4,16,21,18,19, 8,10,17,12,15, 7,23, 9,20, 6, 1,13, 3,22, 0,11, 5]
                self.edgeFaceIndices +=   [0, 3, 0, 4, 0, 2, 4, 1, 1, 3, 1, 5, 1, 2, 3, 5, 4, 3, 2, 4, 5, 0, 5, 2]
                # edgeDataIndices
                for n in range(12):
                    self.edgeDataIndices += [n, n]
                # edgeVertexDataIndices
                self.edgeVertexDataIndices += [23,1,4,2,15,3,17,19,12,5,8,6,16,7,0,14,11,18,20,10,13,21,9,22]
                # faceEdgeIndices
                self.faceEdgeIndices += [21, 7, 23, 17, 19, 15]
                # faceDataIndices
                self.faceDataIndices += [n for n in range(6)]
                # materials
                self.materials.append("materials/dev/reflectivity_30.vmat")
                # vertexData
                self.vertexData.size = 8
                self.vertexData.streams[0].data += [ # position
                    Vector3("512 -512 256".split()),
                    Vector3("-512 -512 -256".split()),
                    Vector3("-512 512 256".split()),
                    Vector3("-512 -512 256".split()),
                    Vector3("512 -512 -256".split()),
                    Vector3("512 512 -256".split()),
                    Vector3("512 512 256".split()),
                    Vector3("-512 512 -256".split())
                ]
                # faceVertexData
                self.faceVertexData.size = 24
                self.faceVertexData.streams[0].data += [ # texcoord
                    Vector2("-128 0".split()),
                    Vector2("-128 -128".split()),
                    Vector2("128 -128".split()),
                    Vector2("128 -128".split()),
                    Vector2("-2048 -2048".split()),
                    Vector2("128 0".split()),
                    Vector2("128 0".split()),
                    Vector2("-128 0".split()),
                    Vector2("-128 128".split()),
                    Vector2("-128 0".split()),
                    Vector2("-128 -128".split()),
                    Vector2("128 0".split()),
                    Vector2("128 128".split()),
                    Vector2("-128 -128".split()),
                    Vector2("128 -128".split()),
                    Vector2("-2048 2048".split()),
                    Vector2("-128 -128".split()),
                    Vector2("-128 0".split()),
                    Vector2("128 -128".split()),
                    Vector2("128 -128".split()),
                    Vector2("128 0".split()),
                    Vector2("2048 2048".split()),
                    Vector2("-128 -128".split()),
                    Vector2("2048 -2048".split())
                ]
                self.faceVertexData.streams[1].data += [ # normal
                    Vector3("1 0 0".split()),
                    Vector3("1 0 0".split()),
                    Vector3("0 1 0".split()),
                    Vector3("-1 0 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("1 0 0".split()),
                    Vector3("0 -1 0".split()),
                    Vector3("-1 0 0".split()),
                    Vector3("0 0 -1".split()),
                    Vector3("0 -1 0".split()),
                    Vector3("0 1 0".split()),
                    Vector3("0 1 0".split()),
                    Vector3("0 0 -1".split()),
                    Vector3("0 -1 0".split()),
                    Vector3("0 -1 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("0 0 -1".split()),
                    Vector3("0 1 0".split()),
                    Vector3("1 0 0".split()),
                    Vector3("0 0 -1".split()),
                    Vector3("-1 0 0".split()),
                    Vector3("0 0 1".split()),
                    Vector3("-1 0 0".split()),
                    Vector3("0 0 1".split())
                ]

                self.faceVertexData.streams[2].data += [ # tangent
                    Vector4("0 1 0 -1".split()),
                    Vector4("0 1 0 -1".split()),
                    Vector4("1 -0 0 1".split()),
                    Vector4("0 1 0 1".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 1 0 -1".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 1 0 1".split()),
                    Vector4("1 0 0 1".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("1 -0 0 1".split()),
                    Vector4("1 -0 0 1".split()),
                    Vector4("1 0 0 1".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("1 0 0 1".split()),
                    Vector4("1 -0 0 1".split()),
                    Vector4("0 1 0 -1".split()),
                    Vector4("1 0 0 1".split()),
                    Vector4("0 1 0 1".split()),
                    Vector4("1 0 0 -1".split()),
                    Vector4("0 1 0 1".split()),
                    Vector4("1 0 0 -1".split())
                ]

                # edgeData
                for n in range(12):
                    self.edgeData.size+=1
                    self.edgeData.streams[0].data.append(0)

                # faceData
                self.faceData.size = 6
                self.faceData.streams[0].data += [
                    Vector2("0.0004882813 0.0004882813".split()),
                    Vector2("0.0078125 0.0078125".split()),
                    Vector2("0.0078125 0.0078125".split()),
                    Vector2("0.0078125 0.0078125".split()),
                    Vector2("0.0078125 0.0078125".split()),
                    Vector2("0.0078125 0.0078125".split())
                ]
                self.faceData.streams[2].data += [
                    Vector4("0 -1 0 0".split()),
                    Vector4("0 -1 0 0".split()),
                    Vector4("0 0 -1 0".split()),
                    Vector4("0 0 -1 0".split()),
                    Vector4("0 0 -1 0".split()),
                    Vector4("0 0 -1 0".split())
                ]
                self.faceData.streams[1].data += [
                    Vector4("1 0 0 0".split()),
                    Vector4("1 0 0 0".split()),
                    Vector4("0 1 0 0".split()),
                    Vector4("0 1 0 0".split()),
                    Vector4("1 0 0 0".split()),
                    Vector4("1 0 0 0".split())
                ]
                self.faceData.streams[3].data += [0]*6
                self.faceData.streams[4].data += [0]*6
                self.faceData.streams[5].data += [0]*6

                # subdivisionData
                for n in range(24):
                    self.subdivisionData.subdivisionLevels.append(0)
                
                return self

            def add_face(self, id: int, textureScale: Vector2,
                textureAxisU: Vector4,
                textureAxisV: Vector4,
                materialindex: int, lightmapScaleBias: int
                ):
                self.faceData.size +=1
                self.faceData.streams[0].data.append(textureScale)
                self.faceData.streams[1].data.append(textureAxisU)
                self.faceData.streams[2].data.append(textureAxisV)
                self.faceData.streams[3].data.append(materialindex)
                self.faceData.streams[4].data.append(0)
                self.faceData.streams[5].data.append(lightmapScaleBias)

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

        # For each side...
        for (i, key), side_kv in keyvalues.items(indexed_keys=True):
            break
            if key != 'side':
                continue
            # Texture Data
            material = f"materials/{side_kv['material'].lower()}.vmat"
            if material not in mesh.meshData.materials:
                mesh.meshData.materials.append(material)
            usplit = side_kv['uaxis'].split()
            vsplit = side_kv['vaxis'].split()
            mesh.meshData.add_face(int(side_kv['id']),
                textureScale=Vector2((float(usplit[-1]), float(vsplit[-1]))),
                textureAxisU=Vector4([int(n.strip('[]')) for n in usplit[:-1]]),
                textureAxisV=Vector4([int(n.strip('[]')) for n in usplit[:-1]]),
                materialindex=mesh.meshData.materials.index(material),
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
    print('Source 2 VMAP Generator!')
    out_vmap = create_fresh_vmap()
    vmap = out_vmap.root
    def test_triangle():
        mesh = CMapWorld.CMapMesh()
        mesh.origin = Vector3([3,3,0])
        mesh.meshData = CMapWorld.CMapMesh.CDmePolygonMesh.SampleTriangle()
        out_vmap.prefix_attributes['map_asset_references'].append("materials/dev/reflectivity_30.vmat")
        vmap['world']['children'].append(mesh.get_element(vmap))
        out_vmap.write("utils/dev/out_sample_triangle.vmap.txt", 'keyvalues2', 4)
        print("Saved", "utils/dev/out_sample_triangle.vmap.txt")

    def test_quad():
        mesh = CMapWorld.CMapMesh()
        mesh.origin = Vector3([0,0,0])
        mesh.meshData = CMapWorld.CMapMesh.CDmePolygonMesh.SampleQuad()
        out_vmap.prefix_attributes['map_asset_references'].append("materials/dev/reflectivity_30.vmat")
        vmap['world']['children'].append(mesh.get_element(vmap))
        out_vmap.write("utils/dev/out_sample_quad.vmap.txt", 'keyvalues2', 4)
        print("Saved", "utils/dev/out_sample_quad.vmap.txt")

    def test_joinedtris():
        mesh = CMapWorld.CMapMesh()
        mesh.origin = Vector3([0,0,0])
        mesh.meshData = CMapWorld.CMapMesh.CDmePolygonMesh.FromDCEL(dcel.e2)
        out_vmap.prefix_attributes['map_asset_references'].append("materials/dev/reflectivity_30.vmat")
        vmap['world']['children'].append(mesh.get_element(vmap))
        out_vmap.write("utils/dev/out_sample_joinedtris.vmap.txt", 'keyvalues2', 4)
        print("Saved", "utils/dev/out_sample_joinedtris.vmap.txt")

    def test_box():
        mesh = CMapWorld.CMapMesh()
        mesh.origin = Vector3([0,0,256])
        mesh.meshData = CMapWorld.CMapMesh.CDmePolygonMesh.SampleBox()
        out_vmap.prefix_attributes['map_asset_references'].append("materials/dev/reflectivity_30.vmat")
        vmap['world']['children'].append(mesh.get_element(vmap))
        out_vmap.write("utils/dev/out_sample_box.vmap.txt", 'keyvalues2', 4)
        print("Saved", "utils/dev/out_sample_box.vmap.txt")
    test_joinedtris()
    import subprocess, shutil
    shutil.copy("utils/dev/out_sample_joinedtris.vmap.txt", "D:/Games/steamapps/common/Half-Life Alyx/content/hlvr_addons/test/maps/test.vmap")
    p = subprocess.run(
        args=[
            "-game", "hlvr",
            "-i", "D:/Games/steamapps/common/Half-Life Alyx/content/hlvr_addons/test/maps/test.vmap",
            "-fshallow",
            "-world",
            #"nominidumps"
        ],
        executable=r"D:\Games\steamapps\common\Half-Life Alyx\game\bin\win64\resourcecompiler.exe",
        stdout=subprocess.PIPE
    )
    if p:
        if p.returncode == 0:
            print("Parsed sucesfully.")
            if b"Created 1 world node" in p.stdout:
                print("Mesh was valid!")
            else:
                print(p.stdout.decode('utf-8'))

        else:
            print("Mesh was corrupted!")
            # delete dumps
            test = os.listdir(".")
            for item in test:
                if item.endswith(".mdmp"):
                    os.remove(os.path.join(item))
