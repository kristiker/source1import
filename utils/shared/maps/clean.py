from typing import Tuple, Optional, List, Dict, Any
from . import vmfpy
from os import path
from mathutils import geometry, Vector, Euler, Matrix
from math import inf, radians, floor, ceil, isclose
from itertools import chain, combinations

from types import SimpleNamespace
bpy = SimpleNamespace
#sys.path.append(r'D:\Games\steamapps\common\Blender\2.93\scripts\modules')
#import bpy
#

# maximum distance to a side plane before cutting a vertice off
_CUT_EPSILON = 0.001


VectorPair = Tuple[Vector, Vector]


def _plane_from_points(p1: Vector, p2: Vector, p3: Vector) -> VectorPair:
    vectors = (p3, p2, p1)
    normal = geometry.normal(vectors)
    return ((vectors[0] + vectors[2]) / 2, normal)


def _intersect_planes(p1: VectorPair, p2: VectorPair, p3: VectorPair) -> Optional[Vector]:
    line: VectorPair = geometry.intersect_plane_plane(*p1, *p2)
    if line[0] is None:
        return None
    return geometry.intersect_line_plane(line[0], line[0] + line[1], *p3)


def _vec_isclose(a: Vector, b: Vector, rel_tol: float = 1e-6, abs_tol: float = 1e-6) -> bool:
    return (isclose(a.x, b.x, rel_tol=rel_tol, abs_tol=abs_tol)
            and isclose(a.y, b.y, rel_tol=rel_tol, abs_tol=abs_tol)
            and isclose(a.z, b.z, rel_tol=rel_tol, abs_tol=abs_tol))


def _tuple_lerp(a: Tuple[float, float], b: Tuple[float, float], amount: float) -> Tuple[float, float]:
    return (a[0] * (1 - amount) + b[0] * amount, a[1] * (1 - amount) + b[1] * amount)


def _srgb2lin(s: float) -> float:
    if s <= 0.0404482362771082:
        lin = s / 12.92
    else:
        lin = pow(((s + 0.055) / 1.055), 2.4)
    return lin


def _vertices_center(verts: List[Vector]) -> Vector:
    return sum(verts, Vector((0, 0, 0))) / len(verts)

SCALE = 1
import pprint
# based on http://mattn.ufoai.org/files/MAPFiles.pdf
def _load_solid(solid: vmfpy.VMFSolid, parent: str):#,
#                collection: bpy.types.Collection, tool_collection: Optional[bpy.types.Collection] = None) -> None:

    solid = vmfpy.VMFSolid(solid)
    name = f"{parent}_{solid.id}"
    
    print(f"[VERBOSE] Building {name}...")
    
    # minimize floating point precision issues
    planes_center = _vertices_center([Vector(point) for side in solid.sides for point in side.plane])
    side_planes: List[VectorPair] = [
        _plane_from_points(*(Vector(point) - planes_center for point in side.plane)) for side in solid.sides
    ]
    vertices: List[Vector] = []  # all vertices for this solid
    materials: List[bpy.types.Material] = []
    # vertices for each face: face_vertices[face_index] = list of indices to vertices
    face_vertices: List[List[int]] = [[] for _ in range(len(side_planes))]
    face_materials: List[int] = []
    face_loop_uvs: List[List[Tuple[float, float]]] = [[] for _ in range(len(side_planes))]
    # intersect every combination of 3 planes to get possible vertices
    idx_a: int
    idx_b: int
    idx_c: int
    for idx_a, idx_b, idx_c in combinations(range(len(side_planes)), 3):
        point = _intersect_planes(side_planes[idx_a], side_planes[idx_b], side_planes[idx_c])
        if point is None:
            continue
        # check that the point is not outside the brush (cut off by any other plane)
        for idx, side_plane in enumerate(side_planes):
            if idx == idx_a or idx == idx_b or idx == idx_c:
                continue
            dist = geometry.distance_point_to_plane(point, *side_plane)
            if dist > _CUT_EPSILON:
                break
        else:
            # check if the point is close enough to any other vertice on the planes to be within error margin
            for v_idx in chain(face_vertices[idx_a], face_vertices[idx_b], face_vertices[idx_c]):
                if _vec_isclose(vertices[v_idx], point, _CUT_EPSILON, _CUT_EPSILON):
                    point_idx = v_idx
                    break
            else:
                point_idx = len(vertices)
                vertices.append(point)
            # the point is on every face plane intersected to create it
            if point_idx not in face_vertices[idx_a]:
                face_vertices[idx_a].append(point_idx)
            if point_idx not in face_vertices[idx_b]:
                face_vertices[idx_b].append(point_idx)
            if point_idx not in face_vertices[idx_c]:
                face_vertices[idx_c].append(point_idx)

    # sort face vertices in clockwise order
    for face_idx, vertice_idxs in enumerate(face_vertices):
        # TODO remove invalid faces instead of erroring?
        if len(vertice_idxs) < 3:
            err = f"INVALID FACE IN {name}: NOT ENOUGH VERTS: {len(vertice_idxs)}"
            print(err)
            print("INVALID MAP OR EPSILON IS TOO BIG")
            print("ALL FACE VERTICES:")
            for v_idx in vertice_idxs:
                for idx in (idx for idx, polys in enumerate(face_vertices) if v_idx in polys):
                    print(f"{idx} Plane({', '.join(str(tuple(v)) for v in solid.sides[idx].plane)})")
                print(f"INTERSECTION --> {v_idx} {tuple(vertices[v_idx])}")
            raise Exception(err)
        # quaternion to convert 3d vertices into 2d vertices on the side plane
        rot_normalize = side_planes[face_idx][1].rotation_difference(Vector((0, 0, 1)))
        # face vertices converted to 2d on the side plane
        face_vertices_2d = [(rot_normalize @ vertices[i]).to_2d() for i in vertice_idxs]
        face_center_vert = sum(face_vertices_2d, Vector((0, 0))) / len(face_vertices_2d)
        # start from the first vertice
        last_line = face_vertices_2d[0] - face_center_vert
        for idx, vertice_idx in enumerate(vertice_idxs[1:], 1):
            # gets the rotation to the last vertice, or infinity if the rotation is negative
            def min_key(t: Tuple[int, Vector]) -> float:
                line = t[1] - face_center_vert
                result = last_line.angle_signed(line)
                return inf if result < 0 else result
            # get the vertice that has the smallest positive rotation to the last one
            # skip already sorted vertices
            next_idx, next_vertice = min(enumerate(face_vertices_2d[idx:], idx), key=min_key)
            last_line = next_vertice - face_center_vert
            # swap the list elements to sort them
            vertice_idxs[idx], vertice_idxs[next_idx] = vertice_idxs[next_idx], vertice_idxs[idx]
            face_vertices_2d[idx], face_vertices_2d[next_idx] = face_vertices_2d[next_idx], face_vertices_2d[idx]

