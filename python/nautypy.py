#! /usr/bin/python/

from _nautypy import ffi,lib
import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
import pygraphviz as pgv
from hashable_containers import hmap,hlist,HGraph,HMultiGraph
from prettytable import PrettyTable


def canonize_simple_graph(g,relabel=True):
    """Canonize a vertex-colored simple graph.

    Interfaces with the NAUTY graph canonization program [https://pallini.di.uniroma1.it/]
    using Python's C Foreign Function Interface.

    Only handles vertex-colored, (not edge-colored) simple (no self-loops, no parallel edges)
    graphs. Canonization of multigraphs with both vertex and edge coloring is implemented 
    in :py:func:`nautypy.canonize_multigraph`.

    **Caveat:** our CFF interface to NAUTY, :mod:`_nauty` expects nodes to be zero-indexed. 
    That is, the node labels must be consecutive integers beginning with zero. If the keyword
    argument `relabel` is True (by default), the node labels of `g` are 
    converted to zero-indexed integers, fed to NAUTY, and then converted back to the original
    labels before returning.

    Given a simple, vertex-colored graph derived from `networkx.Graph`, canonization
    proceeds in stages:

    1. The node indices of `g` are mapped to zero-indexed integers. 
    2. The graph `g` is converted to NAUTY sparse representation
       (see Section 3 of the `NAUTY User's Guide <https://pallini.di.uniroma1.it/Guide.html>`_)
       for details.
    3. `g` is canonized using `_nautypy.lib.canonize`. NAUTY computes the
       'inverse canonical map': a permutation which sends the zero-indexed graph to its canonical
       labeling (canonical isomorph). NAUTY also returns a generating set for the automorphism
       group of the zero-indexed graph.
    4. All indices are mapped from the zero-index back to the original node labels. Thus, the
       automorphism generators and inverse canonical map are sent from permutations of [0,1,2,...]        to dict-like mappings of the original node labels.
    5. The canonical isomorph `g_canonical` is computed by applying the inverse canonical map
       to the input graph `g`.
    6. The canonical map is constructed from its inverse. The forward mapping is
       useful in applications where we wish to represent an arbitrary graph G by its canonical
       isomorph G_c together with the index permutation P such that P(G_c) = G.
       Such a representation is extremely useful in the construction of scattering amplitudes
       from (on-shell or off-shell) diagrams.
       
    Args:
        g (networkx.Graph-like): the graph to canonize. Can be of type `networkx.Graph`
            or a derived class (e.g. `hashable_containers.HGraph`).

    Keyword Args:
        relabel (bool): if True, perform zero-index relabeling before calling NAUTY,
            and apply the inverse relabeling before returning.

    Returns:
        g_canonical (networkx.MultiGraph-like): canonical isomorph of the input graph `g`.
        g_autgens (list): a list of dict-like automorphism generators of Aut(`g`)
        g_canonical_map (dict-like): the node label permutation mapping `g_canonical` to
            the input graph `g`.
    """
    
    #Nauty expects zero-indexed consectutive integers as node labels.
    #Convert from input labeling to zero-indexed integer labeling.
    if relabel:
        input_to_zero = {node:index for index,node in enumerate(sorted(g.nodes.keys()))}
        g_z = HGraph(nx.relabel_nodes(g,input_to_zero,copy=True))
        zero_to_input = {val:key for key,val in input_to_zero.items()}
    else:
        g_z = HGraph(g)
    #Initialize memory for nauty canonize()
    nv = g_z.number_of_nodes()
    nde = 2*g_z.number_of_edges()
    v = ffi.new("size_t[]",nv)
    d = ffi.new("int[]",nv)
    e = ffi.new("int[]",nde)
    lab = ffi.new("int[]",nv)
    ptn = ffi.new("int[]",nv)
    #Compute lab and ptn arrays.
    _lab,_ptn = _get_color_partition(g_z)
    #Load the nx graph g into nauty sparse format.
    de_counter = 0
    for i in range(0,nv):
        lab[i]=_lab[i]
        ptn[i]=_ptn[i]
        d[i]=g_z.degree(i)
        v[i]=de_counter
        neighbors = list(g_z[i].keys())
        for m in range(0,d[i]):
            e[v[i]+m] = neighbors[m]
        de_counter+=d[i]
    #Initialize memory for automorphisms.
    n_auts = ffi.new("int*")
    auts = ffi.new("int***")
    #Invoke canonize()    
    lib.canonize(nv,nde,v,d,e,lab,ptn,n_auts,auts)
    #Convert _lab, lab, ptn to python lists.
    label = []
    canon_label = []
    partition = []
    canon_partition = []
    for i in range(0,nv):
        canon_label.append(int(lab[i]))
        label.append(int(_lab[i]))
        partition.append(int(_ptn[i]))
        canon_partition.append(int(ptn[i]))
    #Construct a relabeling map from the zero_indexed labeling to the canonical zero_indexed labeling.
    #g_z_inverse_canonical_map = dict(zip(canon_label,label))
    g_z_inverse_canonical_map = {l:i for i,l in enumerate(canon_label)}
    print("\n-----------simple canon----------")
    print(f"gz_inv_canmap: {g_z_inverse_canonical_map}")
    print(f"label          : {label}")
    print(f"canon_label    : {canon_label}")
    print(f"partition      : {partition}")
    print(f"canon_partition: {canon_partition}")
    print("---------------------------------\n")

    
    #Conjugate g_z_inverse_canonical_map by zero_to_input to produce g_inverse_canonical_map,
    #which sends the input-labeled graph G to its canonically input-labeled
    #isomorph (g_canonical).
    if relabel:
        g_inverse_canonical_map = {key:zero_to_input[g_z_inverse_canonical_map[val]] for key,val in input_to_zero.items()}
    else:
        g_inverse_canonical_map = g_z_inverse_canonical_map
    #Construct the canonical isomorph.
    g_canonical = g.__class__(nx.relabel_nodes(g,g_inverse_canonical_map,copy=True))
    #Standardize dict order
    g_canonical = _standardize_graph_encoding(g_canonical)
    #Convert automorphisms to hmaps and conjugate to input labeling.
    g_autgens = hlist()
    for i in range(0,n_auts[0]):
        gen_z = hmap({j:auts[0][i][j] for j in range(nv)})
        if relabel:
            gen = {key:zero_to_input[gen_z[val]] for key,val in input_to_zero.items()}
        else:
            gen = gen_z
        g_autgens.append(gen)
    #We will also return the inverse of g_inverse_canonical_map,
    g_canonical_map = hmap({val:key for key,val in g_inverse_canonical_map.items()})
    return g_canonical, g_autgens, g_canonical_map


