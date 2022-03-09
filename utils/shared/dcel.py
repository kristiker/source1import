from functools import cached_property, lru_cache
from typing import Optional
from array import array
# https://en.wikipedia.org/wiki/Doubly_connected_edge_list

import openmesh as om
from dataclassy import dataclass, factory

@dataclass
class coord3d:
    x: float = 0
    y: float = 0
    z: float = 0

@dataclass
class vertex:
    idx: int
    position: coord3d

@dataclass
class face:
    idx: int = -1

@dataclass
class half_edge:
    origin: vertex = None
    next: 'half_edge' = None
    opposite: 'half_edge' = None
    incident_face: face = factory(face)

    @property
    def dest(self) -> 'Optional[vertex]':
        if self.next is not None:
            return self.next.origin
    
    @property
    def previous(self):
        prev = self.opposite.next.opposite
        # rotate around the vertex CCW for halves that enter it (may be more than 2).
        while prev.next is not self:
            prev = prev.next.opposite
        return prev
    
    def __iter__(self):
        edge = self
        # yield self and all next edges until we reach ourselves
        while edge is not None:
            yield edge
            edge = edge.next
            if edge is self:
                break

    def distance_to(self, other: 'half_edge'):
        for i, e in enumerate(self):
            if other is e:
                break
        return i
            
    def __repr__(self):
        if self.incident_face.idx > -1:
            face_id = str(self.incident_face.idx)# chr(0x278a + (self.incident_face.idx))#
        else:
            face_id = chr(0x277f + (self.incident_face.idx*-1))
        return f"{face_id}({getattr(self.origin, 'idx', 'N')}, {getattr(self.dest, 'idx', 'N')})"

    @property
    def loop_count(self):
        return len([*self.__iter__()])
    @property
    def loop_path(self):
        return Path(self, self.previous)

@dataclass
class Path:
    start: half_edge
    finish: half_edge

    def __repr__(self):
        return "-->".join(str(e.origin.idx) for e in self)
    #__contains__ = 5
    def __iter__(self):
        for edge in self.start:
            yield edge
            if edge is self.finish:
                break
    
    def __len__(self):
        return self.start.distance_to(self.finish)+1
    
    @property
    def circuit_complement(self):
        return self.__class__(self.finish.next, self.start.previous)
        #for edge in self.finish:
        #    if edge is self.start:
        #        break
        #    yield edge

    @property
    def is_loop(self):
        return self.finish.next is self.start 

@dataclass
class Polytope:
    vertex_arrangement: 'list[coord3d]'
    faces: 'list[int]'

# https://observablehq.com/@2talltim/mesh-data-structures-traversal#cell-129
class DCEL:
    """Doubly connected edge list (strong directed graph)"""
    FINF = face(-1)
    def __init__(self):
        #self.vertexEdgeIndices = array('i')
        self.vertexPositions = []
        "Positions of each vertex"
        self.vertexDataIndices = array('i')
        "Vertices"

        self.edgeVertexIndices = array('i')
        "Origin vertex of each edge"
        self.edgeOppositeIndices = array('i')
        "Opposite/Twin of each edge"
        self.edgeNextIndices = array('i')
        "Next of each edge"
        self.edgeFaceIndices = array('i')
        "Incident face of each edge"
        self.edgeVertexDataIndices = array('i')
        "Edges"
        self.faceEdgeIndices = array('i')
        "Incident edge of each face"
        self.faceDataIndices = array('i')
        "Faces"

    @lru_cache
    def get(self, index: int)-> half_edge:
        "Get half_edge() at this index"
        print(self.vertexDataIndices, self.edgeVertexIndices, index)
        return half_edge(
            origin=vertex(self.vertexDataIndices[
                self.edgeVertexIndices[index]],
            self.vertexPositions[self.edgeVertexIndices[index]]),
            next=self.get(self.edgeNextIndices[index]),
            opposite=self.get(self.edgeOppositeIndices[index]),
            incident_face=self.edgeFaceIndices[index],
        )

    def get_index(self, half: half_edge)-> int:
        return self.edgeVertexIndices.index(half.origin.idx)

    @property
    def faces(self):
        "Representative hedge for each face"
        return [self.get(index) for index in self.faceDataIndices]
        
    @property
    def holes(self):
        "Representative edge for each hole (1-dimensional boundary)"
        rv = []
        for i, edge_idx in enumerate(self.edgeFaceIndices):
            if edge_idx == -1:
                rv.append(i)
        return rv

    def __repr__(self):
        return f"<DCEL {self.vert_count} nodes {self.edge_count} edges {self.face_count} faces>"

    @property
    def face_count(self): return len(self.faces)
    @property
    def hole_count(self): return len(self.holes)

    @property
    def half_edge_count(self):
        return len(self.edgeVertexIndices)

    @property
    def edge_count(self):
        return len(self.edgeNextIndices)//2

    @property
    def edge_count_old(self):
        return sum([len([h for h in loop]) for loop in self.faces] + len(self.holes))//2

    @property
    def vert_count(self):
        v = set()
        for loop in self.faces:
            for half_edge in loop:
                v.add(half_edge.origin.idx)
        return len(v)
    
    @property
    def edgeList(self):
        face0 = self.faces[0]
        face0_path = Path(face0, face0.previous)#Path(face0.previous, face0.previous.previous)
        rv = []#array('i')
        for half in face0_path:
            rv.append(half)
            rv.append(half.opposite)
        
        return rv

    def verify(self):
        assert self.vert_count-self.edge_count+(self.face_count+self.hole_count) == 2

    def getMeshHoles(self):
        ...
    def isHomeomorphicTo(self, other):
        ...
