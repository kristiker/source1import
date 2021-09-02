import vdf
import re
from io import TextIOWrapper
from .fs import VMFFileSystem, AnyBinaryIO, AnyTextIO
from .vmt import VMT
from typing import List,  Callable, Iterator, Tuple, Optional, NamedTuple, Union, TypeVar, Any


VDFDictKey = Union[str, Tuple[int, str]]


class LowerCaseVDFDict(vdf.VDFDict):
    def _normalize_key(self, key: VDFDictKey) -> Tuple[int, str]:
        key = super()._normalize_key(key)
        return (key[0], key[1].lower())

    def __setitem__(self, key: VDFDictKey, value: Any) -> None:
        if isinstance(key, str):
            key = key.lower()
        if isinstance(key, tuple):
            key = (key[0], key[1].lower())
        super().__setitem__(key, value)

    def get_all_for(self, key: str) -> List[Any]:
        return super().get_all_for(key.lower())

    def remove_all_for(self, key: str) -> None:
        super().remove_all_for(key.lower())


class VMFParseException(Exception):
    def __init__(self, msg: str, context: str = None):
        super().__init__(f"VMF parsing failed: {msg}")
        self.msg = msg
        self._stack: List[str] = []
        if context is not None:
            self._stack.append(context)

    def __str__(self) -> str:
        return f"VMF parsing failed: {' '.join(reversed(self._stack))} {self.msg}"

    def pushstack(self, msg: str, context: str = None) -> None:
        self._stack.append(msg)
        if context is not None:
            self._stack.append(context)


_RT = TypeVar("_RT")


class _VMFParser():
    def __init__(self) -> None:
        self._context: Optional[str] = None

    def _check_str(self, name: str, value: Union[str, dict], full_name: str = None) -> str:
        if full_name is None:
            full_name = name
        if not isinstance(value, str):
            return str(value)
            raise VMFParseException(f"{name} is not a str", self._context)
        return value

    def _parse_str(self, name: str, vdict: dict, full_name: str = None) -> str:
        if full_name is None:
            full_name = name
        if name not in vdict:
            raise VMFParseException(f"{full_name} doesn't exist", self._context)
        value = vdict[name]
        return self._check_str(name, value, full_name)

    def _parse_int(self, name: str, value: str) -> int:
        try:
            return int(value)
        except ValueError:
            raise VMFParseException(f"{name} is not a valid int", self._context)

    def _parse_int_str(self, name: str, vdict: dict) -> int:
        value = self._parse_str(name, vdict)
        return self._parse_int(name, value)

    def _parse_int_list(self, name: str, value: str) -> List[int]:
        try:
            return [int(s) for s in value.split(" ") if s != ""]
        except ValueError:
            raise VMFParseException(f"{name} contains an invalid int", self._context)

    def _parse_int_list_str(self, name: str, vdict: dict) -> List[int]:
        value = self._parse_str(name, vdict)
        return self._parse_int_list(name, value)

    def _parse_float(self, name: str, value: str) -> float:
        try:
            return float(value)
        except ValueError:
            raise VMFParseException(f"{name} is not a valid float", self._context)
        except OverflowError:
            raise VMFParseException(f"{name} is out of range", self._context)

    def _parse_float_str(self, name: str, vdict: dict) -> float:
        value = self._parse_str(name, vdict)
        return self._parse_float(name, value)

    def _parse_bool(self, name: str, vdict: dict) -> bool:
        intv = self._parse_int_str(name, vdict)
        if intv not in (0, 1):
            raise VMFParseException(f"{name} is not a valid bool", self._context)
        return bool(intv)

    def _check_dict(self, name: str, value: Union[str, dict]) -> vdf.VDFDict:
        if not isinstance(value, dict):
            raise VMFParseException(f"{name} is not a dict", self._context)
        return value

    def _parse_dict(self, name: str, vdict: dict) -> vdf.VDFDict:
        if name not in vdict:
            raise VMFParseException(f"{name} doesn't exist", self._context)
        value = vdict[name]
        return self._check_dict(name, value)

    def _iter_parse_matrix(self, name: str, vdict: dict) -> Iterator[Tuple[int, str, str]]:
        if name not in vdict:
            return
        value = self._check_dict(name, vdict[name])
        for row_name in value:
            full_name = f"{name} {row_name}"
            if row_name[:3] != "row":
                raise VMFParseException(f"{name} contains invalid key", self._context)
            try:
                row_idx = int(row_name[3:])
            except ValueError:
                raise VMFParseException(f"{name} contains invalid row index", self._context)
            row_value: str = value[row_name]
            if not isinstance(row_value, str):
                raise VMFParseException(f"{name} contains a non-str value", self._context)
            yield (row_idx, row_value, full_name)

    def _parse_custom(self, parser: Callable[..., _RT], name: str, *args: Any) -> _RT:
        try:
            return parser(*args)
        except VMFParseException as e:
            e.pushstack(name, self._context)
            raise

    def _parse_custom_str(self, parser: Callable[[str], _RT], name: str, vdict: dict) -> _RT:
        value = self._parse_str(name, vdict)
        return self._parse_custom(parser, name, value)


