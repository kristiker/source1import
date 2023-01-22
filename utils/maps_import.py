
from functools import cache
import shutil
import struct
from dataclassy import dataclass, factory

import shared.base_utils2 as sh
import vdf
import bsp_tool
import shared.keyvalues3 as kv3
import itertools
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
    _Vector as datamodel_vector_t,
)

OVERWRITE_MAPS = False
IMPORT_VMF_ENTITIES = True
IMPORT_BSP_ENTITIES = False
#WRITE_TO_PREFAB = True
IMPORT_BSP_TO_VMAP_C = True

maps = Path("maps")
mapsrc = Path("mapsrc")

def out_vmap_name(in_vmf: Path) -> Path:
    root = mapsrc if in_vmf.local.is_relative_to(mapsrc) else maps
    return sh.EXPORT_CONTENT / maps / "source1imported" / "entities" / in_vmf.local.relative_to(root).with_suffix(".vmap")

def out_vmap_c_name(in_vmf: Path) -> Path:
    return sh.EXPORT_GAME / in_vmf.local.with_suffix(".vmap_c")

def main():

    if IMPORT_VMF_ENTITIES:
        print("Importing vmf entities!")
        for vmf_path in itertools.chain(
            sh.collect(mapsrc, ".vmf", ".vmap", OVERWRITE_MAPS, out_vmap_name),
            sh.collect(maps, ".vmf", ".vmap", OVERWRITE_MAPS, out_vmap_name)
        ):
            ImportVMFEntitiesToVMAP(vmf_path)

    if IMPORT_BSP_ENTITIES:
        print("Importing bsp entities!")
        for bsp_path in sh.collect(maps, ".bsp", ".vmap", OVERWRITE_MAPS, out_vmap_name):
            ImportBSPEntitiesToVMAP(bsp_path)

    if IMPORT_BSP_TO_VMAP_C:
        print("Converting bsp to vpk!")
        for bsp_path in sh.collect(maps, ".bsp", ".vpk", OVERWRITE_MAPS, out_vmap_c_name):
            ImportBSPToVPK(bsp_path)

    print("Looks like we are done!")

import shared.worldnode as wnod
import shared.world as wrld
import shared.entities as entities
import shared.physics as physics
from murmurhash2 import murmurhash2

