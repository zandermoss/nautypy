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


def _canonize(g, _lab, _ptn):
    """Python wrapper for the C interface `_nautypy.lib.canonize`.

    N.B. While the ordering of the labels in `_lab` within each cell of `_ptn`
    is irrelevant, the ordering of the cells within `ptn_` is important.
    The canonical label returned from nauty is a permutation of `_lab` 
    which *respects color cells*. The block of indices ultimately assigned to each
    input cell are ordered according to `_ptn`. For example, a graph with six vertices
    and three colors: {(1,4):red, (0,3,5):green, (2):blue} might be represented by

        _lab=[4,1,0,3,5,2]
        _ptn=[1,0,1,1,0,0]

    In `_ptn`, zeros indicate (inclusive) cell end boundaries, so this is equivalent to the partition

        [4,1|0,3,5|2]

    NAUTY might return the canonical labeling

        lab=[1,4,3,5,0,2]

    The labels within color cells have been permuted, but the cell boundaries have been respected.
    Critically, the permutation sending `_lab` to `lab` is **not** the canonical permutation!
    Rather, the canonical permutation is given by the list `lab` in 'one-line notation'. In this case,

        canonical_map = {0->1, 1->4, 2->3, 3->5, 4->0, 5->2}

    This is the relabeling which sends the canonically labeled graph to the input graph `g`.
    The inverse map,

        inverse_canonical_map = {0->4, 1->0, 2->5, 3->2, 4->1, 5->3}

    is the map we actually apply to the graph `g` to canonize it in `nautypy.canonize_simple_graph`
    and `nautypy.canonize_multigraph`. The resulting coloring of the canonically labeled graph is

    {(0,1):red, (2,3,4):green, (5):blue}

    This map is determined by the ordering (red,green,blue) of the cells in `_lab` and `_ptn`.
    For the purposes of graph matching, this order doesn't matter as long as it's consistent among
    all calls to NAUTY. For this reason, `nautypy.canonize_simple_graph` simply sorts vertex colors
    (node attribute dictionaries) as tuples of (key,value) tuples, yielding an arbitrary but consistent
    color ordering (provided keys and values are comparable).

    On the other hand, `nautypy.canonize_multigraph` adds nodes to the input multigraph to represent
    edges, and it is convenient to order all edge node colors after all vertex node colors explicitly
    so that edge labels and vertex labels are never mixed during canonization.

    Args:
        g (networkx.Graph-like): A simple, vertex-labeled (no edge labels!) graph to canonize.
            The node labels must be sequential integers beginning with zero.
        _lab (list): A list of the node labels assigning them to the color cells demarkated in `_ptn`
        _ptn (list): A list of ones and zeros, aligned to `lab`, encoding cells of
            like color (see Section 3 of the
            `NAUTY User's Guide <https://pallini.di.uniroma1.it/Guide.html>`_) for details.

    Returns:
        canonical_map (hashable_containers.hmap): A mapping *from* the labels of the canonical isomorph
            *to* the input graph `g`.
        autgens (hashable_containers.hlist): A list of `hashable_containers.hmaps` encoding the generators
            of the automorphism group of `g`.
    """

    #Initialize memory for nauty canonize()
    nv = g.number_of_nodes()
    nde = 2*g.number_of_edges()
    v = ffi.new("size_t[]",nv)
    d = ffi.new("int[]",nv)
    e = ffi.new("int[]",nde)
    lab = ffi.new("int[]",nv)
    ptn = ffi.new("int[]",nv)
    #Load the nx graph g into nauty sparse format.
    de_counter = 0
    for i in range(0,nv):
        lab[i]=_lab[i]
        ptn[i]=_ptn[i]
        d[i]=g.degree(i)
        v[i]=de_counter
        neighbors = list(g[i].keys())
        for m in range(0,d[i]):
            e[v[i]+m] = neighbors[m]
        de_counter+=d[i]
    #Initialize memory for automorphisms.
    n_auts = ffi.new("int*")
    auts = ffi.new("int***")
    #Invoke canonize()    
    lib.canonize(nv,nde,v,d,e,lab,ptn,n_auts,auts)
    #Construct a relabeling map from lab.
    canonical_map = hmap({i:int(lab[i]) for i in range(nv)})
    #Convert automorphisms to hmaps and conjugate to input labeling.
    autgens = hlist()
    for i in range(0,n_auts[0]):
        gen = hmap({j:auts[0][i][j] for j in range(nv)})
        autgens.append(gen)
    return canonical_map, autgens