def _get_color_partition(g):
    """ Given a vertex-colored graph `g`,
    Generate a label list `lab` and color partition `ptn`.

    Both are formatted for argument to NAUTY.
    Equality of colors is equivalent to equality of
    node attribute dictionaries, so no attributes are ignored.

    Assumes zero-indexed `g`.

    Args:
        g(hashable_containers.HGraph)

    Return:
        lab(list): A list of integer node labels (zero-indexed).
        ptn(list): A list of ones and zeros, aligned to `lab`, encoding cells of
            like color (see Section 3 of the
            `NAUTY User's Guide <https://pallini.di.uniroma1.it/Guide.html>`_) for details.
    """

    #Group nodes by equvalence of their attribute dictionaries.
    color_cells = g._node.fibers()
    print("\n===============[g._node]==============")
    for node,att in g._node.items():
        print(f"node: {node}")
        for key,val in att.items():
            print(f"    {key} : {val}")
    print("======================================\n")
    print("\n===============[g._node.fibers()]==============")
    for att,nodes in color_cells.items():
        print(type(att))
        for key,val in att.items():
            print(f"{key} : {val}")
        print(f"    cell: {nodes}")
    print("======================================\n")
    #print(f"color_cells: {color_cells}")
    #print(f"sorted(list(color_cells.keys())): {sorted(list(color_cells.keys()))}")
    print("\n===============[g._node.fibers() <keysorted>]==============")
    for att in sorted(list(color_cells.keys())):
        for key,val in att.items():
            print(f"{key} : {val}")
        print(f"    cell: {color_cells[att]}")
    print("======================================\n")
    #Generate color partition according to color_cells.
    lab = []
    ptn = []
    #label_lists = sorted([sorted(l) for l in color_cells.values()])
    #for l in label_lists:
    #    lab += l
    #    ptn += ([1 for i in range(0,len(l)-1)]+[0,])
    for color in sorted(list(color_cells.keys())):
        lab += color_cells[color]
        ptn += ([1 for i in range(0,len(color_cells[color])-1)]+[0,])
    return lab,ptn