_VECTOR_REGEX = re.compile(r"^\[(-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*)]$")


class VMFVector(NamedTuple):
    """An XYZ location (or rotation) given by 3 float values."""
    x: float
    y: float
    z: float

    @staticmethod
    def parse_str(data: str) -> 'VMFVector':
        nums = data.split(" ")
        assert len(nums) == 3
        if len(nums) != 3:
            raise VMFParseException("vector doesn't contain 3 values")
        try:
            return VMFVector(*(float(s) for s in nums))
        except ValueError:
            raise VMFParseException("vector contains an invalid float")
        except OverflowError:
            raise VMFParseException("vector float out of range")

    @staticmethod
    def parse_sq_brackets(data: str) -> 'VMFVector':
        match = _VECTOR_REGEX.match(data)
        if match is None:
            raise VMFParseException("vector syntax is invalid (expected square-bracketed)")
        try:
            return VMFVector(*(float(s) for s in match.groups()))
        except ValueError:
            raise VMFParseException("vector contains an invalid float")
        except OverflowError:
            raise VMFParseException("vector float out of range")

    @staticmethod
    def parse_tuple(data: Tuple[str, str, str]) -> 'VMFVector':
        try:
            return VMFVector(*(float(s) for s in data))
        except ValueError:
            raise VMFParseException("vector contains an invalid float")
        except OverflowError:
            raise VMFParseException("vector float out of range")


class VMFColor(NamedTuple):
    """A color value using 3 integers between 0 and 255."""
    r: int
    g: int
    b: int

    @staticmethod
    def parse(data: str) -> 'VMFColor':
        values = [s for s in data.split(" ") if s != ""]
        if len(values) < 3:
            raise VMFParseException("color doesn't have at least 3 values")
        try:
            color = VMFColor(*(int(s) for s in values[:3]))
        except ValueError:
            raise VMFParseException("color contains an invalid int")
        return color

    @staticmethod
    def parse_with_brightness(data: str) -> Tuple['VMFColor', float]:
        values = [s for s in data.split(" ") if s != ""]
        if len(values) < 3:
            raise VMFParseException("color with brightness doesn't have at least 3 values")
        try:
            color = VMFColor(*(int(s) for s in values[:3]))
        except ValueError:
            raise VMFParseException("color contains an invalid int")
        if len(values) > 3:
            try:
                brightness = float(values[3])
            except ValueError:
                raise VMFParseException("color brightness is an invalid float")
            except OverflowError:
                raise VMFParseException("color brightness is out of range")
        else:
            brightness = 0.0
        return (color, brightness)


class VMFEntity(_VMFParser):
    """An entity."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__()
        self.data = data
        self.fs = fs
        self.id = self._parse_int_str("id", data)
        """This is a unique number among other entity ids ."""
        self._context = f"(id {self.id})"
        self.classname: str = self._parse_str("classname", data)
        """This is the name of the entity class."""

        self.origin: Optional[VMFVector] = None
        """This is the point where the point entity exists."""
        if "origin" in data:
            self.origin = self._parse_custom_str(VMFVector.parse_str, "origin", data)
        self.spawnflags: Optional[int] = None
        """Indicates which flags are enabled on the entity."""
        if "spawnflags" in data:
            self.spawnflags = self._parse_int_str("spawnflags", data)


class VMFPointEntity(VMFEntity):
    """A point based entity."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)
        if self.origin is None:
            raise VMFParseException("doesn't have an origin", self._context)
        self.origin: VMFVector


