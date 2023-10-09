#! /usr/bin/python3
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stat
import nautypy as nty
from time import time
from random_graphs import random_multigraph, randomize_colors, random_isomorph,recolor_random_vertex, recolor_random_edge
from comparison import colstate, compare
import pytest

"""
Testing setup and function defs for pytest.
To perform the same tests in an interactive environment, see ``interactive_test.py``.

For verbose output, invoke pytest with

    pytest -rA

"""

#==========[Options/Parameters]==========#
verbose = True 
fixed_seed = True
ngraphs = 100
#Number of vertices
nv=20
#Number of loops
nloops = 40
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

#Generate random multigraphs
random_multigraphs = []
for i in range(ngraphs):
    #Generate random multigraph
    mg = random_multigraph(nv,tree_rv,nloops,rng)
    #Randomly color edges and vertices of the multigraph.
    randomize_colors(mg,colors,rng)
    random_multigraphs.append(mg)

@pytest.mark.parametrize("mg",random_multigraphs)
def test_relabeling(mg):
    """Comparison test on random relabeling."""
    mg_perm,label_map = random_isomorph(mg,rng)
    pstate, data, perm_graphs = compare(mg,mg_perm,verbose=verbose)

@pytest.mark.parametrize("mg",random_multigraphs)
def test_vertex_recoloring(mg):
    """Comparison test on random recoloring of single vertex."""
    v_mg = nx.MultiGraph(mg)
    recolor_random_vertex(v_mg,colors,rng)
    vstate, data, vert_graphs = compare(mg,v_mg,verbose=verbose)

@pytest.mark.parametrize("mg",random_multigraphs)
def test_edge_recoloring(mg):
    """Comparison test on random recoloring of single edge."""
    e_mg = nx.MultiGraph(mg)
    recolor_random_edge(e_mg,colors,rng)
    estate, data, edge_graphs = compare(mg,e_mg,verbose=verbose)