def ImportBSPToVPK(bsp_path: Path):
    compiled_vmap_path = out_vmap_c_name(bsp_path)
    compiled_lumps_folder = compiled_vmap_path.parent / compiled_vmap_path.stem
    compiled_lumps_folder.parent.MakeDir()

    sh.status(f'- Reading {bsp_path.local}')
    bsp: bsp_tool.ValveBsp = bsp_tool.load_bsp(bsp_path.as_posix())

    sprp_lump = sprp(bsp.GAME_LUMP.sprp)
    _dprp: bsp_tool.base.lumps.RawBspLump = bsp.GAME_LUMP.dprp

    import numpy as np
    from math import sin, cos
    def transforms_to_3x4(origin: vector3, angles: qangle) -> list:
        m = np.zeros((3, 4))
        # TODO: Figure out rotation
        m[:, 3] = origin
        #return m.tolist()
        α = angles[1]
        β = angles[0]
        γ = angles[2]
        return [
            [cos(α)*cos(β), cos(α)*sin(β)*sin(γ)-sin(α)*cos(γ), cos(α)*sin(β)*cos(γ)+sin(α)*sin(γ), origin[0]],
            [sin(α)*cos(β), sin(α)*sin(β)*sin(γ)+cos(α)*cos(γ), sin(α)*sin(β)*cos(γ)-cos(α)*sin(γ), origin[1]],
            [-sin(β),       cos(β)*sin(γ),                      cos(β)*cos(γ),                      origin[2]],
        ]

    def col32_to_vec4(diffuse: int) -> list:
        return [
            (diffuse & 0xFF) / 255,
            ((diffuse >> 8) & 0xFF) / 255,
            ((diffuse >> 16) & 0xFF) / 255,
            ((diffuse >> 24) & 0xFF) / 255,
        ]

    worldnode000 = wnod.WorldNode()
    worldnode000.m_boundsGroups.append(wnod.Bounds([-9999.0, -9999.0, -9999.0], [9999999.0, 9999999.0, 9999999.0]))

    for static_prop in sprp_lump.static_props:
        model_path = Path(sprp_lump.model_names[static_prop.PropType]).with_suffix(".vmdl")
        prop_sceneobject = wnod.SceneObject(
            m_nObjectID = 0,
            m_vTransform = transforms_to_3x4(static_prop.Origin, static_prop.Angles),
            m_flFadeStartDistance = static_prop.FadeMinDist,
            m_flFadeEndDistance = static_prop.FadeMaxDist,
            m_vTintColor = col32_to_vec4(static_prop.DiffuseModulation),
            m_skin = str(static_prop.Skin),
            m_nObjectTypeFlags = static_prop.Flags,
            m_vLightingOrigin = static_prop.LightingOrigin, # TODO: relative to origin?
            m_nBoundsGroupIndex = 0,
            m_renderableModel = kv3.flagged_value(model_path.as_posix(), kv3.Flag.resource),
        )

        worldnode000.add_to_layer(prop_sceneobject, "world_layer_base")
        

    worldnode000_path = Path(r"D:\Users\kristi\Documents\s&box projects\cs\maps\ar_lunacy\worldnodes") / "node000.vwnod_c"
    worldnode000_path.parent.MakeDir()

    def write_resource_data_by_template(data: object, template_path: Path, resurce_path: Path):
        # TODO: Resource external references
        resource = bytearray(template_path.read_bytes())
        DATA = bytes(kv3.binarywriter.BinaryLZ4(kv3.KV3File(data)))
        # adjust block size bytes
        blocksize_location = resource.find(b"DATA") + 8
        resource = resource[:blocksize_location] + struct.pack("<I", len(DATA)) + resource[blocksize_location + 4:]
        resource += DATA
        # adjust file size bytes
        resource = struct.pack("<I", len(resource))  + resource[4:]
        resurce_path.write_bytes(resource)

    default_ents = entities.Ents()
    default_ents_path = Path(r"D:\Users\kristi\Documents\s&box projects\cs\maps\ar_lunacy\entities") / "default_ents.vents_c"
    default_ents_path.parent.MakeDir()
    
    for entity in bsp.ENTITIES:
        # In VRF https://github.com/SteamDatabase/ValveResourceFormat/blob/5ac74c973cd843b9d7eafb143d68e9be010c5ae2/ValveResourceFormat/Resource/ResourceTypes/EntityLump.cs#L66
        hashed_kv: dict[int, object] = {}
        string_kv: dict[str, object] = {}

        for key, value in entity.items():
            if isinstance(value, list):
                # connections
                continue
            hashed_kv[murmurhash2(key.encode("ascii"), 0x31415926)] = value

        kvData = bytearray()
        kvData += struct.pack("<I", 1)
        kvData += struct.pack("<I", len(hashed_kv))
        kvData += struct.pack("<I", len(string_kv))
        for key, value in hashed_kv.items():
            kvData += struct.pack("<I", key) # key
            kvData += struct.pack("<I", 0x1e) # type (string)
            kvData += value.encode("utf-8") + b"\x00" # value

        default_ents.m_entityKeyValues.append(entities.Entity(kvData, []))

    world_physics = physics.PhysX()
    world_physics_path = Path(r"D:\Users\kristi\Documents\s&box projects\cs\maps\ar_lunacy") / "world_physics.vphys_c"
    world_physics_path.parent.MakeDir()

    a = bsp.PHYSICS_DISPLACEMENT
    from bsp_tool.branches.shared import PhysicsCollide, PhysicsBlock
    from shared.keyvalues1 import KV as KV1
    collide_lump: PhysicsCollide = bsp.PHYSICS_COLLIDE
    
    for (collision_model_index, solids, script) in collide_lump:
        collision_model_index: int
        solids: list[PhysicsBlock]
        script: bytes
        keyvalues = KV1.CollectionFromBuffer(script.rstrip(b'\x00').decode("ascii"))
        
        for staticsolid in keyvalues.get_all_for("staticsolid"):
            staticsolid["index"]: int
            staticsolid["contents"]: int
        
        # Hopefully sorted
        for surfaceprop in keyvalues["materialtable"]:
            world_physics.m_surfacePropertyHashes.append(
                murmurhash2(surfaceprop.encode("ascii").lower(), 0x31415926)
            )

        for solid in solids:
            collide_header, surface_header = solid.header
            # COLLIDE_POLY
            if collide_header.model_type != 0:
                continue
            surface = compactsurface_t.FromBytes(solid.data[:compactsurface_t.size])
            root_ledge = compactledgenode_t.FromBytes(solid.data[surface.offset_ledgetree_root:surface.offset_ledgetree_root+compactledgenode_t.size])
            root_ledge.address = surface.offset_ledgetree_root
            #Path("solid.bin").write_bytes(solid.data)
            def get_all_ivp_edges(node: compactledgenode_t, ledges: list[compactledge_t]):
                if node is None:
                    return
                if not node.is_terminal:
                    left = compactledgenode_t.FromBytes(solid.data[node.address+compactledgenode_t.size:node.address+compactledgenode_t.size+compactledgenode_t.size])
                    left.address = node.address+compactledgenode_t.size
                    get_all_ivp_edges(left, ledges)
                    right = compactledgenode_t.FromBytes(solid.data[node.address+node.offset_right_node:node.address+node.offset_right_node + compactledgenode_t.size])
                    right.address = node.address+node.offset_right_node
                    get_all_ivp_edges(right, ledges)
                else:
                    p = node.address+node.offset_compact_ledge
                    ledge = compactledge_t.FromBytes(solid.data[p:p+compactledge_t.size])
                    ledge.address = p
                    ledges.append(ledge)

            ledges: list[compactledge_t] = []
            get_all_ivp_edges(root_ledge, ledges)

            for ledge in ledges:
                address_vertices = ledge.address + ledge.c_point_offset
                vert_count = ledge.n_triangles * 3
                verts: list[vector3] = [None] * vert_count
                for i in range(ledge.n_triangles):
                    tri_p = ledge.address+ledge.size+(i*compacttriangle_t.size)
                    tri = compacttriangle_t.FromBytes(solid.data[tri_p:tri_p+compacttriangle_t.size])
                    p = address_vertices + (tri.compact_edge_0_start_point_index * 16)
                    verts[(i*3) + 0] = vector3(struct.unpack('<fff', solid.data[p:p+12]))
                    p = address_vertices + (tri.compact_edge_1_start_point_index * 16)
                    verts[(i*3) + 1] = vector3(struct.unpack('<fff', solid.data[p:p+12]))
                    p = address_vertices + (tri.compact_edge_2_start_point_index * 16)
                    verts[(i*3) + 2] = vector3(struct.unpack('<fff', solid.data[p:p+12]))
                pass

    shape = physics.Shape()
    
    world_physics.m_parts.append(physics.Part(2, 0.0, shape))

    bsp.file.close()
    write_resource_data_by_template(worldnode000, Path("shared/maps/node000.vwnod_c.template"), worldnode000_path)
    write_resource_data_by_template(default_ents, Path("shared/maps/default_ents.vents_c.template"), default_ents_path)
    write_resource_data_by_template(world_physics, Path("shared/maps/world_physics.vphys_c.template"), world_physics_path)

    #write_node_resource(worldnode000, worldnode000_path)
    #write_node_manifest()
    #write_world()
    # TODO: pack to vpk

    shutil.copytree(compiled_lumps_folder, Path(r"D:\Users\kristi\Documents\s&box projects\compile\maps\ar_lunacy"), dirs_exist_ok=True)

    #if sh.eEngineUtils.vpk.avaliable():
    #    r = sh.eEngineUtils.vpk([
    #        "-?",
    #    ])

    # map
    import os
    os.system('cd "D:/Users/kristi/Documents/s&box projects/cs/maps" && compilemap.bat')
    
    # rename compile.vpk to mapname.vpk
    shutil.copyfile(r"D:\Users\kristi\Documents\s&box projects\compile.vpk", r"D:\Users\kristi\Documents\s&box projects\cs\maps\ar_lunacy.vpk")
    # copy to

        
    print("Saved map ", compiled_lumps_folder.name)

