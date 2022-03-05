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
    def dest(self) -> 'Optional[half_edge]':
        if self.next is not None:
            return self.next.origin
    
    @property
    def previous(self):
        return self.opposite.next.opposite
    
    def __iter__(self):
        edge = self
        # yield self and all next edges until we reach ourselves
        while edge is not None:
            yield edge
            edge = edge.next
            if edge is self:
                break

    def __repr__(self):
        return f"({getattr(self.origin, 'idx', 'N')}, {self.incident_face.idx}, {getattr(self.dest, 'idx', 'N')})"
    @property
    def loop_count(self):
        return len([*self.__iter__()])

class DCEL:
    FINF = face(-1)
    def __init__(self):
        self.edgeList: list[half_edge] = []
        """Contains one half_edge for each loop"""
    
    def __repr__(self):
        return f"<DCEL {self.vert_count} nodes {self.edge_count} edges {self.face_count} faces>"

    @property
    def face_count(self):
        if not self.edgeList:
            return 0
        return len(self.edgeList)-1

    @property
    def edge_count(self):
        return sum([len([h for h in loop]) for loop in self.edgeList])//2

    @property
    def vert_count(self):
        v = set()
        for loop in self.edgeList:
            for half_edge in loop:
                v.add(half_edge.origin.idx)
        return len(v)

    def add_edge(self, edge: tuple, positions:'list[coord3d]') -> 'tuple[half_edge]':
        left = half_edge(vertex(edge[0]))
        right = half_edge(vertex(edge[1]))
        if not self.edges:
            self.edges += [left, right]
        else:
            self.edges += [right, left]

        return left, right

    def add_half(self, half: half_edge):
        if self.face_count == 0: # adding first inner edge
            if self.face_count == half.incident_face.idx:
                self.edgeList = [half,None]
            elif half.incident_face.idx == -1:
                self.edgeList = [None,half]
            else:
                raise ValueError("First edge added to a DCEL should belong to the first face.")
        elif self.face_count < half.incident_face.idx+1:
            if self.face_count == half.incident_face.idx:
                self.edgeList.insert(half.incident_face.idx, half)
            else:
                raise ValueError("Edge is too disconnected. Add edges from a closer face first.")
        elif self.edgeList[half.incident_face.idx] == None:
            self.edgeList[half.incident_face.idx] = half

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

            print([[a for a in asd] for asd in self.edgeList])

        firstLeftEdge, firstRightEdge = self.edgeList[0], self.edgeList[1]
        prevLeftEdge.next = firstLeftEdge
        #prevRightEdge.next = firstRightEdge
        #firstLeftEdge.next = prevLeftEdge
        firstRightEdge.next = prevRightEdge
        print([[a for a in asd] for asd in self.edgeList], '1-final')
        prevRightEdge.origin = firstLeftEdge.origin
        print([[a for a in asd] for asd in self.edgeList], 'final')
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
        for right_edge in self.edgeList[1]:
            assert (right_edge.incident_face == self.FINF), "Already a face?, %s" % right_edge
            for other_right_edge in face_dcel.edgeList[1]:
                if other_right_edge.dest.idx == right_edge.origin.idx:
                    #print(f"True {self.edges.index(right_edge)}th with {face_dcel.edges.index(other_right_edge)}th")
                    print("Splittin and joining")
                    print(right_edge, other_right_edge)
                    
                    # outer loop (FINF)
                    if self.edgeList[-1] == right_edge:
                        self.edgeList[-1] = self.edgeList[-1].next
                    right_edge.previous .next = other_right_edge.next
                    other_right_edge.previous .next = right_edge.next

                    # inner loop (face+1)
                    right_edge .next = other_right_edge.opposite.next
                    other_right_edge.next.opposite .next = right_edge

                    print(right_edge, right_edge.next, right_edge.next.next)
                    for new_loop_edge in right_edge:
                        new_loop_edge.incident_face = f
                        self.add_half(new_loop_edge)
                    print(right_edge, right_edge.next, right_edge.next.next)
                    #self.edges = 
                    [(0, 1), (1, 0), (2, 3), (3, 2), (0, 2), (2, 0), (3, 1), (1, 3)]
                    [(0, 1), (1, 0), (2, 3), (3, 2), (0, 2), (2, 0), (3, 1), (1, 3), (2, 1), (1, 2)]

                    [0,-1,-1, 0,-1, 0,-1, 0]
                    [1,-1,-1, 0,-1, 1,-1, 0, 0, 1]
        
            return

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
        [4, 5, 7, 6],
        [0, 1, 5, 4],
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
e = pydata2()
print(e)
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