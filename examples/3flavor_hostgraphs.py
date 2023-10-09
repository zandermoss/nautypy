#! /usr/bin/python3
"""examples/3flavor_hostgraphs.py
Using the same setup as examples/3flavor.py, we examine the 
canonization of a multigraph in greater detail. NAUTY is 
designed to work with vertex-colored simple graphs: 
graphs with no multi-edges, self-edges (loops), or edge colors.
To handle these cases (all of which appear in scattering diagrams),
we proceed in three steps.

1. Given a multigraph `mg` with c_v vertex colors and c_e edge colors,
    we embed `mg` in a simple, vertex-colored graph `g`, which
    we refer to as the "host graph". We assign a "vertex node" in `g`
    to each vertex in `mg`. We also assign an "edge node" in `g`
    to each *edge* in `mg`. Each edge node in `g` is connected to exactly
    two vertex nodes by colorless edges. Generally, there may be overlap
    between the vertex colors and edge colors of `mg`. To avoid mixing 
    up edge and vertex nodes, their attribute dictionaries are augmented
    with pairs `type:"vertex"` or `type:"edge"`, respectively. In effect, 
    we map the set of distinct vertex/edge colors in `mg` to a set of
    c_v + c_e vertex-node colors in `g`.
2. Call NAUTY to canonize the host graph.
3. Restrict both the automorphism generators and the canonical relabeling
    map returned from NAUTY to their actions on the set of vertex nodes, and
    construct the canonical isomorph of `mg` by applying the inverse of the
    restricted canonical map to relabel `mg`.

This example draws the host graph before and after canonization to illustrate
this process.
"""

import networkx as nx
import nautypy as nty
import matplotlib.pyplot as plt

#Construct example multigraph.
mg = nx.MultiGraph()

mg.add_node(0,color="red",ext=True)
mg.add_node(1,color="green",ext=True)
mg.add_node(2,color="red",ext=True)
mg.add_node(3,color="green",ext=True)
mg.add_node(4,color="black",ext=False)
mg.add_node(5,color="black",ext=False)
   
mg.add_edge(0,4,color="red")
mg.add_edge(1,4,color="green")
mg.add_edge(2,5,color="red")
mg.add_edge(3,5,color="green")
mg.add_edge(4,5,color="blue")
mg.add_edge(4,5,color="blue")

#Permute multigraph.
mg_perm = nx.relabel_nodes(mg,{0:0,1:1,2:2,3:3,4:5,5:4},copy=True)

#Canonicalize multigraphs, storing host graph data.
hostgraphs = dict()
mg_perm_canonical,mg_perm_autgens,mg_perm_canonical_map = nty.canonize_multigraph(mg_perm,
    color_sort_conditions = [('ext',True)], hostgraphs=hostgraphs) 
mg_perm_host = hostgraphs['host']
mg_perm_host_canonical = hostgraphs['host_canonical']

#Prettyprint graph data.
print("mg_perm")
nty.gprint(mg_perm)
print("mg_perm_host")
nty.gprint(mg_perm_host)
print("mg_perm_host_canonical")
nty.gprint(mg_perm_host_canonical)
print("mg_perm_canonical")
nty.gprint(mg_perm_canonical)

#Draw graphs.
def draw_diagram(_g,title=''):
    g = _g.copy()
    g.graph['node']={'shape':'circle'}
    for node in g.nodes:
        if g.nodes[node].get("ext", False) == True:
            g.nodes[node]["shape"] = "triangle"
        if g.nodes[node].get("type", "vertex") == "edge":
            g.nodes[node]["shape"] = "square"
    nty.gdraw(g,title=title)
    return

ax1 = plt.subplot(221)
draw_diagram(mg_perm,title="MultiGraph")

ax2 = plt.subplot(222)
draw_diagram(mg_perm_host,title="Host Graph")

ax3 = plt.subplot(223)
draw_diagram(mg_perm_host_canonical,title="Canonical Host Graph")

ax4 = plt.subplot(224)
draw_diagram(mg_perm_canonical,title="Canonical MultiGraph")

plt.show()
