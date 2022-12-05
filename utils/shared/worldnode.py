from dataclasses import dataclass, field

@dataclass
class SceneObject:
    m_nObjectID: int
    m_vTransform: list[list[float]]
    m_flFadeStartDistance: float
    m_flFadeEndDistance: float
    m_vTintColor: list[float]
    m_skin: str
    m_nObjectTypeFlags: int | str
    """"int flags or flag name"""
    m_vLightingOrigin: list[float]
    m_nLightGroup: int = 0
    m_nOverlayRenderOrder: int = 0
    m_nLODOverride: int = -1
    m_nCubeMapPrecomputedHandshake: int = 0
    m_nLightProbeVolumePrecomputedHandshake: int = 0
    m_nBoundsGroupIndex: int = -1
    m_renderableModel: str = None # resource flag
    """vmdl file to render"""
    m_renderable: str = None
    """vmesh file to render"""
    #m_externalTextures: list[str] = field(default_factory=list)
    #m_VisClusterMemberBits: int = 0

@dataclass
class Bounds:
    m_vMinBounds: list[float]
    m_vMaxBounds: list[float]

@dataclass
class MaterialOverride:
    m_nSceneObjectIndex: int
    m_nSubSceneObject: int
    m_nDrawCallIndex: int
    m_pMaterial: str # resource flag

@dataclass
class NodeLightingInfo:
    m_nLightmapVersionNumber: int = 0
    m_nLightmapGameVersionNumber: int = 0
    m_vLightmapUvScale: list = field(default_factory=lambda: [1.0, 1.0])
    m_bHasLightmaps: bool = False
    m_lightMaps: list = field(default_factory=list)

@dataclass
class WorldNode:
    """Format for Valve vwnod_c files"""
    m_sceneObjects: list[SceneObject] = field(default_factory=list)
    m_infoOverlays: list = field(default_factory=list)
    m_visClusterMembership: list = field(default_factory=list)
    m_boundsGroups: list[Bounds] = field(default_factory=list)
    m_boneOverrides: list = field(default_factory=list)
    m_aggregateSceneObjects: list = field(default_factory=list)
    m_extraVertexStreamOverrides: list = field(default_factory=list)
    m_materialOverrides: list[MaterialOverride] = field(default_factory=list)
    m_extraVertexStreams: list = field(default_factory=list)
    m_layerNames: list[str] = field(default_factory=list)
    m_sceneObjectLayerIndices: list[int] = field(default_factory=list)
    m_overlayLayerIndices: list = field(default_factory=list)
    m_grassFileName: str = ""
    m_nodeLightingInfo: NodeLightingInfo = field(default_factory=NodeLightingInfo)

    def add_to_layer(self, scene_object: SceneObject, layer: str):
        """Add a scene object to a layer"""
        if layer not in self.m_layerNames:
            self.m_layerNames.append(layer)
        self.m_sceneObjectLayerIndices.append(self.m_layerNames.index(layer))
        self.m_sceneObjects.append(scene_object)
