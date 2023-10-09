#! /usr/bin/python3
"""
A simple example from a toy Feynman diagram describing
scattering of two particles of flavor A (red) and two
particles of flavor B (green). The process is mediated
by states of flavor C (blue). Wick contractions produce
many copies of the same diagram which are equivalent 
up to a permutation of interaction vertices. When two 
contractions differ by a permutation of equivalent vertices,
they yield the same contribution to the scattering amplitude,
and give rise to the ``symmetry factors'' familiar from
scalar QFT. External leg vertices are denoted by triangles
of the same color as the leg. Interaction vertices are denoted
by black circles.

Here, we use nautypy to demonstrate the equivalence of two 
such contraction graphs by sending them to their canonical
isomorphs, the equality of which is trivially verified.
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

#Canonicalize multigraphs.
mg_canonical,mg_autgens,mg_canonical_map = nty.canonize_multigraph(mg) 
mg_perm_canonical,mg_perm_autgens,mg_perm_canonical_map = nty.canonize_multigraph(mg_perm) 

#Compare mg, mg_perm, mg_canonical, mg_perm_canonical.
print(f'mg Canonical Map: {mg_canonical_map}')
print(f'mg_perm Canonical Map: {mg_perm_canonical_map}\n')
print('Check inequality of mg, mg_perm and equality of mg_canonical, mg_perm_canonical')
print(f'(mg = mg_perm)? {nx.utils.graphs_equal(mg,mg_perm)}')
print(f'(mg_canonical = mg_perm_canonical)? {nx.utils.graphs_equal(mg_canonical,mg_perm_canonical)}\n')

#Prettyprint graph data.
print("MultiGraph")
nty.gprint(mg)
print("Permuted MultiGraph")
nty.gprint(mg_perm)
print("Canonical MultiGraph")
nty.gprint(mg_canonical)
print("Canonical Permuted MultiGraph")
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
draw_diagram(mg,title="MultiGraph")

ax2 = plt.subplot(222)
draw_diagram(mg_canonical,title="Canonical MultiGraph")

ax3 = plt.subplot(223)
draw_diagram(mg_perm,title="Permuted MultiGraph")

ax4 = plt.subplot(224)
draw_diagram(mg_perm_canonical,title="Canonical Permuted MultiGraph")

plt.show()
