
from itertools import zip_longest
from typing import Optional
import igraph

# https://en.wikipedia.org/wiki/Doubly_connected_edge_list

from dataclassy import dataclass

@dataclass
class vertex:
    idx: int
    x: float
    y: float

@dataclass
class half_edge:
    start: vertex
    end: vertex
    opposite: 'half_edge' = None

@dataclass
class face:
    idx: int = -1


g = igraph.Graph(edges=[(0,1), (1,2), (2,0)]).as_directed()

class DCEL(igraph.Graph):
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
    DCEL.FromVmeshEdges(8,
        [6, 0, 2, 6, 3, 2, 7, 5, 4, 5, 1, 4, 7, 1, 4, 0, 5, 6, 7, 2, 3, 0, 1, 3],
        [1, 0, 3, 2, 5, 4, 7, 6, 9, 8,11,10,13,12,15,14,17,16,19,18,21,20,23,22],
        [2,14, 4,16,21,18,19, 8,10,17,12,15, 7,23, 9,20, 6, 1,13, 3,22, 0,11, 5],
        [23,1,4,2,15,3,17,19,12,5,8,6,16,7,0,14,11,18,20,10,13,21,9,22]),
#layout=layout,
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