def _get_color_partition(g,color_sort_conditions=[]):
    """ Given a vertex-colored graph `g`,
    Generate a label list `lab` and color partition `ptn`.

    Both are formatted for argument to NAUTY.
    Equality of colors is equivalent to equality of
    node attribute dictionaries, so no attributes are ignored.

    Assumes zero-indexed `g`.

    Args:
        g(hashable_containers.HGraph)

    Keyword Args:
        color_sort_conditions(list): A list of tuples (key:state) used to establish
            a partial color ordering among the canonical labels. For example, [('type':'vertex')]
            would assign all nodes satisfying node['type']=='vertex' integer labels strictly less
            than nodes satisfying node['type']!='vertex' or not containing the key 'type'.
            This ordering can be extended by adding tuples to the condition list. For example,
            [('type':'vertex'),('weight'<1.0)] would first order the node labels according to 
            the 'type'=='vertex' condition, and then within each of the two partitions (=='vertex'            and !='vertex'/no key 'vertex'), would apply an analogous order using the condition
            node['weight']<1.0. 

    Return:
        lab(list): A list of integer node labels (zero-indexed).
        ptn(list): A list of ones and zeros, aligned to `lab`, encoding cells of
            like color (see Section 3 of the
            `NAUTY User's Guide <https://pallini.di.uniroma1.it/Guide.html>`_) for details.
    """

    g = _standardize_graph_encoding(g)
    color_cells = g._node.fibers()
    cell_orders = hmap()
    for color in color_cells.keys():
        order = 0
        for n,c in enumerate(color_sort_conditions[::-1]):
            if c[0] in color:
                coeff = int(color[c[0]]!=c[1])
            else:
                coeff = 1
            order+= coeff*2**n
        cell_orders[color] = order
    colors_by_order = cell_orders.fibers()
    lab = []
    ptn = []
    for order in sorted(list(colors_by_order.keys())):
        colors = colors_by_order[order]
        for color in sorted(colors):
            lab += sorted(color_cells[color])
            ptn += ([1 for i in range(0,len(color_cells[color])-1)]+[0,])
    return lab,ptn


def canonize_simple_graph(g, color_sort_conditions = []):
    """Canonize a vertex-colored simple graph.

    Interfaces with the NAUTY graph canonization program [https://pallini.di.uniroma1.it/]
    using Python's C Foreign Function Interface.

    Only handles vertex-colored, (not edge-colored) simple (no self-loops, no parallel edges)
    graphs. Canonization of multigraphs with both vertex and edge coloring is implemented 
    in :py:func:`nautypy.canonize_multigraph`.

    Given a simple, vertex-colored graph derived from `networkx.Graph`, canonization
    proceeds in stages:

    1. The node indices of `g` are mapped to zero-indexed integers (NAUTY format). 
    2. The graph `g` is converted to NAUTY sparse representation
       (see Section 3 of the `NAUTY User's Guide <https://pallini.di.uniroma1.it/Guide.html>`_)
       for details.
    3. `g` is canonized using `_nautypy.lib.canonize`. NAUTY computes the
       'canonical map': a permutation which sends the canonically labeled graph (canonical isomorph)
       to the input graph. NAUTY also returns a generating set for the automorphism
       group of the zero-indexed graph.
    4. All indices are mapped from the zero-index back to the original node labels. Thus, the
       automorphism generators and canonical map are sent from permutations of [0,1,2,...]
       to dict-like mappings of the original node labels.
    5. The canonical isomorph `g_canonical` is computed by applying the inverse canonical map
       to the input graph `g`.
       
    Args:
        g (networkx.Graph-like): the graph to canonize. Can be of type `networkx.Graph`
            or a derived class (e.g. `hashable_containers.HGraph`).

    Returns:
        g_canonical (networkx.Graph-like): canonical isomorph of the input graph `g`. The return object
            belongs to the same class as the input graph `g`.
        g_autgens (list): a list of dict-like automorphism generators of Aut(`g`)
        g_canonical_map (dict-like): the node label permutation mapping `g_canonical` to
            the input graph `g`.
    """

    g = _standardize_graph_encoding(g)    
    #Convert from input labeling to zero-indexed integer labeling.
    input_to_zero = {node:index for index,node in enumerate(sorted(g.nodes.keys()))}
    g_z = HGraph(nx.relabel_nodes(g,input_to_zero,copy=True))
    zero_to_input = {val:key for key,val in input_to_zero.items()}
    #Compute lab and ptn arrays.
    color_cells = g_z._node.fibers()
    lab, ptn = _get_color_partition(g_z, color_sort_conditions=color_sort_conditions)
    #Canonize
    g_z_canonical_map, g_z_autgens = _canonize(g_z, lab, ptn)
    #Convert from zero-indexed integer labeling to input labeling.
    g_canonical_map = {key:zero_to_input[g_z_canonical_map[val]] for key,val in input_to_zero.items()}
    g_autgens = hlist()
    for gen_z in g_z_autgens:
        gen = {key:zero_to_input[gen_z[val]] for key,val in input_to_zero.items()}
        g_autgens.append(gen)
    #Invert the canonical map.
    g_inverse_canonical_map = hmap({val:key for key,val in g_canonical_map.items()})
    #Construct the canonical isomorph.
    g_canonical = g.__class__(nx.relabel_nodes(g,g_inverse_canonical_map,copy=True))
    #Standardize dict order
    g_canonical = _standardize_graph_encoding(g_canonical)
    return g_canonical, g_autgens, g_canonical_map


