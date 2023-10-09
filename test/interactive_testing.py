#! /usr/bin/python3
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stat
import nautypy as nty
from time import time
from random_graphs import random_multigraph, randomize_colors, random_isomorph,recolor_random_vertex, recolor_random_edge
from comparison import colstate, compare

""" Interactive/visual testing for nautypy.

Multigraphs are randomly generated and colored.
Then, three variants of each multigraph are produced.
The first randomly permutes node labels.
The second randomly recolors a node (color may be stabilized).
The third randomly recolors an edge (color may be stabilized).
Both VF2 and nautypy are then called to determine whether the
multigraph is isomorphic to each of these variants in turn, 
and if so, to produce a relabeling map realizing the isomorphism.
For each multigraph and variant, we are essentially looking for
agreement between VF2 and nautypy. The meat of the test is the
``compare`` function, and details are provided there.

To advance to the next graph, simply close the matplotlib window
from the previous graph.
"""

#==========[Options/Parameters]==========#
#Print test details?
verbose = True 
#Draw graphs?
draw = True
#Use a fixed random seed, or use system time?
fixed_seed = False
#Number of multigraphs to generate and test.
ngraphs = 10
#Number of vertices
nv=5
#Number of loops
nloops = 10
#Edge/vertex colors
colors = ['red','green','blue']
#colors = ['red','orange','green','blue','indigo','violet']
#colors = ['black']
#=========================================#

#Initialize np.random RNG.
if fixed_seed:
    seed = 12345
else:
    seed = int(str(time()).replace('.',''))
rng = np.random.default_rng(seed)
#Exponential distribution for child multiplicity of spanning tree.
tree_rv = stat.expon(loc=0,scale=1)
tree_rv.random_state = rng


for i in range(ngraphs):
    if verbose:
        print(f'\n\n================================================================')
        print(f'=======================[Graph {i} of {ngraphs}]=========================')
        print(f'================================================================')
    #Generate random multigraph
    mg = random_multigraph(nv,tree_rv,nloops,rng)
    #Randomly color edges and vertices of the multigraph.
    randomize_colors(mg,colors,rng)
    #Generate a random isomorph of the multigraph.
    if verbose:
        print('\n----------RANDOM PERMUTATION----------')
    mg_perm,label_map = random_isomorph(mg,rng)
    pstate, data, perm_graphs = compare(mg,mg_perm,verbose=verbose)
    if verbose:
        print("************************")
        print(f'PERM PASS?    {colstate(pstate)}')
        print("************************")
        print('\n----------RANDOM VERTEX RECOLORING----------')
    v_mg = nx.MultiGraph(mg)
    recolor_random_vertex(v_mg,colors,rng)
    vstate, data, vert_graphs = compare(mg,v_mg,verbose=verbose)
    if verbose:
        print("************************")
        print(f'VERT PASS?    {colstate(vstate)}')
        print("************************")
        print('\n----------RANDOM EDGE RECOLORING----------')
    e_mg = nx.MultiGraph(mg)
    recolor_random_edge(e_mg,colors,rng)
    estate, data, edge_graphs = compare(mg,e_mg,verbose=verbose)
    if verbose:
        print("************************")
        print(f'EDGE PASS?    {colstate(estate)}')
        print("************************")
    if draw:
        subax1 = plt.subplot(221)
        nty.gdraw(mg, title = "Random MultiGraph")
        subax2 = plt.subplot(222)
        nty.gdraw(mg_perm, title = "Random Permutation")
        subax3 = plt.subplot(223)
        nty.gdraw(v_mg, title = "Vertex Recoloring")
        subax4 = plt.subplot(224)
        nty.gdraw(e_mg, title = "Edge Recoloring")
        #nty.gdraw(mg,title=f"MultiGraph {i} of {ngraphs}")
        plt.show()