#    @property
#    def edgeVertexIndices(self):
#    
    def add_face(self, face_verts):
        self.faceDataIndices.append(0)
        prevRight: Optional[int] = -1
        prevLeft: Optional[int] = -1
        for right, vert_idx in enumerate(face_verts):
            left = right+1
            self.edgeFaceIndices.append(0)
            self.edgeFaceIndices.append(-1)

            self.edgeNextIndices.append(-1)
            self.edgeNextIndices.append(prevLeft)

            self.edgeVertexIndices.append(vert_idx)
            self.edgeVertexIndices.append(-1)

            self.edgeOppositeIndices.append(left)
            self.edgeOppositeIndices.append(right)

            if prevRight != -1:
                self.edgeNextIndices[prevRight] = right
            if prevLeft != -1:
                self.edgeVertexIndices[prevLeft] = vert_idx
            
            prevRight = right
            prevLeft = left

            #print([[a for a in asd] for asd in self.edgeList])

        self.edgeNextIndices[prevRight] = 0
        self.edgeNextIndices[prevLeft] = 1
        #print([[a for a in asd] for asd in self.edgeList], '1-final')
        self.edgeVertexIndices[prevLeft] = self.edgeVertexIndices[0]

    @classmethod
    def from_pydata(cls, vertices: 'list[coord3d]', faces: 'list[list[int]]'):
        ...
        #g = igraph.Graph(directed=True)
        #print("(0, 6) (6, 0) (6, 2) (2, 6) (2, 3) (3, 2) (5, 7) (7, 5) (5, 4) (4, 5) (4, 1) (1, 4) (1, 7) (7, 1) (0, 4) (4, 0) (6, 5) (5, 6) (2, 7) (7, 2) (0, 3) (3, 0) (3, 1) (1, 3)")
        #g.add_edge()
        #nwise_longest = lambda g, *, n=2, fv=object(): zip_longest(*(islice(g, i, None) for i, g in enumerate(tee(g, n))), fillvalue=fv)
        #verts = []
        print("Building face 0")
        self = cls()
        self.vertexPositions.extend(vertices)
        self.vertexDataIndices.extend([range(max(max(v) for v in fv) for fv in faces)])
        self.add_face(vertices, faces.pop(0))
        print("Main Inner:", [asd for asd in self.faces[0]])

        for face_verts in faces:
            face_dcel = cls.new_face(vertices, face_verts)
            self.join_face(face_dcel)

            #self.verify()
    
        return self

    # https://en.wikipedia.org/wiki/Manifold#Gluing_along_boundaries
    def join_face(self, face_dcel: 'DCEL'):
        """Join a face by gluing along common boundaries"""
        f = self.face_count
        self.faceDataIndices.append(f)
        print("Joining face", self.face_count)
        bMatchedOnce = False
        bFullLoop = False
        existing_outers = [*iter(self.holes[0])]
        new_outers = [*iter(face_dcel.holes[0])]
        for right_edge in existing_outers:

            #assert (right_edge.incident_face == self.FINF), "Already a face?, %s" % right_edge
            for other_right_edge in new_outers:
                if (other_right_edge.dest.idx != right_edge.origin.idx
                    or right_edge.dest.idx != other_right_edge.origin.idx
                    ):
                    continue
                #    # matched and attached once, but matched again with a different path
                #    self.form_hole(f.idx)
                #    break
                #bMatchedOnce=True

                print("True, there is a match", self.holes[0].distance_to(right_edge), "with", face_dcel.holes[0].distance_to(other_right_edge))
                print(right_edge, "with", other_right_edge)
                # See if there is more
                path = Path(start=right_edge, finish=right_edge)                   # start [ 5 --> (1 --> 0) --> 4]finish
                other_path = Path(start=other_right_edge, finish=other_right_edge) # finish[ 5 <-- (1 <-- 0) <-- 4] start
                # walk back
                while other_path.start.previous.origin.idx == path.finish.next.dest.idx and not path.is_loop:
                    print("Walk back 1", other_path.start.previous)
                    path.finish = path.finish.next
                    other_path.start = other_path.start.previous
                # walk forward
                while other_path.finish.next.dest.idx == path.start.previous.origin.idx and not path.is_loop:
                    print("Walk forward 1",  other_path.finish.next)
                    path.start = path.start.previous
                    other_path.finish = other_path.finish.next
                
                #if len(path) == 4 == self.holes[0].loop_count:
                #    assert path.is_loop, path
                if path.is_loop:
                    print("Path is full loop, filling with face", f)
                    for edge in path:
                        edge.incident_face = f
                    self.faceEdgeIndices.append(self.get_index(path.start))
                    bFullLoop=True
                    break
                print("Splittin and joining")
                
                outer_complement_path = other_path.circuit_complement
                print(f"Path: {[e for e in path]}, started at: {right_edge}")
                print(f"Othr: {[e for e in other_path]}, started at: {other_right_edge}")
                print(f"Cplm: {[e for e in outer_complement_path]}")

                # outer loop (FINF)
                #if self.holes[0] in path:
                #    self.holes[0] = outer_complement_path.start
    
                # join end of existing outer loop with start of other outer loop
                # path.start.previous == cplm.finish
                path.start.previous .next = outer_complement_path.start
    
                # join end of other outer loop with start of existing outer loop
                # path.finish.next == cplm.start
                outer_complement_path.finish.next = path.finish.next

                #other_right_edge.previous .next = right_edge.next
                print("Outer face edges:", outer_complement_path.start.loop_count)
                #if outer_complement_path.start.loop_count == 4:
                #    self.bMatched = True
                
                # inner loop (face+1)
                # join end of other inner loop with start of existing inner loop
                outer_complement_path.start.opposite .next = path.start
                # join end of existing inner loop with start of other inner loop
                # 
                path.finish.next = outer_complement_path.finish.opposite

                #right_edge .next = other_right_edge.opposite.next
                #other_right_edge.next.opposite .next = right_edge
                print(f"New face edges: {path.start.loop_count} ({len(path)}+{len(outer_complement_path)})")

                if bMatchedOnce:
                    # matched and attached once, but matched again with a different path
                    self.detect_holes()
                for new_loop_edge in path.start:
                    new_loop_edge.incident_face = f
                self.faceEdgeIndices.append(self.get_index(path.start))
                print("Face count", self.face_count)
                print("Hole count", self.hole_count)

                bMatchedOnce=True

                [(0, 1), (1, 0), (2, 3), (3, 2), (0, 2), (2, 0), (3, 1), (1, 3)]
                [(0, 1), (1, 0), (2, 3), (3, 2), (0, 2), (2, 0), (3, 1), (1, 3), (2, 1), (1, 2)]
                [0,-1,-1, 0,-1, 0,-1, 0]
                [1,-1,-1, 0,-1, 1,-1, 0, 0, 1]
            if bFullLoop:
                break
        #assert self.face_count == f.idx+1, ([*self.edgeList[-1]], [*face_dcel.edgeList[-1]])
        return
    
    def detect_holes(self):
        print("~~~~Detecting Holes")
        for inner_edge in self.faces[-1]: # last face
            outer = inner_edge.opposite
            # if outer half-edge is a boundary (makes a hole)
            if outer.incident_face.idx == self.holes[-1].incident_face.idx:
                print("TRUEEEEEEEE", outer)
                # skip if already part of existing hole
                if outer in self.holes[-1]:
                    print("Continue")
                    continue
                # for each next edge from this outer
                f = face(-(self.hole_count+1))
                self.faceEdgeIndices.append(self.get_index(outer))
                for outer in outer:
                    outer.incident_face = f
                print("Detected hole", f, "from edge", outer)