def canonize_multigraph(mg, color_sort_conditions=[], hostgraphs=None):
    """Canonize an edge- and vertex-colored multigraph.

    Given a multigraph derived from `networkx.MultiGraph`, canonization
    proceeds in stages:

    1. The node indices of `mg` are mapped to zero-indexed integers. 
    2. The multigraph is embedded in a simple, vertex-colored "host" graph derived from
       `networkx.Graph` by :py:func:`nautypy._embed_multigraph`.
    3. The host graph is passed to :py:func:`nautypy._canonize`, producing
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
        hostgraphs(None or dict-like): if not None, update :param:`hostgraphs` with copies
            of the input and canonized host graphs.

    Returns:
        mg_canonical (networkx.MultiGraph-like): canonical isomorph of the input multigraph `mg`.
            The return object belongs to the same class as the input multigraph `mg`.
        mg_autgens (list): a list of dict-like automorphism generators of Aut(`mg`)
        mg_canonical_map (dict-like): the node label permutation mapping mg_canonical to
            the input multigraph `mg`.
    """

    mg = _standardize_graph_encoding(mg)
    #Nauty expects zero-indexed consectutive integers as node labels.
    #Convert from input labeling to zero-indexed integer labeling.
    input_to_zero = {node:index for index,node in enumerate(sorted(mg.nodes.keys()))}
    mg_z = HMultiGraph(nx.relabel_nodes(mg,input_to_zero,copy=True))
    zero_to_input = {val:key for key,val in input_to_zero.items()}
    #Embed MultiGraph mg in a simple, vertex-colored host graph G
    g_z = _embed_multigraph(mg_z)
    #Optionally store the host graph.
    if hostgraphs!=None:
        hostgraphs['host'] = g_z
    #Compute lab and ptn arrays.
    _node_vertices = hmap({node:g_z._node[node] for node in range(0,mg.order())})
    vertex_color_cells = _node_vertices.fibers()
    # Don't mix vertex and edge labels
    lab, ptn = _get_color_partition(g_z,
        color_sort_conditions = [('type','vertex')]+color_sort_conditions)
    #Compute a canonically labeled host graph CG from g.
    g_z_canonical_map, g_z_autgens = _canonize(g_z, lab, ptn)
    #Optionally store the canonized host graph.
    if hostgraphs!=None:
        g_z_inverse_canonical_map = hmap({val:key for key,val in g_z_canonical_map.items()})
        hostgraphs['host_canonical'] = nx.relabel_nodes(g_z,g_z_inverse_canonical_map,copy=True)
    #Convert from zero-indexed integer labeling to input labeling.
    mg_canonical_map = {key:zero_to_input[g_z_canonical_map[val]] for key,val in input_to_zero.items()}
    mg_autgens = hlist()
    for gen_z in g_z_autgens:
        gen = {key:zero_to_input[gen_z[val]] for key,val in input_to_zero.items()}
        mg_autgens.append(gen)
    #Invert the canonical map.
    mg_inverse_canonical_map = hmap({val:key for key,val in mg_canonical_map.items()})
    #Construct the canonical isomorph.
    mg_canonical = HMultiGraph(nx.relabel_nodes(mg,mg_inverse_canonical_map,copy=True))
    #Key multi-edges in color-sorted order.
    mg_canonical_edgesort = HMultiGraph()
    mg_canonical_edgesort.graph.update(mg_canonical.graph)
    for node in mg_canonical.nodes:
        mg_canonical_edgesort.add_node(node,**dict(mg_canonical.nodes[node]))
    for edgepair in set(mg_canonical.edges()):
        multiedges = mg_canonical.adj[edgepair[0]][edgepair[1]]
        colors = sorted(list(multiedges.values()))
        for key,color in enumerate(colors):
            mg_canonical_edgesort.add_edge(*edgepair,key=key,**color)
    #Convert to input graph class
    mg_canonical = mg.__class__(mg_canonical_edgesort)
    #Standardize dict order
    mg_canonical = _standardize_graph_encoding(mg_canonical)
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