#    # need to track side ids and corresponding verts and faces for overlays
#    if self.import_overlays:
#        for side_idx, side in enumerate(solid.sides):
#            self._side_face_vertices[side.id] = [[i for i in range(len(face_vertices[side_idx]))]]
#            self._side_vertices[side.id] = [vertices[i] + planes_center for i in face_vertices[side_idx]]
#            self._side_normals[side.id] = side_planes[side_idx][1]

    # create uvs and materials
    for side_idx, side in enumerate(solid.sides):
        texture_width, texture_height, material = 1024, 1024, "dev/reflectivity_30"#self._get_material(side.material)
        if material not in materials:
            material_idx = len(materials)
            materials.append(material)
        else:
            material_idx = materials.index(material)
        face_materials.append(material_idx)
        for vertice_idx in face_vertices[side_idx]:
            face_loop_uvs[side_idx].append((
                (((vertices[vertice_idx] + planes_center) @ Vector(side.uaxis[:3]))
                    / (texture_width * side.uaxis.scale) + side.uaxis.trans / texture_width),
                (((vertices[vertice_idx] + planes_center) @ Vector(side.vaxis[:3]))
                    / (texture_height * side.vaxis.scale) + side.vaxis.trans / texture_height) * -1,
            ))

        # normalize uvs
        nearest_u = face_loop_uvs[side_idx][0][0]
        for loop_uv in face_loop_uvs[side_idx]:
            if not abs(loop_uv[0]) > 1:
                nearest_u = 0
                break
            if abs(loop_uv[0]) < abs(nearest_u):
                nearest_u = loop_uv[0]
        else:
            nearest_u = floor(nearest_u) if nearest_u > 0 else ceil(nearest_u)
        nearest_v = face_loop_uvs[side_idx][0][1]
        for loop_uv in face_loop_uvs[side_idx]:
            if not abs(loop_uv[1]) > 1:
                nearest_v = 0
                break
            if abs(loop_uv[1]) < abs(nearest_v):
                nearest_v = loop_uv[1]
        else:
            nearest_v = floor(nearest_v) if nearest_v > 0 else ceil(nearest_v)
        face_loop_uvs[side_idx] = [((uv[0] - nearest_u), (uv[1] - nearest_v)) for uv in face_loop_uvs[side_idx]]

    is_displacement = any(side.dispinfo is not None for side in solid.sides)

    if is_displacement:
        # get rid of non-displacement data
        old_vertices = vertices
        vertices = []
        old_face_vertices = face_vertices
        face_vertices = []
        old_face_materials = face_materials
        face_materials = []
        old_face_loop_uvs = face_loop_uvs
        face_loop_uvs = []
        face_loop_cols: List[List[Tuple[float, float, float, float]]] = []
        original_face_normals: List[Vector] = []
        # build displacements
        for side_idx, side in enumerate(solid.sides):
            if side.dispinfo is None:
                continue