class VMFPropEntity(VMFPointEntity):
    """Adds a model to the world."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)
        self.angles: VMFVector
        """This entity's orientation in the world."""
        if "angles" in data:
            self.angles = self._parse_custom_str(VMFVector.parse_str, "angles", data)
        else:
            self.angles = VMFVector(0, 0, 0)
        if "modelscale" in data:
            self.scale = self._parse_float_str("modelscale", data)
        elif "uniformscale" in data:
            self.scale = self._parse_float_str("uniformscale", data)
        else:
            self.scale = 1
        self.model = self._parse_str("model", data)
        """The model this entity should appear as."""
        self.skin: int
        """Some models have multiple skins. This value selects from the index, starting with 0."""
        if "skin" in data:
            self.skin = self._parse_int_str("skin", data)
        else:
            self.skin = 0
        if "rendercolor" in data:
            self.rendercolor = self._parse_custom_str(VMFColor.parse, "rendercolor", data)
        else:
            self.rendercolor = VMFColor(255, 255, 255)
        if "renderamt" in data:
            self.renderamt = self._parse_int_str("renderamt", data)
        else:
            self.renderamt = 255

    def open_model(self) -> AnyBinaryIO:
        return self.fs.open_file(self.model)


class VMFOverlayEntity(VMFPointEntity):
    """More powerful version of a material projected onto existing surfaces."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)

        self.material = self._parse_str("material", data)
        """The material to overlay."""
        self.materialpath = "materials/" + self.material + ".vmt"

        self.sides = self._parse_int_list_str("sides", data)
        """Faces on which the overlay will be applied."""

        self.renderorder: Optional[int] = None
        """Higher values render after lower values (on top). This value can be 0–3."""
        if "RenderOrder" in data:
            self.renderorder = self._parse_int_str("RenderOrder", data)

        self.startu = self._parse_float_str("StartU", data)
        """Texture coordinates for the image."""
        self.startv = self._parse_float_str("StartV", data)
        """Texture coordinates for the image."""
        self.endu = self._parse_float_str("EndU", data)
        """Texture coordinates for the image."""
        self.endv = self._parse_float_str("EndV", data)
        """Texture coordinates for the image."""

        self.basisorigin: VMFVector = self._parse_custom_str(VMFVector.parse_str, "BasisOrigin", data)
        """Offset of the surface from the position of the overlay entity."""
        self.basisu: VMFVector = self._parse_custom_str(VMFVector.parse_str, "BasisU", data)
        """Direction of the material's X-axis."""
        self.basisv: VMFVector = self._parse_custom_str(VMFVector.parse_str, "BasisV", data)
        """Direction of the material's Y-axis."""
        self.basisnormal: VMFVector = self._parse_custom_str(VMFVector.parse_str, "BasisNormal", data)
        """Direction out of the surface."""

        self.uv0: VMFVector = self._parse_custom_str(VMFVector.parse_str, "uv0", data)
        self.uv1: VMFVector = self._parse_custom_str(VMFVector.parse_str, "uv1", data)
        self.uv2: VMFVector = self._parse_custom_str(VMFVector.parse_str, "uv2", data)
        self.uv3: VMFVector = self._parse_custom_str(VMFVector.parse_str, "uv3", data)

    def open_material_file(self) -> TextIOWrapper:
        return self.fs.open_file_utf8(self.materialpath)

    def get_material(self, allow_patch: bool = False) -> VMT:
        with self.open_material_file() as vmt_f:
            return VMT(vmt_f, self.fs, allow_patch=allow_patch)


