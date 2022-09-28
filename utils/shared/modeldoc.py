from dataclasses import dataclass, field
from typing import Literal, Type

@dataclass
class _BaseNode:
    _class: str = __name__
    note: str = ""
    children: list["_Node"] = field(default_factory=list)

    def __post_init__(self):
        self._class = self.__class__.__name__.replace("_", " ")

    def add_nodes(self, *nodes: "_BaseNode"):
        for node in nodes:
            self.children.append(node)
    
    def with_nodes(self, *nodes: "_BaseNode"):
        self.add_nodes(*nodes)
        return self
    
    def find_by_class_bfs(self, cls: Type["_BaseNode"]) -> "_BaseNode":
        """Breadth first search node by class."""
        for child in self.children:
            if isinstance(child, cls):
                return child
        for child in self.children:
            result = child.find_by_class_bfs(cls)
            if result is not None:
                return result

    def find_by_name_dfs(self, name: str, depth=-1) -> "_BaseNode":
        """Depth first search node by name."""
        for child in self.children:
            if child.name == name:
                return child
            if depth == 0:
                break
            result = child.find_by_name_dfs(name, depth-1)
            if result is not None:
                return result

@dataclass
class _Node(_BaseNode):
    "Node with _class, note, name, and children"
    name: str = ""

class resourcepath(str):
    "string path to a resource"
class namelink(str):
    "string link to another node"

mdBaseLists: list[Type[_BaseNode]] = []
def containerof(*node_types):
    def inner(cls):
        # cls is supposed to contain *node_types
        mdBaseLists.append(cls)
        cls._childtypes = node_types
        return cls
    return inner

class ModelDoc:
    
    @dataclass
    class RootNode(_BaseNode):
        model_archetype: str = ""
        primary_associated_entity: str = ""
        anim_graph_name: str = ""
        base_model_name: str = ""

    class Folder(_Node):
        pass

    @dataclass
    class RenderMeshFile(_Node):
        filename: resourcepath = ""
        import_translation: list[float] = field(default_factory=lambda: [0, 0, 0])
        import_rotation: list[float] = field(default_factory=lambda: [0, 0, 0])
        import_scale: float = 1.0
        align_origin_x_type: str = "None"
        align_origin_y_type: str = "None"
        align_origin_z_type: str = "None"
        parent_bone: namelink = ""
        import_filter: dict = field(
            default_factory=lambda:dict(
                exclude_by_default = False,
                exception_list = [  ]
            )
        )

    @dataclass
    class AnimFile(_Node):
        activity_name: str = ""
        activity_weight: int = 1
        weight_list_name: str = ""
        fade_in_time: float = 0.2
        fade_out_time: float = 0.2
        looping: bool = False
        delta: bool = False
        worldSpace: bool = False
        hidden: bool = False
        anim_markup_ordered: bool = False
        disable_compression: bool = False
        source_filename: resourcepath = ""
        start_frame: int = -1
        end_frame: int = -1
        framerate: int = -1.0
        take: int = 0
        reverse: bool = False

    @dataclass
    class PhysicsHullFile(_Node):
        parent_bone: str = ""
        surface_prop: str = "default"
        collision_tags: str = "solid"
        recenter_on_parent_bone: bool = False
        offset_origin = [ 0.0, 0.0, 0.0 ]
        offset_angles = [ 0.0, 0.0, 0.0 ]
        align_origin_x_type: str = "None"
        align_origin_y_type: str = "None"
        align_origin_z_type: str = "None"
        filename: resourcepath = ""
        import_scale: float = 1.0
        faceMergeAngle: float = 10.0
        maxHullVertices: int = 0
        import_mode: str = "SingleHull"
        optimization_algorithm: str = "QEM"
        import_filter: dict = field(
            default_factory=lambda:dict(
                exclude_by_default = False,
                exception_list = [  ]
            )
        )

    @dataclass
    class BodyGroupChoice(_Node):
        meshes: list[namelink] = field(default_factory=list) # list of names of meshes

    @dataclass
    class LODGroup(_Node):
        switch_threshold: float = 0.0
        meshes: list[namelink] = field(default_factory=list) # list of names of meshes

    @dataclass
    class Attachment(_Node):
        parent_bone: namelink = ""
        relative_origin: list[float] = field(default_factory=lambda: [0, 0, 0])
        relative_angles: list[float] = field(default_factory=lambda: [0, 0, 0])
        weight: float = 1.0
        ignore_rotation: bool = False

    @dataclass
    class GenericGameData(_Node):
        game_class: str = ""
        game_keys: dict = field(default_factory=dict)


    @dataclass
    class Bone(_Node):
        origin: list[float] = field(default_factory=lambda: [0, 0, 0])
        angles: list[float] = field(default_factory=lambda: [0, 0, 0])
        do_not_discard: bool = True

    @dataclass
    class DefaultMaterialGroup(_Node):
        remaps: list[dict[Literal["from"] | Literal["to"], resourcepath]] = field(default_factory=list)
        use_global_default: bool = False
        global_default_material: resourcepath = ""
    
    @dataclass
    class MaterialGroup(_Node):
        remaps: list[dict[Literal["from"] | Literal["to"], resourcepath]] = field(default_factory=list)

    @dataclass
    class Bounds_Hull(_Node):
        """
        If this node is present, set the model hull bounds explicitly.  Normally the model hull bounds is derived from the physics hull bounds at model load time.
        """
        mins: list[float] = field(default_factory=lambda: [ -1.0, -1.0, 0.0 ])
        maxs: list[float] = field(default_factory=lambda: [ 1.0, 1.0, 1.0 ])

    @dataclass
    class Bounds_View(_Node):
        """
        If this node is present, set the model view bounds explicitly.  Normally the model view bounds is derived from the render mesh bounds at model load time.
        """
        mins: list[float] = field(default_factory=lambda: [ -1.0, -1.0, 0.0 ])
        maxs: list[float] = field(default_factory=lambda: [ 1.0, 1.0, 1.0 ])

    @dataclass
    class Prefab(_Node):
        target_file: resourcepath = ""

    @staticmethod
    def get_container(node_type: Type[_Node]):
        for basecontainer in mdBaseLists:
            if node_type in basecontainer._childtypes:
                return basecontainer

    #@containerof(BodyGroupChoice)
    @dataclass
    class BodyGroup(_Node):
        name: str = ""
        hidden_in_tools: bool = False

    @containerof(BodyGroup)
    class BodyGroupList(_BaseNode): pass

    @containerof(LODGroup)
    class LODGroupList(_BaseNode): pass

    @containerof(RenderMeshFile)
    class RenderMeshList(_BaseNode): pass
    
    @containerof(AnimFile)
    @dataclass
    class AnimationList(_BaseNode):
        default_root_bone_name: str = ""
    
    @containerof(Bone)
    class Skeleton(_BaseNode): pass
    
    @containerof(DefaultMaterialGroup, MaterialGroup)
    class MaterialGroupList(_BaseNode): pass

    @containerof(PhysicsHullFile)
    class PhysicsShapeList(_BaseNode): pass

    @containerof(Attachment)
    class AttachmentList(_BaseNode): pass

    @containerof(GenericGameData)
    class GameDataList(_BaseNode): pass

    @containerof(Bounds_Hull, Bounds_View)
    class ModelDataList(_BaseNode): pass

    @containerof(Prefab)
    class PrefabList(_BaseNode): pass
