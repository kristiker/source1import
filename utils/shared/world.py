from dataclasses import dataclass, field

@dataclass
class BuilderParams:
    m_nSizeBytesPerVoxel: int
    m_flMinDrawVolumeSize: float
    m_flMinDistToCamera: float
    m_flMinAtlasDist: float
    m_flMinSimplifiedDist: float
    m_flHorzFOV: float
    m_flHalfScreenWidth: float
    m_nAtlasTextureSizeX: int
    m_nAtlasTextureSizeY: int
    m_nUniqueTextureSizeX: int
    m_nUniqueTextureSizeY: int
    m_nCompressedAtlasSize: int
    m_flGutterSize: float
    m_flUVMapThreshold: float
    m_vWorldUnitsPerTile: list[float] #= field(default_factory=lambda:[10000.000000, 10000.000000, 1000.000000])
    m_nMaxTexScaleSlots: int
    m_bWrapInAtlas: bool
    m_bBuildBakedLighting: bool
    m_vLightmapUvScale: list[float] #= field(default_factory=lambda:[1.0, 1.0])
    m_nCompileTimestamp: int = 1657194806
    m_nCompileFingerprint: int = 8654431948308770350

@dataclass
class Node:
    m_Flags: int # flags
    m_nParent: int
    m_vOrigin: list[float] = field(default_factory=lambda:[0.0, 0.0, 0.0]) # vec3
    m_vMinBounds: list[float] = field(default_factory=list) # vec3
    m_vMaxBounds: list[float] = field(default_factory=list) # vec3
    m_flMinimumDistance: float = -1.000000
    m_ChildNodeIndices: list[int] = field(default_factory=list)
    m_worldNodePrefix: str = "" # maps\map\worldnodes\node000

@dataclass
class LightingInfo:
    m_nLightmapVersionNumber: int = 8
    m_nLightmapGameVersionNumber: int =  1
    m_vLightmapUvScale: list[float] = field(default_factory=lambda:[1.0, 1.0])
    m_bHasLightmaps: bool = True
    m_lightMaps: list[str] = field(default_factory=list)
    #[
    #    resource:"maps/map/lightmaps/direct_light_indices.vtex",
    #    resource:"maps/map/lightmaps/direct_light_strengths.vtex",
    #    resource:"maps/map/lightmaps/irradiance.vtex",
    #    resource:"maps/map/lightmaps/directional_irradiance.vtex",
    #    resource:"maps/map/lightmaps/debug_chart_color.vtex",
    #]

@dataclass
class World:
    """Format for Valve vwrld_c files"""
    m_builderParams: BuilderParams
    m_worldNodes: list[Node] = field(default_factory=list)
    m_worldLightingInfo: LightingInfo = field(default_factory=LightingInfo)
    m_entityLumps: list[str] = field(default_factory=list)