def canonize_multigraph(mg,relabel=True,hostgraphs=None):
    """Canonize an edge- and vertex-colored multigraph.

    Given a multigraph derived from `networkx.MultiGraph`, canonization
    proceeds in stages:

    1. The node indices of `mg` are mapped to zero-indexed integers. 
    2. The multigraph is embedded in a simple, vertex-colored "host" graph derived from
       `networkx.Graph` by :py:func:`nautypy._embed_multigraph`.
    3. The host graph is passed to :py:func:`nautypy.canonize_simple_graph`, producing
       the canonical isomorph of the host graph, a list of its automorphism generators,
       and the canonical map which sends the canonical host graph to the input host graph.
    4. The host graph automorphisms and canonical map are converted to the automorphisms
       and canonical map of the embedded multigraph.
    5. All indices are mapped from the zero-index back to the original node labels. Thus, the
       automorphism generators and canonical map are sent from permutations of [0,1,2,...] to
       dict-like mappings of the original node labels of `mg`.
    6. The canonical isomorph `mg_canonical` is computed by applying the resulting canonical map
       to the input multigraph `mg`.

    Args:
        mg (networkx.MultiGraph-like): the multigraph to canonize. Can be of type
        `networkx.MultiGraph` or a derived class (e.g. `hashable_containers.HMultiGraph`). 

    Keyword Args:
        relabel (bool): if True, perform zero-index relabeling before any calculation,
            and apply the inverse relabeling before returning.
        hostgraphs(None or dict-like): if not None, update :param:`hostgraphs` with copies
            of the input and canonized host graphs.

    Returns:
        mg_canonical (networkx.MultiGraph-like): canonical isomorph of the input multigraph `mg`.
        mg_autgens (list): a list of dict-like automorphism generators of Aut(`mg`)
        mg_canonical_map (dict-like): the node label permutation mapping mg_canonical to
            the input multigraph `mg`.
    """

    #Nauty expects zero-indexed consectutive integers as node labels.
    #Convert from input labeling to zero-indexed integer labeling.
    if relabel:
        input_to_zero = {node:index for index,node in enumerate(sorted(mg.nodes.keys()))}
        mg_z = HMultiGraph(nx.relabel_nodes(mg,input_to_zero,copy=True))
        zero_to_input = {val:key for key,val in input_to_zero.items()}
    else:
        mg_z = HMultiGraph(mg)
    #Embed MultiGraph mg in a simple, vertex-colored host graph G
    g_z = _embed_multigraph(mg_z)
    #Optionally store the host graph.
    if hostgraphs!=None:
        if relabel:
            hostgraphs['host'] = nx.relabel_nodes(g_z,zero_to_input,copy=True)
        else:
            hostgraphs['host'] = g_z.copy()
    #Compute a canonically labeled host graph CG from g.
    g_z_canonical, g_z_autgens, g_z_canonical_map = canonize_simple_graph(g_z,relabel=False)
    #Optionally store the canonized host graph.
    if hostgraphs!=None:
        if relabel:
            hostgraphs['host_canonical'] = nx.relabel_nodes(g_z_canonical,zero_to_input,copy=True)
        else:
            hostgraphs['host_canonical'] = g_z_canonical.copy()
    #Restrict g_z_canonical_map from the full range of host graph nodes to the
    #nodes of the embedded multigraph.
    mg_z_canonical_map = hmap({key:val for key,val in g_z_canonical_map.items() if key<mg_z.order()})
    #Conjugate mg_z_canonical_map zero_to_input.
    if relabel:
        print(f"in2zero: {input_to_zero}")
        print(f"zero2in: {zero_to_input}")
        print(f"MGZCMAP: {mg_z_canonical_map}")
        mg_canonical_map = hmap({key:zero_to_input[mg_z_canonical_map[val]] for key,val in input_to_zero.items()})
    else:
        mg_canonical_map = hmap(mg_z_canonical_map)
    #The inverse map sends the input-labeled multigraph mg to its canonically
    #input-labeled isomorph (mg_canonical).
    mg_inverse_canonical_map = hmap({val:key for key,val in mg_canonical_map.items()})
    mg_canonical = mg.__class__(nx.relabel_nodes(mg,mg_inverse_canonical_map,copy=True))
    #Standardize dict order
    mg_canonical = _standardize_graph_encoding(mg_canonical)
    #Restrict host graph automorphism generators to multigraph nodes.
    #Conjugate multigraph automorphism generators from zero-index to input labeling.
    mg_autgens = hlist()
    for gen_z in g_z_autgens:
        mg_gen_z = hmap({key:val for key,val in gen_z.items() if key<mg.order()})
        if relabel:
            mg_gen = {key:zero_to_input[mg_gen_z[val]] for key,val in input_to_zero.items()}
        else:
            mg_gen = mg_gen_z
        mg_autgens.append(mg_gen)
    return mg_canonical, mg_autgens, mg_canonical_map


