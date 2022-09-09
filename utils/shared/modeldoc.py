from dataclasses import dataclass, field

@dataclass
class _BaseNode(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    
    _class: str = __name__
    note: str = ""
    children: list["_BaseNode"] = field(default_factory=list)

    def __post_init__(self):
        self._class = self.__class__.__name__
        super().update(**self.__dict__)

    def add_nodes(self, *nodes: "_BaseNode"):
        for node in nodes:
            self.children.append(node)
    
    def with_nodes(self, *nodes: "_BaseNode"):
        self.add_nodes(*nodes)
        return self

@dataclass
class _Node(_BaseNode):
    "Node with _class, note, name, and children"
    name: str = ""

def containerof(*node_types):
    def inner(cls):
        # cls is supposed to contain *node_types
        return cls
    return inner

class ModelDoc:
    
    @dataclass
    class RootNode(_BaseNode):
        model_archetype: str = ""
        primary_associated_entity: str = ""
        anim_graph_name: str = ""
        #base_model_name = ""

    class Folder(_Node):
        pass

    @dataclass
    class RenderMeshFile(_Node):
        filename: str = ""
        import_translation: list[float] = field(default_factory=lambda: [0, 0, 0])
        import_rotation: list[float] = field(default_factory=lambda: [0, 0, 0])
        import_scale: float = 1.0
        align_origin_x_type = "None"
        align_origin_y_type = "None"
        align_origin_z_type = "None"
        parent_bone: str = ""
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
        source_filename: str = ""
        start_frame: int = -1
        end_frame: int = -1
        framerate: int = -1.0
        take: int = 0
        reverse: bool = False
    
    #@containerof(BodyGroup)
    class BodyGroupList(_BaseNode):
        @dataclass
        class BodyGroup(_Node):
            name: str = ""
            hidden_in_tools: bool = False
            
            @dataclass
            class BodyGroupChoice(_Node):
                meshes: list[str] = field(default_factory=list) # list of names of meshes

    @containerof(RenderMeshFile,)
    class RenderMeshList(_BaseNode): pass
    @dataclass
    @containerof(AnimFile)
    class AnimationList(_BaseNode):
        default_root_bone_name: str = ""