class VMFLightEntity(VMFPointEntity):
    """Creates an invisible, static light source that shines in all directions."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)
        color, brightness = self._parse_custom_str(VMFColor.parse_with_brightness, "_light", data)
        self.color: VMFColor = color
        """The RGB color of the light."""
        self.brightness: float = brightness
        """The brightness of the light."""

        if "_lightHDR" in data:
            color, brightness = self._parse_custom_str(VMFColor.parse_with_brightness, "_lightHDR", data)
            self.hdr_color: VMFColor = color
            """Color override used in HDR mode. Default is -1 -1 -1 which means no change."""
            self.hdr_brightness: float = brightness
            """Brightness override used in HDR mode. Default is 1 which means no change."""
        else:
            self.hdr_color = VMFColor(-1, -1, -1)
            self.hdr_brightness = 1.0
        if "_lightscaleHDR" in data:
            self.hdr_scale = self._parse_float_str("_lightscaleHDR", data)
            """A simple intensity multiplier used when compiling HDR lighting."""
        else:
            self.hdr_scale = 1.0

        self.style: Optional[int] = None
        """Various Custom Appearance presets."""
        if "style" in data:
            self.style = self._parse_int_str("style", data)
        self.constant_attn: Optional[float] = None
        """Determines how the intensity of the emitted light falls off over distance."""
        if "_constant_attn" in data:
            self.constant_attn = self._parse_float_str("_constant_attn", data)
        self.linear_attn: Optional[float] = None
        """Determines how the intensity of the emitted light falls off over distance."""
        if "_linear_attn" in data:
            self.linear_attn = self._parse_float_str("_linear_attn", data)
        self.quadratic_attn: Optional[float] = None
        """Determines how the intensity of the emitted light falls off over distance."""
        if "_quadratic_attn" in data:
            self.quadratic_attn = self._parse_float_str("_quadratic_attn", data)
        self.fifty_percent_distance: Optional[float] = None
        """Distance at which brightness should have fallen to 50%. Overrides attn if non-zero."""
        if "_fifty_percent_distance" in data:
            self.fifty_percent_distance = self._parse_float_str("_fifty_percent_distance", data)
        self.zero_percent_distance: Optional[float] = None
        """Distance at which brightness should have fallen to (1/256)%. Overrides attn if non-zero."""
        if "_zero_percent_distance" in data:
            self.zero_percent_distance = self._parse_float_str("_zero_percent_distance", data)


class VMFSpotLightEntity(VMFLightEntity):
    """A cone-shaped, invisible light source."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)
        self.angles: VMFVector
        """This entity's orientation in the world."""
        if "angles" in data:
            self.angles = self._parse_custom_str(VMFVector.parse_str, "angles", data)
        else:
            self.angles = VMFVector(0, 0, 0)
        self.pitch = self._parse_float_str("pitch", data)
        """Used instead of angles value for reasons unknown."""

        self.inner_cone = self._parse_float_str("_inner_cone", data)
        """The angle of the inner spotlight beam."""
        self.cone = self._parse_float_str("_cone", data)
        """The angle of the outer spotlight beam."""
        self.exponent = self._parse_float_str("_exponent", data)
        """Changes the distance between the umbra and penumbra cone."""


class VMFEnvLightEntity(VMFLightEntity):
    """Casts parallel directional lighting and diffuse skylight from the toolsskybox texture."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)
        self.angles: VMFVector
        """This entity's orientation in the world."""
        if "angles" in data:
            self.angles = self._parse_custom_str(VMFVector.parse_str, "angles", data)
        else:
            self.angles = VMFVector(0, 0, 0)
        if "pitch" in data:
            self.pitch = self._parse_float_str("pitch", data)
        else:
            self.pitch = self.angles[0]
        """Used instead of angles value for reasons unknown."""

        color, brightness = self._parse_custom_str(VMFColor.parse_with_brightness, "_ambient", data)
        self.amb_color: VMFColor = color
        """Color of the diffuse skylight."""
        self.amb_brightness: float = brightness
        """Brightness of the diffuse skylight."""

        if "_ambientHDR" in data:
            color, brightness = self._parse_custom_str(VMFColor.parse_with_brightness, "_ambientHDR", data)
            self.amb_hdr_color: VMFColor = color
            """Override for ambient color when compiling HDR lighting."""
            self.amb_hdr_brightness: float = brightness
            """Override for ambient brightness when compiling HDR lighting."""
        else:
            self.amb_hdr_color = VMFColor(-1, -1, -1)
            self.amb_hdr_brightness = 1.0
        if "_AmbientScaleHDR" in data:
            self.amb_hdr_scale = self._parse_float_str("_AmbientScaleHDR", data)
            """Amount to scale the ambient light by when compiling for HDR."""
        else:
            self.amb_hdr_scale = 1.0

        if "SunSpreadAngle" in data:
            self.sun_spread_angle = self._parse_float_str("SunSpreadAngle", data)
            """The angular extent of the sun for casting soft shadows."""
        else:
            self.sun_spread_angle = 0.0