import ctypes

class sprp:
    model_names: list[str]
    leaf: list[ctypes.c_uint16]
    static_props: list["StaticPropV11"]

    def __init__(self, raw_lump: bsp_tool.base.lumps.RawBspLump):
        raw_lump.file.seek(raw_lump.offset)
        data = raw_lump.file.read(raw_lump._length)
        pos = 0

        dict_count = struct.unpack('<i', data[pos:pos+4])[0]
        pos += 4
        self.model_names = []
        for _ in range(dict_count):
            self.model_names.append(struct.unpack('<128s', data[pos:pos+128])[0].decode("ascii").rstrip('\x00'))
            pos += 128

        leaf_count = struct.unpack('<i', data[pos:pos+4])[0]
        pos += 4
        self.leaf = []
        for _ in range(leaf_count):
            self.leaf.append(struct.unpack('<H', data[pos:pos+2])[0])
            pos += 2

        self.static_prop_count = struct.unpack('<i', data[pos:pos+4])[0]
        pos += 4
        self.static_props = []
        for _ in range(self.static_prop_count):
            self.static_props.append(StaticPropV11.FromBytes(data[pos:pos+StaticPropV11.size]))
            pos += StaticPropV11.size

class _common_struct:
    @classmethod
    @property
    @cache
    def size(cls):
        total = 0
        for type in cls.__annotations__.values():
            if issubclass(type, ctypes._SimpleCData):
                total += ctypes.sizeof(type)
            elif issubclass(type, datamodel_vector_t):
                total += sum(struct.calcsize(vec_element) for vec_element in type.type_str)
        return total

    @classmethod
    def FromBytes(cls, data: bytes):
        kwargs = {}
        pos = 0
        for property, type in cls.__annotations__.items():
            if issubclass(type, ctypes._SimpleCData):
                advance = ctypes.sizeof(type)
                kwargs[property] = struct.unpack('<' + type._type_, data[pos:pos+advance])[0]
                pos += advance
            elif issubclass(type, datamodel_vector_t):
                vecargs = []
                for vector_element in type.type_str:
                    advance = struct.calcsize(vector_element)
                    vecargs.append(struct.unpack('<' + vector_element, data[pos:pos+advance])[0])
                    pos += advance
                kwargs[property] = type(vecargs)

        assert pos == len(data)
        return cls(**kwargs)