def _standardize_graph_encoding(g):
    """ Copy a graph or multigraph, filling all attribute dictionaries 
    in key-sorted order.

    We can guarantee that any two graphs returned by `canonize_simple_graph` 
    or two multigraphs returned by `canonize_multigraph` which have the same
    edge, vertex, and graph attribute dictionaries (modulo key order) will
    produce the same `nautypy.gdraw` and `nautypy.gprint` outputs by filling
    their attribute dictionaries in key-sorted order before returning/plotting.

    **Caveat:** this operation is *not* related to isomorphism, and does not 
    alter the graph encoded in the object `g`. We are only standardizing 
    the *encoding* of the graph to ease visual inspection by the user.

    **Another Caveat:** Even after standardization, two equivalent graphs
    encoded in objects of type `networkx.Graph` or `networkx.MultiGraph`
    may not compare equal using the `==` operator. Comparison of networkx
    objects must be performed with `networkx.utils.graphs_equal(g1,g2)`
    to determine eqality of the *encoded graphs*. The subclasses
    `hashable_containers.HGraph` and `hashable_containers.HMultiGraph`
    have overloaded the `==` operator to compare the embedded graphs
    directly in an effort to avoid this confusion.

    Args:
        g (networkx.Graph-like or networkx.MultiGraph-like): Any graph or 
            multigraph derived from networkx type.

    Returns:
        g_standard (networkx.Graph-like or networkx.MultiGraph-like): A
            copy of `g` with all dictionaries in key-sorted order.
    """

    g_standard = g.__class__()
    #Copy graph attribute dictionary.
    g_standard.graph.update(g.graph)
    #Copy node dictionary in key-sorted order.
    s_nodes = [(node,dict(g.nodes[node])) for node in sorted(g.nodes)]
    for sn in s_nodes:
        g_standard.add_node(sn[0],**sn[1])
    #Copy adj dictionary in key-sorted order.
    s_edges = [(edge,dict(g.edges[edge])) for edge in sorted(g.edges)]
    for se in s_edges:
        g_standard.add_edge(*se[0],**se[1])
    return g_standard


def _embed_multigraph(mg):
    """ Embed a vertex- and edge-colored multigraph (including self-loops)
    in vertex-colored simple graph.

    Assumes `mg` is zero-indexed.
    
    Args:
        mg(networkx.MultiGraph-like): The multigraph to be embedded.

    Returns:
        g(hashable_containers.HGraph): The simple "host graph" encoding `mg`.
    """

    g = HGraph()
    #Copy the graph attribute dict from mg to g.
    g.graph.update(mg.graph)
    # Add all multigraph nodes to the simple graph as nodes with type "vertex".
    # Copy the node attributes from mg to g.
    for node in mg.nodes():
        g.add_node(node)
        g.nodes[node]["type"]="vertex"
        g.nodes[node].update(mg.nodes[node])
    #Beginning with the max label, add all multigraph edges to the simple graph
    #as nodes with type "edge".
    #Copy the edge attributes from mg to g.
    node = mg.order()
    for edge in mg.edges:
        g.add_node(node)
        g.nodes[node]["type"]="edge"
        g.nodes[node].update(mg.edges[edge])
        g.add_edge(node,edge[0])
        g.add_edge(node,edge[1])
        node += 1
    return g


