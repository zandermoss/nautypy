#! /usr/bin/python3
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stat
import nautypy as nty
from random_graphs import random_multigraph, randomize_colors, random_isomorph
from networkx.algorithms import isomorphism

#Initialize np.random RNG.
rng = np.random.default_rng(12345)
#Number of vertices
nv=10
#Number of loops
nloops = 5
#Edge/Vertex Colors
#colors = ['red','orange','yellow','green','blue','indigo','violet']
colors = ['red','orange','green','blue','indigo','violet']
#Exponential distribution for child multiplicity of spanning tree.
tree_rv = stat.expon(loc=0,scale=1)
tree_rv.random_state = rng
#Generate random multigraph
mg = random_multigraph(nv,tree_rv,nloops,rng)
#Randomly color edges and vertices of the multigraph.
randomize_colors(mg,colors,rng)
#Generate a random isomorph of the multigraph.
mg_perm,label_map = random_isomorph(mg,rng)


#Construct example multigraph.
#mg1 = nx.MultiGraph()
mg1 = nx.MultiGraph()
mg1.add_node(0,color="red")
mg1.add_node(1,color="red")
mg1.add_node(2,color="blue")
mg1.add_edge(0,1,color="black")
mg1.add_edge(1,2,color="black")

#Construct example multigraph.
#mg2 = nx.MultiGraph()
mg2 = nx.MultiGraph()
mg2.add_node(0,color="red")
mg2.add_node(1,color="red")
mg2.add_node(2,color="blue")
mg2.add_edge(0,1,color="black")
mg2.add_edge(1,2,color="black")
mg2 = nx.relabel_nodes(mg2,{0:2,1:1,2:0},copy=True)

print("---------MG1---------")
for node in mg1.nodes:
    print(node)
    print(mg1.nodes[node])
print("---------MG2---------")
for node in mg2.nodes:
    print(node)
    print(mg2.nodes[node])



def node_match_color(n1,n2):
    print()
    print(n1)
    print(n2)
    print()
    return n1['color']==n2['color']

#matcher = isomorphism.GraphMatcher(mg1, mg2,)
#iso_q = matcher.is_isomorphic()
#iso_q = nx.is_isomorphic(mg1,mg2,node_match=node_match_color)
#iso_q = nx.is_isomorphic(mg1,mg2)
#print(f"Isomorphic? {iso_q}")
#perm = matcher.mapping
#print(f"Permutation: {perm}")



#Canonicalize multigraphs.
#mg1_canonical,mg1_autgens,mg1_canonical_map = nty.canonize_multigraph(mg1) 
#mg2_canonical,mg2_autgens,mg2_canonical_map = nty.canonize_multigraph(mg2) 
mg1_canonical,mg1_autgens,mg1_canonical_map = nty.canonize_simple_graph(mg1) 
mg2_canonical,mg2_autgens,mg2_canonical_map = nty.canonize_simple_graph(mg2) 

#Compare mg, mg_perm, mg_canonical, mg_perm_canonical.
print(f'mg1 Canonical Map: {mg1_canonical_map}')
print(f'mg2 Canonical Map: {mg2_canonical_map}')
print(f'(mg1 = mg2)? {nx.utils.graphs_equal(mg1_canonical,mg2_canonical)}')



#Draw graphs.
subax1 = plt.subplot(221)
#nty.gdraw(mg, title = "Random MultiGraph")
nty.gdraw(mg1, title = "MG1")
subax2 = plt.subplot(222)
nty.gdraw(mg1_canonical, title = "MG1 Canonical")
#g_colormap = [g.nodes[node]['color'] for node in g.nodes]
#g_edge_colormap = [g.edges[edge]['color'] for edge in g.edges]
#nx.draw(g, with_labels=True, font_weight='bold',node_color = g_colormap,edge_color = g_edge_colormap)
subax3 = plt.subplot(223)
#nty.gdraw(mg_perm, title = "Random Node Permutation")
nty.gdraw(mg2, title = "MG2")
subax4 = plt.subplot(224)
nty.gdraw(mg2_canonical, title = "MG2 Canonical")
#g_p_colormap = [g_p.nodes[node]['color'] for node in g_p.nodes]
#g_p_edge_colormap = [g_p.edges[edge]['color'] for edge in g_p.edges]
#nx.draw(g_p, with_labels=True, font_weight='bold',node_color = g_p_colormap,edge_color = g_p_edge_colormap)
plt.show()





# nv = 20
# scale = 1
# tree = random_tree(nv,stat.expon(loc=0,scale=scale))
# dg = diameter(tree,0)
#
# dia_path = diameter_path(dg)
# print(dia_path)
# mp = midpoints(dia_path)
# print(mp)
#
# for v in range(nv):
#     tree.nodes[v]['color']='lightgray'
# for v in dia_path:
#     tree.nodes[v]['color']='cyan'
# for v in mp:
#     tree.nodes[v]['color']='orange'
#
# colormap = [tree.nodes[v]['color'] for v in range(nv)]
# nodelist = list(range(nv))
# print(colormap)
# print(list(tree))
#
# subax1 = plt.subplot(121)
# nx.draw(tree, with_labels=True, font_weight='bold', nodelist=nodelist, node_color=colormap, pos=nx.nx_agraph.graphviz_layout(nx.bfs_tree(tree,0),prog='dot'))
#
# subax2 = plt.subplot(122)
# nx.draw(tree, with_labels=True, font_weight='bold', nodelist=nodelist, node_color=colormap, pos=nx.nx_agraph.graphviz_layout(nx.bfs_tree(tree,mp[0]),prog='dot'))
#
# dg_mp_root = diameter(tree,mp[0])
#
# print("OG Diameter: {}  New Diameter: {}".format(dg.nodes[0]['diameter'],dg_mp_root.nodes[mp[0]]['diameter']))
# print("OG Height: {}  New Height: {}".format(dg.nodes[0]['height'],dg_mp_root.nodes[mp[0]]['height']))
#
#
# plt.show()
#
#
#
#
#