@dataclass
class StaticPropV11(_common_struct):
    # https://developer.valvesoftware.com/wiki/Source_BSP_File_Format#Static_props:~:text=struct%20StaticPropLump_t
    Origin: vector3
    Angles: qangle
    PropType: ctypes.c_uint16
    FirstLeaf: ctypes.c_uint16
    LeafCount: ctypes.c_uint16
    Solid: ctypes.c_uint8
    Flags: ctypes.c_int
    Skin: ctypes.c_int
    FadeMinDist: ctypes.c_float
    FadeMaxDist: ctypes.c_float
    LightingOrigin: vector3
    ForcedFadeScale: ctypes.c_float
    MinCPULevel: ctypes.c_uint8
    MaxCPULevel: ctypes.c_uint8
    MinGPULevel: ctypes.c_uint8
    MaxGPULevel: ctypes.c_uint8
    DiffuseModulation: ctypes.c_int # color32
    DisableX360: ctypes.c_bool
    FlagsEx: ctypes.c_int32
    UniformScale: ctypes.c_float

@dataclass
class compactsurface_t(_common_struct):
    mass_center: vector3
    rotation_inertia: vector3
    upper_limit_radius: ctypes.c_float
    
    #max_factor_surface_deviation: ctypes.c_uint | Literal[8]
    #byte_size: ctypes.c_int | Literal[24]
    bitfield0: ctypes.c_int
    offset_ledgetree_root: ctypes.c_int
    dummy: vector3

    @property
    def max_factor_surface_deviation(self):
        return self.bitfield0 & 0xFF
    
    @property
    def byte_size(self):
        return (self.bitfield0 >> 8) & 0xFFFFFF


@dataclass
class compactledgenode_t(_common_struct):
    offset_right_node: ctypes.c_int
    offset_compact_ledge: ctypes.c_int
    center: vector3
    radius: ctypes.c_float
    box_size_x: ctypes.c_ubyte
    box_size_y: ctypes.c_ubyte
    box_size_z: ctypes.c_ubyte
    free_0: ctypes.c_ubyte

    @property
    def is_terminal(self):
        return self.offset_right_node == 0
    
@dataclass
class compactledge_t(_common_struct):
    c_point_offset: ctypes.c_int
    ledgetree_node_offset: ctypes.c_int | ctypes.c_int
    bitfield0: ctypes.c_int
    n_triangles: ctypes.c_short
    for_future_use: ctypes.c_short