class VMFSkyCameraEntity(VMFPointEntity):
    """Used to mark the position of the map's origin inside the 3D Skybox."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)
        self.angles: VMFVector
        """This entity's orientation in the world."""
        if "angles" in data:
            self.angles = self._parse_custom_str(VMFVector.parse_str, "angles", data)
        else:
            self.angles = VMFVector(0, 0, 0)

        if "scale" in data:
            self.scale = self._parse_float_str("scale", data)
            """This number determines how large objects in your skybox will seem relative to the map."""
        else:
            self.scale = 16.0

        if "fogenable" in data:
            self.fog_enable = self._parse_bool("fogenable", data)
        else:
            self.fog_enable = False
        if "fogblend" in data:
            self.fog_blend = self._parse_float_str("fogblend", data)
        else:
            self.fog_blend = 0.0
        if "fogcolor" in data:
            self.fog_color = self._parse_custom_str(VMFColor.parse, "fogcolor", data)
        else:
            self.fog_color = VMFColor(255, 255, 255)
        if "fogcolor2" in data:
            self.fog_color2 = self._parse_custom_str(VMFColor.parse, "fogcolor2", data)
        else:
            self.fog_color2 = VMFColor(255, 255, 255)
        if "fogdir" in data:
            self.fog_dir = self._parse_custom_str(VMFVector.parse_str, "fogdir", data)
        if "fogstart" in data:
            self.fog_start = self._parse_float_str("fogstart", data)
        if "fogend" in data:
            self.fog_end = self._parse_float_str("fogend", data)
        if "fogmaxdensity" in data:
            self.fog_max_density = self._parse_float_str("fogmaxdensity", data)


_PLANE_REGEX = re.compile(r"^\((-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*)\) "
                          r"\((-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*)\) "
                          r"\((-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*)\)$")


class VMFPlane(NamedTuple):
    """"A fundamental two-dimensional object defined by three points."""
    btm_l: VMFVector
    top_l: VMFVector
    top_r: VMFVector

    @staticmethod
    def parse(data: str) -> 'VMFPlane':
        match = _PLANE_REGEX.match(data)
        if match is None:
            raise VMFParseException("plane syntax is invalid")
        try:
            floats = [float(s) for s in match.groups()]
        except ValueError:
            raise VMFParseException("plane contains an invalid float")
        except OverflowError:
            raise VMFParseException("plane float out of range")
        return VMFPlane(VMFVector(*floats[:3]),
                        VMFVector(*floats[3:6]),
                        VMFVector(*floats[6:9]))


_AXIS_REGEX = re.compile(r"^\[(-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*) (-?\d*\.?\d*e?-?\d*)] "
                         r"(-?\d*\.?\d*e?-?\d*)$")


class VMFAxis(NamedTuple):
    """Texture specific axis."""
    x: float
    y: float
    z: float
    trans: float
    scale: float

    @staticmethod
    def parse(data: str) -> 'VMFAxis':
        match = _AXIS_REGEX.match(data)
        if match is None:
            raise VMFParseException("axis syntax is invalid")
        try:
            floats = [float(s) for s in match.groups()]
        except ValueError:
            raise VMFParseException("axis contains an invalid float")
        except OverflowError:
            raise VMFParseException("axis float out of range")
        return VMFAxis(*floats)