#            if self.import_overlays:
#                self._side_face_vertices[side.id] = []
#                self._side_vertices[side.id] = []
            # displacements must be quadrilateral
            if len(old_face_vertices[side_idx]) != 4:
                err = f"INVALID DISPLACEMENT IN {name}: INVALID AMOUNT OF VERTS: {len(old_face_vertices[side_idx])}"
                raise Exception(err)

            # figure out which corner the start position is from original face vertices by finding closest vertice
            start_pos = Vector(side.dispinfo.startposition) - planes_center
            start_idx = min(range(len(old_face_vertices[side_idx])),
                            key=lambda i: (old_vertices[old_face_vertices[side_idx][i]] - start_pos).length)
            # these are based on empirical research
            top_l_idx = start_idx
            top_r_idx = (start_idx + 3) % len(old_face_vertices[side_idx])
            btm_r_idx = (start_idx + 2) % len(old_face_vertices[side_idx])
            btm_l_idx = (start_idx + 1) % len(old_face_vertices[side_idx])

            # create displacement vertices, 2d array (row, column) for every vertice, contains indices into vertices
            disp_vertices: List[List[int]] = []
            disp_loop_uvs: List[List[Tuple[float, float]]] = []
            for row_idx in range(side.dispinfo.dimension):
                disp_vertices.append([])
                disp_loop_uvs.append([])
                if row_idx == 0:  # take existing vertice from the original face if this is a corner
                    row_vert_i_a = len(vertices)
                    vertices.append(old_vertices[old_face_vertices[side_idx][top_l_idx]].copy())
                    row_vert_uv_a = old_face_loop_uvs[side_idx][top_l_idx]
                    row_vert_i_b = len(vertices)
                    vertices.append(old_vertices[old_face_vertices[side_idx][top_r_idx]].copy())
                    row_vert_uv_b = old_face_loop_uvs[side_idx][top_r_idx]
                elif row_idx == side.dispinfo.dimension - 1:
                    row_vert_i_a = len(vertices)
                    vertices.append(old_vertices[old_face_vertices[side_idx][btm_l_idx]].copy())
                    row_vert_uv_a = old_face_loop_uvs[side_idx][btm_l_idx]
                    row_vert_i_b = len(vertices)
                    vertices.append(old_vertices[old_face_vertices[side_idx][btm_r_idx]].copy())
                    row_vert_uv_b = old_face_loop_uvs[side_idx][btm_r_idx]
                else:  # if this is not a corner, create a new vertice by interpolating between corner vertices
                    row_vert_i_a = len(vertices)
                    vertices.append(old_vertices[old_face_vertices[side_idx][top_l_idx]].lerp(
                        old_vertices[old_face_vertices[side_idx][btm_l_idx]],
                        row_idx / (side.dispinfo.dimension - 1)
                    ))
                    row_vert_uv_a = _tuple_lerp(old_face_loop_uvs[side_idx][top_l_idx],
                                                old_face_loop_uvs[side_idx][btm_l_idx],
                                                row_idx / (side.dispinfo.dimension - 1))
                    row_vert_i_b = len(vertices)
                    vertices.append(old_vertices[old_face_vertices[side_idx][top_r_idx]].lerp(
                        old_vertices[old_face_vertices[side_idx][btm_r_idx]],
                        row_idx / (side.dispinfo.dimension - 1)
                    ))
                    row_vert_uv_b = _tuple_lerp(old_face_loop_uvs[side_idx][top_r_idx],
                                                old_face_loop_uvs[side_idx][btm_r_idx],
                                                row_idx / (side.dispinfo.dimension - 1))
                for col_idx in range(side.dispinfo.dimension):
                    if col_idx == 0:  # if this is a side vertice, it is already created in the row loop
                        col_vert_i = row_vert_i_a
                        col_vert_uv = row_vert_uv_a
                    elif col_idx == side.dispinfo.dimension - 1:
                        col_vert_i = row_vert_i_b
                        col_vert_uv = row_vert_uv_b
                    else:  # if not, create a new vertice by interpolating the corresponding side vertices
                        col_vert_i = len(vertices)
                        vertices.append(vertices[row_vert_i_a].lerp(
                            vertices[row_vert_i_b], col_idx / (side.dispinfo.dimension - 1)
                        ))
                        col_vert_uv = _tuple_lerp(row_vert_uv_a, row_vert_uv_b,
                                                    col_idx / (side.dispinfo.dimension - 1))
                    disp_vertices[row_idx].append(col_vert_i)
                    disp_loop_uvs[row_idx].append(col_vert_uv)
            disp_loop_cols = [[(0., 0., 0., a / 255) for a in row] for row in side.dispinfo.alphas]