def _extract_multigraph(g):
    """ Extract a vertex- and edge-colored multigraph (including self-loops)
    from a vertex-colored simple graph. Assumes zero-indexed `g`.

    Args:
        g(networkx.Graph-like): The simple host graph encoding a multigraph.

    Returns:
        mg(hashable_containers.HMultiGraph): The encoded multigraph.

    Note:
        **Not currently used.**
    """

    mg = HMultiGraph()
    #Copy the graph attribute dict from G to mg.
    mg.graph.update(g.graph)
    #Embed nodes and edges.
    for node in g.nodes():
        if g.nodes[node]["type"] == "vertex":
            mg.add_node(node)
            mg.nodes[node].update(g.nodes[node])
            #No longer need to track "type"
            del mg.nodes[node]["type"]
        else: #G node represents an mg edge.
            #Thus, two neighbors usually,
            neighbors = list(G[node].keys())
            #unless self loop:
            if len(neighbors)==1:
                #Resolve into actual mg self-loop.
                nnode = neighbors[0]
                neighbors = [nnode,nnode]
            # Add edge to mg, combine [neighbors] into [n1,n2,key] mg edge key.
            key = mg.add_edge(*neighbors)
            edge = neighbors
            edge.append(key)
            #Update edge attribute dict.
            mg.edges[edge].update(g.nodes[node])
            #No longer need to track "type"
            del mg.edges[edge]["type"]
    return mg




def gprint(_g):
    """ Pretty-print graph data.

    Print graph data in a table format. Graph encodings are standardized with
    `nautypy._standardize_graph_encoding` before formatting to ensure that equivalent
    graphs produce identical output.

    Args:
        g(networkx.Graph-like): Input graph. Can be derived from `networkx.Graph` or
            `networkx.MultiGraph`.
    """
    g = _standardize_graph_encoding(_g)
    #Print node data table(s).
    if 'type' in g.nodes[list(g.nodes.keys())[0]].keys():
        vnodes = {key:val for key,val in g.nodes.items() if 'vertex' in val.values()}
        vntab = PrettyTable(["node"]+list(vnodes[list(vnodes.keys())[0]].keys()))
        for node in vnodes:
            vntab.add_row([node]+list(vnodes[node].values()))
        print(vntab)

        enodes = {key:val for key,val in g.nodes.items() if 'edge' in val.values()}
        entab = PrettyTable(["node"]+list(enodes[list(enodes.keys())[0]].keys()))
        for node in enodes:
            entab.add_row([node]+list(enodes[node].values()))
        print(entab)
    else:
        ntab = PrettyTable(["node"]+list(g.nodes[list(g.nodes.keys())[0]].keys()))
        for node in g.nodes:
            ntab.add_row([node]+list(g.nodes[node].values()))
        print(ntab)
    #Print edge data table.
    etab = PrettyTable(["edge"]+list(g.edges[list(g.edges.keys())[0]].keys()))
    for edge in g.edges:
        etab.add_row([edge]+list(g.edges[edge].values()))
    print(etab)
    print('\n')


def gdraw(_g, title='', layout='neato', fname = None):
    """ Draw a graph using pygraphviz.

    Args:
        g(networkx.Graph-like): Input graph. Can be derived from `networkx.Graph` or
            `networkx.MultiGraph`.

    Keyword Args:
        title(str): Optional title for the plot. Defaults to ''. 
        layout(str): Layout for graph drawing. Defaults to 'neato'.
        fname(str): Optional filename at which to save the drawing.
            if None (default), the drawing is only temporarily saved
            to 'temp_graph.png' and deleted after the plot is closed.
    """

    #Standardize graph encoding by key-sorting node and adj dictionaries
    #with _standardize_graph_encoding. This ensures that node and edge
    #positions on the graph drawing are independent of the order in which
    #they were inserted into the graph object.
    #This property is especially useful when visually comparing graphs to
    #their canonical isomorphs, because it guarantees that the nodes
    #stabilized by canonization do not change position on the
    #graph drawing.
    g = _standardize_graph_encoding(_g) 
    # s_nodes = [(node,dict(_g.nodes[node])) for node in sorted(_g.nodes)]
    # for sn in s_nodes:
    #     g.add_node(sn[0],**sn[1])
    # s_edges = [(edge,dict(_g.edges[edge])) for edge in sorted(_g.edges)]
    # for se in s_edges:
    #     g.add_edge(*se[0],**se[1])
    #Convert to pygraphviz format.
    A = to_agraph(g)
    #Fix drawing layout.
    A.layout(layout)
    #Display hi-res image.
    A.graph_attr.update(dpi=300.0)
    #Set filename and draw graph.
    if fname==None:
        filename = 'temp_graph.png'
    else:
        filename = fname
    A.draw(filename)
    ax = plt.gca()
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)
    ax.set_title(title)
    plt.imshow(mpimg.imread(filename))
    #Optionally remove temporary graph file.
    if fname==None:
        os.system(f"rm {filename}")
    return