class VMFDispInfo(_VMFParser):
    """Deals with all the information for a displacement map."""
    def __init__(self, data: vdf.VDFDict):
        super().__init__()
        self.power = self._parse_int_str("power", data)
        """Used to calculate the number of rows and columns."""
        self.triangle_dimension = 2 ** self.power
        """The number of rows and columns in triangles."""
        self.dimension = self.triangle_dimension + 1
        """The number of rows and columns in vertexes."""
        self.startposition: VMFVector = self._parse_custom_str(VMFVector.parse_sq_brackets, "startposition", data)
        """The position of the bottom left corner in an actual x y z position."""
        self.elevation = self._parse_float_str("elevation", data)
        """A universal displacement in the direction of the vertex's normal added to all of the points."""
        self.subdiv = self._parse_bool("subdiv", data)
        """Marks whether or not the displacement is being subdivided."""

        self.normals: List[List[VMFVector]] = [[VMFVector(0, 0, 0) for _ in range(self.dimension)]
                                               for _ in range(self.dimension)]
        """Defines the normal line for each vertex."""
        for row_idx, row_value, row_name in self._iter_parse_matrix("normals", data):
            row_nums_it = iter(row_value.split(" "))
            vec_tuple: Tuple[str, str, str]
            for idx, vec_tuple in enumerate(zip(row_nums_it, row_nums_it, row_nums_it)):
                self.normals[row_idx][idx] = self._parse_custom(VMFVector.parse_tuple, row_name, vec_tuple)

        self.distances: List[List[float]] = [[0 for _ in range(self.dimension)] for _ in range(self.dimension)]
        """The distance values represent how much the vertex is moved along the normal line."""
        for row_idx, row_value, row_name in self._iter_parse_matrix("distances", data):
            for idx, num_str in enumerate(row_value.split(" ")):
                self.distances[row_idx][idx] = self._parse_float(row_name, num_str)

        self.offsets: List[List[VMFVector]] = [[VMFVector(0, 0, 0) for _ in range(self.dimension)]
                                               for _ in range(self.dimension)]
        """Lists all the default positions for each vertex in a displacement map."""
        for row_idx, row_value, row_name in self._iter_parse_matrix("offsets", data):
            row_nums_it = iter(row_value.split(" "))
            for idx, vec_tuple in enumerate(zip(row_nums_it, row_nums_it, row_nums_it)):
                self.offsets[row_idx][idx] = self._parse_custom(VMFVector.parse_tuple, row_name, vec_tuple)

        self.offset_normals: List[List[VMFVector]] = [[VMFVector(0, 0, 0) for _ in range(self.dimension)]
                                                      for _ in range(self.dimension)]
        """Defines the default normal lines that the normals are based from."""
        for row_idx, row_value, row_name in self._iter_parse_matrix("offset_normals", data):
            row_nums_it = iter(row_value.split(" "))
            for idx, vec_tuple in enumerate(zip(row_nums_it, row_nums_it, row_nums_it)):
                self.offset_normals[row_idx][idx] = self._parse_custom(VMFVector.parse_tuple, row_name, vec_tuple)

        self.alphas: List[List[float]] = [[0 for _ in range(self.dimension)] for _ in range(self.dimension)]
        """Contains a value for each vertex that represents how much of which texture to shown in blended materials."""
        for row_idx, row_value, row_name in self._iter_parse_matrix("alphas", data):
            for idx, num_str in enumerate(row_value.split(" ")):
                self.alphas[row_idx][idx] = self._parse_float(row_name, num_str)

        self.triangle_tags: List[List[Tuple[int, int]]] = [[(0, 0) for _ in range(self.triangle_dimension)]
                                                           for _ in range(self.triangle_dimension)]
        """Contains information specific to each triangle in the displacement."""
        for row_idx, row_value, row_name in self._iter_parse_matrix("triangle_tags", data):
            row_nums_it = iter(row_value.split(" "))
            for idx, tag_tuple in enumerate(zip(row_nums_it, row_nums_it)):
                self.triangle_tags[row_idx][idx] = (self._parse_int(row_name, tag_tuple[0]),
                                                    self._parse_int(row_name, tag_tuple[1]))

        allowed_verts_dict = self._parse_dict("allowed_verts", data)
        allowed_verts_value = self._parse_str("10", allowed_verts_dict, "allowed_verts 10")
        self.allowed_verts = tuple(self._parse_int_list("allowed_verts 10", allowed_verts_value))
        """This states which vertices share an edge with another displacement map, but not a vertex."""


