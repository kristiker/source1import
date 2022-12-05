from dataclasses import dataclass, field

from .worldnode import Bounds

@dataclass
class _BaseShape:
    m_nCollisionAttributeIndex: int = 0
    m_nSurfacePropertyIndex: int = 0
    m_UserFriendlyName: str = ""

@dataclass
class Hull(_BaseShape):
    @dataclass
    class Hull:
        @dataclass
        class Plane:
            m_vNormal: list[float]
            m_flOffset: float
        @dataclass
        class Edge:
            m_nNext: int
            m_nTwin: int
            m_nOrigin: int
            m_nFace: int
        @dataclass
        class Face:
            m_nEdge: int
        m_vCentroid: list[float] = field(default_factory=list)
        m_flMaxAngularRadius: float = 0.0
        m_Vertices: list[list[float]] = field(default_factory=list)
        m_Planes: list[Plane] = field(default_factory=list)
        m_Edges: list[Edge] = field(default_factory=list)
        m_Faces: list[Face] = field(default_factory=list)
        m_vOrthographicAreas: list[float] = field(default_factory=list)
        m_MassProperties: list[float] = field(default_factory=list)
        m_flVolume: float = 0.0
        m_flMaxMotionRadius: float = 0.0
        m_flMinMotionThickness: float = 0.0
        m_Bounds: Bounds = field(default_factory=Bounds)
        m_nFlags: int = 0
    m_Hull: Hull = field(default_factory=Hull)


@dataclass
class Mesh(_BaseShape):
    @dataclass
    class Mesh:
        m_vMin: list[float] = field(default_factory=list)
        m_vMax: list[float] = field(default_factory=list)
        m_Materials: list[int] = field(default_factory=list)
        m_vOrthographicAreas: list[float] = field(default_factory=list)
        m_Nodes: bytearray = field(default_factory=bytearray)
        m_Triangles: bytearray = field(default_factory=bytearray)
        m_Vertices: bytearray = field(default_factory=bytearray)
    m_Mesh: Mesh =field(default_factory=Mesh)

@dataclass
class Shape:
    m_spheres: list = field(default_factory=list)
    m_capsules: list = field(default_factory=list)
    m_hulls: list[Hull] = field(default_factory=list)
    m_meshes: list[Mesh] = field(default_factory=list)


@dataclass
class Part:
    m_nFlags: int
    m_flMass: float
    """mas in kg"""
    m_rnShape: Shape
    m_CollisionAttributeIndices: list[int] = field(default_factory=list)
    m_nSurfacepropertyIndices: list = field(default_factory=list)
    m_nCollisionAttributeIndex: int = 0
    m_nReserved: int = 0
    m_flInertiaScale: float = 1.0
    m_flLinearDamping: float = 0.0
    m_flAngularDamping: float = 0.0
    m_bOverrideMassCenter: bool = False
    m_vMassCenterOverride: list[float] = field(default_factory=list)

@dataclass
class CollisionAttribute:
    m_CollisionGroup: int
    m_InteractAs: list[int]
    m_InteractWith: list[int]
    m_InteractExclude: list[int]
    m_CollisionGroupString: str = "Default"
    m_InteractAsStrings: list[str] = field(default_factory=list)
    m_InteractWithStrings: list[str] = field(default_factory=list)
    m_InteractExcludeStrings: list[str] = field(default_factory=list)

@dataclass
class PhysX:
    m_nFlags: int = 0
    m_nRefCounter: int = 0
    m_bonesHash: list = field(default_factory=list)
    m_boneNames: list = field(default_factory=list)
    m_indexNames: list = field(default_factory=list)
    m_indexHash: list = field(default_factory=list)
    m_bindPose: list = field(default_factory=list)
    m_parts: list[Part] = field(default_factory=list)
    m_constraints2: list = field(default_factory=list)
    m_joints: list = field(default_factory=list)
    m_pFeModel: object = None
    m_boneParents: list = field(default_factory=list)
    m_surfacePropertyHashes: list[int] = field(default_factory=list)
    m_collisionAttributes: list[CollisionAttribute] = field(default_factory=list)
    m_debugPartNames: list = field(default_factory=list)
    m_embeddedKeyvalues: str = ""