#! /usr/bin/python

import networkx as nx
import matplotlib.pyplot as plt
import scipy.stats as stat
import numpy as np
import math

"""
A collection of functions used during testing to generate
random multigraphs with random vertex and edge coloring.
"""


def random_tree(nv,rv):
    g = nx.Graph()
    i=0
    q=[i]
    while True:
        v = q.pop(0)
        nchildren = math.ceil(rv.rvs())
        for j in range(nchildren):
            i+=1
            if(i>=nv):
                return g
            g.add_node(i)
            g.add_edge(v,i)
            q.append(i)
    return g


def random_multigraph(nv,tree_rv,nloops,rng):
    tree = random_tree(nv,tree_rv)
    random_loop_edges = zip(rng.integers(low=0,high=nv,size=nloops),
                            rng.integers(low=0,high=nv,size=nloops))
    g = nx.MultiGraph(tree)
    for n1,n2 in random_loop_edges:
        g.add_edge(n1,n2)
    return g


def randomize_colors(g,colors,rng):
    nv = g.number_of_nodes()
    ne = g.number_of_edges()
    nc = len(colors)
    #Color nodes.
    random_vertex_colors = rng.integers(low=0,high=nc,size=nv)
    for c,node in zip(random_vertex_colors,g.nodes):
        g.nodes[node]['color'] = colors[c]
        #print(g.nodes[node])
    #Color edges.
    random_edge_colors = rng.integers(low=0,high=nc,size=ne)
    for c,edge in zip(random_edge_colors,g.edges):
        g.edges[edge]['color'] = colors[c]
    return

def recolor_random_vertex(g,colors,rng):
    nv = g.number_of_nodes()
    ne = g.number_of_edges()
    nc = len(colors)
    random_vertex = rng.integers(low=0,high=nv,size=1)
    random_vertex_color = rng.integers(low=0,high=nc,size=1)
    g.nodes[random_vertex[0]]['color'] = colors[random_vertex_color[0]]
    return

def recolor_random_edge(g,colors,rng):
    nv = g.number_of_nodes()
    ne = g.number_of_edges()
    nc = len(colors)
    edgelist = list(g.edges)
    random_edge_index = rng.integers(low=0,high=len(edgelist),size=1)
    edge = edgelist[random_edge_index[0]]
    random_edge_colors = rng.integers(low=0,high=nc,size=1)
    g._adj[edge[0]][edge[1]][edge[2]]['color']=colors[random_edge_colors[0]]
    return


def random_isomorph(g,rng):
    nv = g.number_of_nodes()
    indices = list(range(nv))
    perm = list(indices)
    rng.shuffle(perm)
    label_map = {i:p for i,p in zip(indices,perm)}
    g_p = nx.relabel_nodes(g,label_map,copy=True)
    return g_p,label_map




#------------------------------------------#
if __name__ == '__main__':
    nv = 20
    scale = 3
    tree = random_tree(nv,stat.expon(loc=0,scale=scale))
    nx.draw(tree, with_labels=True, font_weight='bold')
    plt.show()