class VMFSide(_VMFParser):
    """Defines all the data relevant to one side and just to that side."""
    def __init__(self, data: vdf.VDFDict):
        super().__init__()
        """File system for opening game files."""
        self.id = self._parse_int_str("id", data)
        """A unique value among other sides ids."""
        self._context = f"(id {self.id})"
        self.plane: VMFPlane = self._parse_custom_str(VMFPlane.parse, "plane", data)
        """Defines the orientation of the face."""
        self.material = self._parse_str("material", data)
        """The directory and name of the texture the side has applied to it."""
        self.materialpath = "materials/" + self.material + ".vmt"
        self.uaxis: VMFAxis = self._parse_custom_str(VMFAxis.parse, "uaxis", data)
        """The u-axis and v-axis are the texture specific axes."""
        self.vaxis: VMFAxis = self._parse_custom_str(VMFAxis.parse, "vaxis", data)
        """The u-axis and v-axis are the texture specific axes."""
        if "rotation" in data:
            self.rotation: Optional[float] = self._parse_float_str("rotation", data)
        else:
            self.rotation = None
            """The rotation of the given texture on the side."""
        if "lightmapscale" in data:
            self.lightmapscale: Optional[int] = self._parse_int_str("lightmapscale", data)
        else:
            self.lightmapscale = None
        """The light map resolution on the face."""
        if "smoothing_groups" in data:
            self.smoothing_groups: Optional[bytes] = self._parse_int_str("smoothing_groups", data).to_bytes(4, 'little')
            """"Select a smoothing group to use for lighting on the face."""
        else:
            self.smoothing_groups = None

        self.dispinfo: Optional[VMFDispInfo] = None
        """Deals with all the information for a displacement map."""
        if "dispinfo" in data:
            dispinfo_dict = self._parse_dict("dispinfo", data)
            self.dispinfo = self._parse_custom(VMFDispInfo, "dispinfo", dispinfo_dict)

    def open_material_file(self) -> TextIOWrapper:
        return self.fs.open_file_utf8(self.materialpath)

    def get_material(self, allow_patch: bool = False) -> VMT:
        with self.open_material_file() as vmt_f:
            return VMT(vmt_f, self.fs, allow_patch=allow_patch)


class VMFSolid(_VMFParser):
    """Represents 1 single brush in Hammer."""
    def __init__(self, data: vdf.VDFDict):
        """File system for opening game files."""
        self.id = self._parse_int_str("id", data)
        """A unique value among other solids' IDs."""
        self._context = f"(id {self.id})"
        dict_sides = data.get_all_for("side")
        self.sides: List[VMFSide] = list()
        for side in dict_sides:
            side = self._check_dict("side", side)
            self.sides.append(self._parse_custom(VMFSide, "side", side))