@dataclass
class compacttriangle_t(_common_struct):
    bitfield0: ctypes.c_int
    compact_edge_0: ctypes.c_int
    compact_edge_1: ctypes.c_int
    compact_edge_2: ctypes.c_int

    tri_index = property(lambda self: self.bitfield0 & 0xFFF)
    pierce_index = property(lambda self: (self.bitfield0 >> 12) & 0xFFF)
    material_index = property(lambda self: (self.bitfield0 >> 24) & 0x7F)
    is_virtual = property(lambda self: (self.bitfield0 >> 31) & 0x1)

    compact_edge_0_start_point_index = property(lambda self: self.compact_edge_0 & 0xFFFF)
    compact_edge_0_opposite_index = property(lambda self: (self.compact_edge_0 >> 16) & 0x7FFF)
    compact_edge_0_is_virtual = property(lambda self: (self.compact_edge_0 >> 31) & 0x1)
    compact_edge_1_start_point_index = property(lambda self: self.compact_edge_1 & 0xFFFF)
    compact_edge_1_opposite_index = property(lambda self: (self.compact_edge_1 >> 16) & 0x7FFF)
    compact_edge_1_is_virtual = property(lambda self: (self.compact_edge_1 >> 31) & 0x1)
    compact_edge_2_start_point_index = property(lambda self: self.compact_edge_2 & 0xFFFF)
    compact_edge_2_opposite_index = property(lambda self: (self.compact_edge_2 >> 16) & 0x7FFF)
    compact_edge_2_is_virtual = property(lambda self: (self.compact_edge_2 >> 31) & 0x1)

def ImportVMFEntitiesToVMAP(vmf_path):

    vmap_path = out_vmap_name(vmf_path)
    vmap_path.parent.MakeDir()

    sh.status(f'- Reading {vmf_path.local}')
    with open(vmf_path) as fp:
        vmf: vdf.VDFDict = vdf.load(fp, mapper=vdf.VDFDict, merge_duplicate_keys=False)#KV.CollectionFromFile(vmf_path, case_sensitive=True)

    out_vmap = convert_vmf_entities(vmf)
    out_vmap.write(vmap_path, "keyvalues2", 4)
    if sh.MOCK:
        dmx.remove_ids(vmap_path)
    print("+ Generated", vmap_path.local)
    return vmap_path

def ImportBSPEntitiesToVMAP(bsp_path):
    """Reads the bsp entity lump and converts it to a content vmap file."""
    vmap_path = out_vmap_name(bsp_path)
    vmap_path.parent.MakeDir()

    sh.status(f'- Reading {bsp_path.local}')
    bsp: bsp_tool.ValveBsp = bsp_tool.load_bsp(bsp_path.as_posix())
    fake_vmf = vdf.VDFDict()
    for entity in bsp.ENTITIES:
        fake_vmf[base_vmf.entity] = entity

    out_vmap = convert_vmf_entities(fake_vmf)
    out_vmap.write(vmap_path, "keyvalues2", 4)
    print("+ Generated from bsp", vmap_path.local)
    return vmap_path

def convert_vmf_entities(vmf: vdf.VDFDict) -> dmx.DataModel:
    out_vmap = create_fresh_vmap()
    vmap = out_vmap.root

    for key, value in vmf.items():
        # dismiss excess base keys (exlcuding entity)
        # e.g. multiple worlds, TODO: merge_multiple_worlds() use latest properties
        if len(vmf.get_all_for(key)) > 1 or key in (base_vmf.world, base_vmf.entity):
            continue
        # some fixups
        main_to_root(vmap, key, value)

    for vmfEntityKeyValues in vmf.get_all_for("entity"):
        translated_entity = CMapWorld.CMapEntity.FromVMFEntity(vmfEntityKeyValues)
        vmap["world"]["children"].append(
            translated_entity.get_element(vmap)
        )
        
    return out_vmap

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
    boilerplate = dmx.load(Path(__file__).parent / "shared/empty.vmap.txt")
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
                if isinstance(v, list):
                    v = v[0] # bsp_tool duplicate keys
                editorDict[k] = v
            #else:
            #    print("Unknown editor object", k, type(v))
        t.__dict__.update(baseDict)
        if isinstance(t, _BaseEnt):
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
    sh.parse_argv(globals())
    main()