#            if self.import_overlays:
#                self._side_vertices[side.id] = [vertices[i] + planes_center for row in disp_vertices for i in row]
#                side_vertice_lookup = {v_i: i for i, v_i in enumerate(i for row in disp_vertices for i in row)}

            # create displacement faces
            for row_idx in range(len(disp_vertices) - 1):
                for col_idx in range(len(disp_vertices[row_idx]) - 1):
                    face_materials.extend((old_face_materials[side_idx],) * 2)
                    # this creates a checker pattern of quads consisting of two triangles from the verts
                    # the diagonal line of the quad is oriented / in half of the quads and \ in others
                    if row_idx % 2 == col_idx % 2:
                        disp_face_indexes = (
                            ((row_idx + 1, col_idx), (row_idx, col_idx), (row_idx + 1, col_idx + 1)),
                            ((row_idx, col_idx), (row_idx, col_idx + 1), (row_idx + 1, col_idx + 1))
                        )
                    else:
                        disp_face_indexes = (
                            ((row_idx + 1, col_idx), (row_idx, col_idx), (row_idx, col_idx + 1)),
                            ((row_idx + 1, col_idx), (row_idx, col_idx + 1), (row_idx + 1, col_idx + 1))
                        )
                    extend_face_vertices = [[disp_vertices[r][c] for r, c in idxs] for idxs in disp_face_indexes]
                    face_vertices.extend(extend_face_vertices)
                    face_loop_uvs.extend([disp_loop_uvs[r][c] for r, c in idxs] for idxs in disp_face_indexes)
                    face_loop_cols.extend([disp_loop_cols[r][c] for r, c in idxs] for idxs in disp_face_indexes)
                    original_face_normals.extend(side_planes[side_idx][1] for _ in disp_face_indexes)
#                    if self.import_overlays:
#                        self._side_face_vertices[side.id].extend(
#                            [side_vertice_lookup[v_i] for v_i in f_verts] for f_verts in extend_face_vertices
#                        )

            for row_idx in range(len(disp_vertices)):
                for col_idx in range(len(disp_vertices[row_idx])):
                    vert_idx = disp_vertices[row_idx][col_idx]
                    # apply displacement offset and normals + distances + elevation
                    vertices[vert_idx] += (Vector(side.dispinfo.offsets[row_idx][col_idx])
                                            + (Vector(side.dispinfo.normals[row_idx][col_idx])
                                                * side.dispinfo.distances[row_idx][col_idx])
                                            + side_planes[side_idx][1] * side.dispinfo.elevation)
#                    if self.import_overlays:
#                        self._side_vertices[side.id].append(vertices[vert_idx] + planes_center)

    center = _vertices_center(vertices)

    #mesh: bpy.types.Mesh = bpy.data.meshes.new(name)

    # blender can figure out the edges -- but you CANNOT haha
    #mesh.from_pydata([(v - center) * SCALE for v in vertices], (), face_vertices)
    print([(v - center) * SCALE for v in vertices], (), face_vertices)
    for material in materials:
        print("material used", material)
        #mesh.materials.append(material)
    pprint.pprint(locals(), indent=4, compact=False, sort_dicts=True)
    uv_layer: bpy.types.MeshUVLoopLayer = mesh.uv_layers.new()
    for polygon_idx, polygon in enumerate(mesh.polygons):
        polygon.material_index = face_materials[polygon_idx]
        for loop_ref_idx, loop_idx in enumerate(polygon.loop_indices):
            uv_layer.data[loop_idx].uv = face_loop_uvs[polygon_idx][loop_ref_idx]
    if is_displacement:
        vertex_colors: bpy.types.MeshLoopColorLayer = mesh.vertex_colors.new()
        for polygon_idx, polygon in enumerate(mesh.polygons):
            polygon.use_smooth = True
            for loop_ref_idx, loop_idx in enumerate(polygon.loop_indices):
                vertex_colors.data[loop_idx].color = face_loop_cols[polygon_idx][loop_ref_idx]
        # check if normals need to be flipped by comparing each displacement face normal to original plane normal
        if sum(original_face_normals[i].dot(p.normal) for i, p in enumerate(mesh.polygons)) < 0:
            mesh.flip_normals()
    # check if normals need to be flipped by comparing the first polygon normal to the plane normal
    elif side_planes[0][1].dot(mesh.polygons[0].normal) < 0:
        mesh.flip_normals()
    obj: bpy.types.Object = bpy.data.objects.new(name, object_data=mesh)
    #collection.objects.link(obj)
    obj.location = (planes_center + center) * SCALE

    
    print(obj)