class VMFBrushEntity(VMFEntity):
    """A brush based entity."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)
        dict_solids = data.get_all_for("solid")
        self.solids: List[VMFSolid] = list()
        for solid in dict_solids:
            if not isinstance(solid, vdf.VDFDict):
                continue
            self.solids.append(self._parse_custom(VMFSolid, "solid", solid, self.fs))


class VMFWorldEntity(VMFBrushEntity):
    """Contains all the world brush information for Hammer."""
    def __init__(self, data: vdf.VDFDict, fs: VMFFileSystem):
        super().__init__(data, fs)
        if self.classname != "worldspawn":
            raise VMFParseException("classname is not worldspawn")
        self.skyname = self._parse_str("skyname", data)
        """The name of the skybox to be used."""


class VMF(_VMFParser):
    def __init__(self, file: AnyTextIO, fs: VMFFileSystem = VMFFileSystem()):
        super().__init__()
        self.fs = fs
        """File system for opening game files."""
        vdf_dict = vdf.load(file, mapper=LowerCaseVDFDict, merge_duplicate_keys=False, escaped=False)

        if "versioninfo" in vdf_dict:
            versioninfo = self._parse_dict("versioninfo", vdf_dict)
            self.editorversion: Optional[int] = self._parse_int_str("editorversion", versioninfo)
            """The version of Hammer used to create the file, version 4.00 is "400"."""
            self.editorbuild: Optional[int] = self._parse_int_str("editorbuild", versioninfo)
            """The patch number of Hammer the file was generated with."""
            self.mapversion: Optional[int] = self._parse_int_str("mapversion", versioninfo)
            """This represents how many times you've saved the file, useful for comparing old or new versions."""
            self.prefab: Optional[int] = self._parse_bool("prefab", versioninfo)
            """Whether this is a full map or simply a collection of prefabricated objects."""
        else:
            self.editorversion = None
            self.editorbuild = None
            self.mapversion = None
            self.prefab = None

        world_dict = self._parse_dict("world", vdf_dict)
        self.world: VMFWorldEntity = self._parse_custom(VMFWorldEntity, "world", world_dict, self.fs)
        """"Contains all the world brush information for Hammer."""

        self.entities: List[VMFEntity] = list()
        """List of all entities in the map."""
        self.overlay_entities: List[VMFOverlayEntity] = list()
        """List of info_overlays in the map."""
        self.sky_camera_entity: Optional[VMFSkyCameraEntity] = None
        self.env_light_entity: Optional[VMFEnvLightEntity] = None
        self.spot_light_entities: List[VMFSpotLightEntity] = list()
        """List of light_spots in the map."""
        self.light_entities: List[VMFLightEntity] = list()
        """List of other lights in the map."""
        self.func_entities: List[VMFBrushEntity] = list()
        """List of func (brush) entities in the map."""
        self.trigger_entities: List[VMFBrushEntity] = list()
        """List of trigger (brush) entites in the map."""
        self.prop_entities: List[VMFPropEntity] = list()
        """List of prop entities in the map."""

        dict_entities = vdf_dict.get_all_for("entity")
        for entity in dict_entities:
            entity = self._check_dict("entity", entity)
            classname = self._parse_str("classname", entity, "entity classname")
            entity_inst: VMFEntity
            if classname == "info_overlay":
                entity_inst = self._parse_custom(VMFOverlayEntity, "entity (info_overlay)", entity, self.fs)
                self.overlay_entities.append(entity_inst)
            elif classname == "sky_camera":
                entity_inst = self._parse_custom(VMFSkyCameraEntity, "entity (sky_camera)", entity, self.fs)
                self.sky_camera_entity = entity_inst
            elif classname == "light_environment":
                entity_inst = self._parse_custom(VMFEnvLightEntity, "entity (light_environment)", entity, self.fs)
                self.env_light_entity = entity_inst
            elif classname == "light_spot":
                entity_inst = self._parse_custom(VMFSpotLightEntity, "entity (light_spot)", entity, self.fs)
                self.spot_light_entities.append(entity_inst)
            elif classname.startswith("light"):
                entity_inst = self._parse_custom(VMFLightEntity, "entity (light)", entity, self.fs)
                self.light_entities.append(entity_inst)
            elif classname.startswith("func"):
                entity_inst = self._parse_custom(VMFBrushEntity, "entity (func)", entity, self.fs)
                self.func_entities.append(entity_inst)
            elif classname.startswith("trigger"):
                entity_inst = self._parse_custom(VMFBrushEntity, "entity (trigger)", entity, self.fs)
                self.trigger_entities.append(entity_inst)
            elif classname in ("prop_static", "prop_detail", "prop_ragdoll", "prop_door_rotating",
                               "prop_dynamic", "prop_dynamic_override",
                               "prop_physics", "prop_physics_multiplayer", "prop_physics_override"):
                entity_inst = self._parse_custom(VMFPropEntity, "entity (prop)", entity, self.fs)
                self.prop_entities.append(entity_inst)
            elif "origin" in entity:
                entity_inst = self._parse_custom(VMFPointEntity, "entity", entity, self.fs)
            else:
                entity_inst = self._parse_custom(VMFEntity, "entity", entity, self.fs)
            self.entities.append(entity_inst)
