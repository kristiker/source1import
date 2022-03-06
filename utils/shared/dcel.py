from typing import Optional
import igraph

# https://en.wikipedia.org/wiki/Doubly_connected_edge_list

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


class DCEL:
    """Doubly connected edge list (strong directed graph)"""
    FINF = face(-1)
    def __init__(self):
        self.faces: list[half_edge] = []
        self.holes: list[half_edge] = []
        """Contains one half_edge for each loop"""
    
    def __repr__(self):
        return f"<DCEL {self.vert_count} nodes {self.edge_count} edges {self.face_count} faces>"

    @property
    def face_count(self): return len(self.faces)
    @property
    def hole_count(self): return len(self.holes)

    @property
    def edge_count(self):
        return sum([len([h for h in loop]) for loop in self.faces] + [len([h for h in loop]) for loop in self.holes])//2

    @property
    def vert_count(self):
        v = set()
        for loop in self.faces:
            for half_edge in loop:
                v.add(half_edge.origin.idx)
        return len(v)

    def add_half(self, half: half_edge):
        if half.incident_face.idx < 0:
            actual_index = ((1 + half.incident_face.idx) * -1)
            count = self.hole_count
            lst = self.holes
        else:
            actual_index = half.incident_face.idx
            count = self.face_count
            lst = self.faces

        if count <= actual_index:
            if count == actual_index:
                lst.append(half)
            else:
                raise ValueError("Edge is too disconnected. Add edges from a closer face first.")
            #else:
            #    lst[actual_index] = half

    @classmethod
    def new_face(cls, vertices, face_verts):
        self = cls()
        f = face(0)
        #self.face_count+=1
        prevLeftEdge = None
        prevRightEdge = None
        for vert_idx in face_verts:
            v = vertex(idx=vert_idx, position=vertices[vert_idx])
            left, right = half_edge(), half_edge()
            left.incident_face = f
            left.next = None
            left.origin = v
            left.opposite = right
            right.incident_face = self.FINF
            right.next = prevRightEdge
            right.origin = None
            right.opposite = left

            self.add_half(left)
            self.add_half(right)
            if prevLeftEdge is not None:
                prevLeftEdge.next = left
            if prevRightEdge is not None:
                prevRightEdge.origin = v
            
            prevLeftEdge = left
            prevRightEdge = right


        firstLeftEdge, firstRightEdge = self.faces[0], self.holes[0]
        prevLeftEdge.next = firstLeftEdge
        #prevRightEdge.next = firstRightEdge
        #firstLeftEdge.next = prevLeftEdge
        firstRightEdge.next = prevRightEdge
        prevRightEdge.origin = firstLeftEdge.origin
        return self

    @classmethod
    def from_pydata(cls, vertices: 'list[coord3d]', faces: 'list[list[int]]'):
        ...
        #g = igraph.Graph(directed=True)
        #print("(0, 6) (6, 0) (6, 2) (2, 6) (2, 3) (3, 2) (5, 7) (7, 5) (5, 4) (4, 5) (4, 1) (1, 4) (1, 7) (7, 1) (0, 4) (4, 0) (6, 5) (5, 6) (2, 7) (7, 2) (0, 3) (3, 0) (3, 1) (1, 3)")
        #g.add_edge()
        #nwise_longest = lambda g, *, n=2, fv=object(): zip_longest(*(islice(g, i, None) for i, g in enumerate(tee(g, n))), fillvalue=fv)
        #verts = []
        print("Building face 0")
        self = cls.new_face(vertices, faces.pop(0))

        for face_verts in faces:
            face_dcel = cls.new_face(vertices, face_verts)
            self.join_face(face_dcel)

            #self.verify()
    
        return self

    def join_face(self, face_dcel: 'DCEL'):
        f = face(self.face_count)
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
                    self.add_half(self.holes.pop(0))
                    bFullLoop=True
                    break
                print("Splittin and joining")
                
                outer_complement_path = other_path.circuit_complement
                print(f"Path: {[e for e in path]}, started at: {right_edge}")
                print(f"Othr: {[e for e in other_path]}, started at: {other_right_edge}")
                print(f"Cplm: {[e for e in outer_complement_path]}")

                # outer loop (FINF)
                if self.holes[0] in path:
                    self.holes[0] = outer_complement_path.start
    
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
                    self.add_half(new_loop_edge)
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
            # if outer faces a hole
            if outer.incident_face.idx == self.holes[-1].incident_face.idx:
                print("TRUEEEEEEEE", outer)
                # skip if already part of existing hole
                if outer in self.holes[-1]:
                    print("Continue")
                    continue
                # for each next edge from this outer
                f = face(-(self.hole_count+1))
                for outer in outer:
                    outer.incident_face = f
                self.add_half(outer)
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
    return DCEL.from_pydata(
        [coord3d(-3.5, -3.5, 0),
        coord3d(3.5, -3.5, 0),
        coord3d(-3.5, 3.5, 0),
        coord3d(3.5, 3.5, 0),],
        [[0, 3, 1],
        [0, 2, 3]]
)
pydata2()
e = pydata()
print(e)
if __name__ == '__main__':
    import unittest
    @dataclass
    class Polygon:
        coords: 'list[coord3d]'
        verts: 'list[int]'
        expected_edges: int
        expected_faces: int
        expected_verts: int
        expected_holes: int
    class Test_DCEL(unittest.TestCase):
        triangle=Polygon(
            coords=[coord3d(-3, -3, 0), coord3d(3, -3, 0), coord3d(-3, 3, 0)],
            verts=[[0,1,2]],
            expected_edges=3,
            expected_faces=1,
            expected_verts=3,
            expected_holes=1,
        )
        quad=Polygon(
            coords=[coord3d(-3.5, -3.5, 0),coord3d(3.5, -3.5, 0),coord3d(-3.5, 3.5, 0),coord3d(3.5, 3.5, 0)],
            verts=[[0, 1, 3, 2]],
            expected_edges=4,
            expected_faces=1,
            expected_verts=4,
            expected_holes=1,
        )
        splitquad=Polygon(
            coords=[coord3d(-3.5, -3.5, 0),coord3d(3.5, -3.5, 0),coord3d(-3.5, 3.5, 0),coord3d(3.5, 3.5, 0)],
            verts=[[0, 3, 1],[0, 2, 3]],
            expected_edges=5,
            expected_faces=2,
            expected_verts=4,
            expected_holes=1,
        )
        block=Polygon(
            coords=
                [coord3d(-512.0, 512.0, 256.0),
                coord3d(-512.0, -512.0, 256.0),
                coord3d(512.0, 512.0, 256.0),
                coord3d(512.0, -512.0, 256.0),
                coord3d(-512.0, 512.0, -256.0),
                coord3d(-512.0, -512.0, -256.0),
                coord3d(512.0, 512.0, -256.0),
                coord3d(512.0, -512.0, -256.0)],
            verts=
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

        def common2d(self, p: Polygon):
            d = DCEL.from_pydata(
                p.coords,
                p.verts.copy()
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

            self.assertEqual([point.origin.idx for point in inner_path], p.verts[0])

            if d.hole_count:
                for i, outer_half_edge in enumerate(d.holes[0]):
                    self.assertLess(i, p.expected_edges, f"More than {p.expected_edges} outer edges")
                    self.assertEqual(outer_half_edge.incident_face.idx, -1)

            # test DCEL.add_half logic
            # adding edge too disconnected from our list should raise ValueError
            self.assertRaises(ValueError, d.add_half, half_edge(d.faces[0].origin, incident_face=face(p.expected_faces+1)))

            return d

        def test_triangle(self):
            self.common2d(self.triangle)
        def test_quad(self):
            self.common2d(self.quad)
        def test_splitquad(self):
            self.common2d(self.splitquad)
        def test_block(self):
            self.common2d(self.block)
    unittest.main()

#quit()

g = igraph.Graph(edges=[(0,1), (1,2), (2,0)]).as_directed()

class DCEL2(igraph.Graph):
    @classmethod
    def FromVmeshEdges(cls, n, edgeVertex: list, edgeOpposite: list, edgeNext: list, edgeVertexData: list):
        g = igraph.Graph(directed=True)        
        starting_verts = [None] * len(edgeVertex)
        start = 0
        current = 0#edgeVertexData.index()
        last_vert = None
        while None in starting_verts:
            print(f"{current=}, {last_vert=}, {edgeVertex[current]=}")

            starting_verts[current] = last_vert
            if last_vert is not None and current == start:
                try:
                    current = start = starting_verts.index(None)
                    last_vert = None
                except ValueError:
                    break
                print("currenting a new one", current)
                continue
            starting_verts[edgeOpposite[current]] = edgeVertex[current]

            last_vert = edgeVertex[current]
            current = edgeNext[current]#edgeVertexData.index()
        if None in starting_verts:
            raise RuntimeError("Not all half-edges were travelled through: %r" % starting_verts)
        g.add_vertices(n)
        print(*zip(starting_verts, edgeVertex))
        g.add_edges([*zip(starting_verts, edgeVertex)])
        return g  

    @classmethod
    def FromVmesh2(cls, n, edgeVertex: list):
        g = igraph.Graph(directed=True)        
        edges = [None] * len(edgeVertex)
        for i, (end, start) in enumerate(zip_longest(*[iter(edgeVertex)]*2)):
            edges[2*i] = (start, end)
            edges[2*i+1] = (end, start)
        g.add_vertices(n)
        g.add_edges(edges)
        return g
    def __init2__(self, edge_list=[(0,1), (1,2), (2,0)]) -> None:
        g = igraph.Graph(edges=edge_list)
        if g.ecount() < 3:
            raise ValueError("Need at least 3 edges.")
        if g.vcount() < 3:
             raise ValueError("Need at least 3 vertices.")
        g: igraph.Graph = g.as_directed()
        # igraph: (+,+,+,-,-,-)
        # here: (+,-,+,-,+,-)
        # vmap?: (+,-,-,+,-,+)
        for edge in range(len(edge_list)):
            h1 = half_edge(*g.es[edge].tuple)
            h2 = half_edge(*g.es[edge+len(edge_list)].tuple)
            h1.opposite = h2
            h2.opposite = h1
            half_edges.append(h1)
            half_edges.append(h2)

    def plot(self):
        layout = [[0,0], [0,1], [1,1], [1,0], ]
        color_dict = {"clockwise": "green", "counter-clockwise": "red"}
        igraph.plot(self, layout=layout,
        vertex_color='cyan',
        vertex_shape='rectangle',
        vertex_size=14,
        vertex_label = self.vertexData,
        edge_color=["green", "green", "green", "green", "red", "red", "red", "red"],#[color_dict[clockrot] for clockrot in self.es["rotation"]],
        #edge_label= self.edgeVertexData,
        edge_curved=0.001,
        edge_arrow_size=2,
        edge_arrow_width=1,
        edge_width=4,)


#DCEL.FromVmeshEdges(3, [1, 0, 1, 2, 2, 0], [1, 0, 3, 2, 5, 4], [3, 4, 1, 5, 2, 0], [0,1,2,3,4,5])
#quit()

layout = [[0,0], [0,1], [1,1], [1,0], ]
color_dict = {"clockwise": "green", "counter-clockwise": "red"}
igraph.plot(
    #DCEL.FromVmeshEdges(8,
    #    [6, 0, 2, 6, 3, 2, 7, 5, 4, 5, 1, 4, 7, 1, 4, 0, 5, 6, 7, 2, 3, 0, 1, 3],
    #    [1, 0, 3, 2, 5, 4, 7, 6, 9, 8,11,10,13,12,15,14,17,16,19,18,21,20,23,22],
    #    [2,14, 4,16,21,18,19, 8,10,17,12,15, 7,23, 9,20, 6, 1,13, 3,22, 0,11, 5],
    #    [23,1,4,2,15,3,17,19,12,5,8,6,16,7,0,14,11,18,20,10,13,21,9,22]),
    #DCEL.FromVmeshEdges(3, [1, 0, 1, 2, 2, 0], [1, 0, 3, 2, 5, 4], [3, 4, 1, 5, 2, 0], [0,1,2,3,4,5]),
    DCEL.FromVmesh2(4, [1,0,3,2,2,0,1,3,1,2]),
    #DCEL2.FromVmesh2(4, [1,0,3,2,2,0,1,3]),
layout=[[0,1], [0,0], [1,1], [1,0], ],
vertex_color='cyan',
vertex_shape='rectangle',
vertex_size=14,
vertex_label = [0, 1, 2, 3],
#edge_color=["green", "red", "red", "green", "red", "green", "red", "green"],
#edge_label= self.edgeVertexData,
edge_curved=0.001,
edge_arrow_size=2,
edge_arrow_width=1,
edge_width=4,)