def triangle() -> 'list[half_edge]':
    rv = []
    rv.append(half_edge(origin=vertex(0, coord3d(0,0,0))))
    rv.append(half_edge(origin=vertex(0, coord3d(1,0,0)), next=rv[-1]))
    rv.append(half_edge(origin=vertex(0, coord3d(0,1,0)), next=rv[-1]))
    rv[0].next = rv[-1]
    print(f"1 Face with {rv[0].loop_count} edges")
    return rv

def pydata():
    """M.G.
            4---------------5
           /|              /|
          / |    /1/      / |
         /  |            /  |
        0---+------|2|--1   |
        |   |           |   |
        |~4 |           |~5 |
        |   |           |   |
        |   6---|0|-----+---7
        |  /            |  /
        | /     /3/     | /
        |/              |/
        2---------------3
    """
    return DCEL.from_pydata(
        [coord3d(-512.0, 512.0, 256.0),
        coord3d(-512.0, -512.0, 256.0),
        coord3d(512.0, 512.0, 256.0),
        coord3d(512.0, -512.0, 256.0),
        coord3d(-512.0, 512.0, -256.0),
        coord3d(-512.0, -512.0, -256.0),
        coord3d(512.0, 512.0, -256.0),
        coord3d(512.0, -512.0, -256.0)],
        [[0, 2, 3, 1],
        [0, 1, 5, 4],
        [4, 5, 7, 6],
        [2, 6, 7, 3],
        [0, 4, 6, 2],
        [1, 3, 7, 5]]
)
def pydata2():
    """
        2-------3
        | [1] / |
        |   /   |
        | / [0] |
        0-------1
    """
    return DCEL.from_pydata(
        [coord3d(-3.5, -3.5, 0),
        coord3d(-3.5, 3.5, 0),
        coord3d(3.5, -3.5, 0),
        coord3d(3.5, 3.5, 0),],
        [[0, 1, 3],
        [0, 3, 2]]
)
def pydata3():
    """
        2--------3
        | \  [1] |
        |   \    |
        | [0] \  |
        0--------1
    """
    return DCEL.from_pydata(
        [coord3d(-3.5, -3.5, 0),
        coord3d(-3.5, 3.5, 0),
        coord3d(3.5, -3.5, 0),
        coord3d(3.5, 3.5, 0),],
        [[0, 1, 2],
        [1, 3, 2]]
)
e0 = DCEL.from_pydata(
    [coord3d(-3.5, -3.5, 0),
    coord3d(-3.5, 3.5, 0),
    coord3d(3.5, -3.5, 0),
    coord3d(3.5, 3.5, 0),],
    [[0, 2, 3, 1]]
)


m0 = om.PolyMesh()
# add a a couple of vertices to the mesh
vh0 = m0.add_vertex([-3.5, -3.5, 0])
vh1 = m0.add_vertex([-3.5, 3.5, 0])
vh2 = m0.add_vertex([3.5, -3.5, 0])
vh3 = m0.add_vertex([3.5, 3.5, 0])

# add a couple of faces to the mesh
fh0 = m0.add_face(vh0, vh2, vh3, vh1)

e3 = pydata()

e1 = pydata2()
e2 = pydata3()

assert repr(e0.edgeList) == '[0(0, 1), ➀(1, 0), ➀(2, 3), 0(3, 2), ➀(0, 2), 0(2, 0), ➀(3, 1), 0(1, 3)]'
assert repr(e2.edgeList) == '[1(0, 1), ➀(1, 0), ➀(2, 3), 0(3, 2), ➀(0, 2), 1(2, 0), ➀(3, 1), 0(1, 3), 0(2, 1), 1(1, 2)]'

#e = pydata()
#print(e)
from timeit import default_timer as timer
start = timer()
_print=print
print = lambda *s:...
for _ in range(1000):
    pydata()
end = timer()
print = _print
print("Time taken:", end-start)
quit()
    

if __name__ == '__main__':
    class TestPolytope(Polytope):
        expected_edges: int
        expected_faces: int
        expected_verts: int
        expected_holes: int
    import unittest    
    class Test_DCEL(unittest.TestCase):
        triangle=TestPolytope(
            vertex_arrangement=[coord3d(-3, -3, 0), coord3d(3, -3, 0), coord3d(-3, 3, 0)],
            faces=[[0,1,2]],
            expected_edges=3,
            expected_faces=1,
            expected_verts=3,
            expected_holes=1,
        )
        quad=TestPolytope(
            vertex_arrangement=[coord3d(-3.5, -3.5, 0),coord3d(3.5, -3.5, 0),coord3d(-3.5, 3.5, 0),coord3d(3.5, 3.5, 0)],
           faces=[[0, 1, 3, 2]],
            expected_edges=4,
            expected_faces=1,
            expected_verts=4,
            expected_holes=1,
        )
        splitquad=TestPolytope(
            vertex_arrangement=[coord3d(-3.5, -3.5, 0),coord3d(3.5, -3.5, 0),coord3d(-3.5, 3.5, 0),coord3d(3.5, 3.5, 0)],
           faces=[[0, 3, 1],[0, 2, 3]],
            expected_edges=5,
            expected_faces=2,
            expected_verts=4,
            expected_holes=1,
        )
        block=TestPolytope(
            vertex_arrangement=
                [coord3d(-512.0, 512.0, 256.0),
                coord3d(-512.0, -512.0, 256.0),
                coord3d(512.0, 512.0, 256.0),
                coord3d(512.0, -512.0, 256.0),
                coord3d(-512.0, 512.0, -256.0),
                coord3d(-512.0, -512.0, -256.0),
                coord3d(512.0, 512.0, -256.0),
                coord3d(512.0, -512.0, -256.0)],
           faces=
                [[0, 2, 3, 1],
                [0, 1, 5, 4],
                [4, 5, 7, 6],
                [2, 6, 7, 3],
                [0, 4, 6, 2],
                [1, 3, 7, 5]],
            expected_edges=12,
            expected_faces=6,
            expected_verts=8,
            expected_holes=0,
        )
        def test_default(self):
            d = DCEL()
            self.assertEqual(d.faces, [])
            self.assertEqual(d.edge_count, 0)
            self.assertEqual(d.face_count, 0)
            self.assertEqual(d.vert_count, 0)

        def common(self, p: TestPolytope):
            d = DCEL.from_pydata(
                p.vertex_arrangement,
                p.faces.copy()
            )
            self.assertEqual(d.edge_count, p.expected_edges)
            self.assertEqual(d.face_count, p.expected_faces)
            self.assertEqual(d.vert_count, p.expected_verts)
            self.assertEqual(d.hole_count, p.expected_holes)
            
            # verify data for each half edge
            for loop_edges in d.faces:
                previouses = []
                actuals = []
                nexts = []
                opposites = []
                for half in loop_edges:
                    previouses.append(half.previous)
                    actuals.append(half)
                    nexts.append(half.next)
                    opposites.append(half.opposite)
                
                halves_msg = f"\n\nprev:: {previouses}\n"+\
                    f"this:: {actuals}\n"+\
                    f"next:: {nexts}\n"+\
                    f"twin:: {opposites}\n"

                # check for Nones
                self.assertTrue(all(previouses), halves_msg)
                self.assertTrue(all(actuals), halves_msg)
                self.assertTrue(all(nexts), halves_msg)
                self.assertTrue(all(opposites), halves_msg)

                # check for correct .nexts and .opposites
                for i, half in enumerate(previouses):
                    self.assertIs(half, actuals[i-1], halves_msg)
                    self.assertIs(half, nexts[i-2], halves_msg)

            inner_path = Path(d.faces[0], d.faces[0])
            for i, inner_half_edge in enumerate(d.faces[0]):
                self.assertLess(i, p.expected_edges, f"More than {p.expected_edges} inner edges")
                self.assertEqual(inner_half_edge.incident_face.idx, 0)
                inner_path.finish = inner_half_edge

            # test path logic (provided h-edge.previous is correct)
            self.assertIs(d.faces[0].previous, inner_path.finish,
                msg=f"\n{[asd for asd in d.faces[0]]}\n{[asd.previous for asd in d.faces[0]]}\n{inner_path!r}")

            self.assertEqual([point.origin.idx for point in inner_path], p.faces[0])

            if d.hole_count:
                for i, outer_half_edge in enumerate(d.holes[0]):
                    self.assertLess(i, p.expected_edges, f"More than {p.expected_edges} outer edges")
                    self.assertEqual(outer_half_edge.incident_face.idx, -1)

            # test DCEL.add_half logic
            # adding edge too disconnected from our list should raise ValueError
            self.assertRaises(ValueError, d.add_half, half_edge(d.faces[0].origin, incident_face=face(p.expected_faces+1)))

            return d

        def test_triangle(self):
            self.common(self.triangle)
        def test_quad(self):
            self.common(self.quad)
        def test_splitquad(self):
            self.common(self.splitquad)
        def test_block(self):
            self.common(self.block)

    unittest.main()
