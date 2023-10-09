#! /usr/bin/python3 
import networkx as nx
 
class hmap(dict): 
    """
    Dict subclass which includes 
    a hash function, as well as a function to compute
    the fibers of the map.
    """
 
    def fibers(self): 
        _fibers = {value:[] for value in self.values()}
        for key, value in super().items(): 
            _fibers[value].append(key) 
        
        _fibers = hmap({key:tuple(value) for (key,value) in _fibers.items()})

        return _fibers 

    def __hash__(self): 
        return hash(tuple(sorted(super().items()))) 

    def __lt__(self,other):
        assert type(self)==type(other)
        return tuple(sorted(super().items())) < tuple(sorted(other.items()))
        #return hash(self) < hash(other)


class hlist(list): 
    """
    List subclass which includes 
    a hash function.
    """

    def __hash__(self): 
        return hash(tuple(super().copy())) 

    def __lt__(self,other):
        assert type(self)==type(other)
        return tuple(sorted(super().copy())) < tuple(sorted(other.copy()))
        #return hash(self) < hash(other)


class HGraph(nx.Graph):
    """
    `networkx.Graph`  subclass  which uses hmap containers
    instead of python dicts. Because hmap objects are hashable,
    the graph object itself can be hashed. A well-behaved __eq__
    function is also defined, using the same data
    (graph, _node, _adj) as hash function.
    """

    #Use hashable_containers::hmap for all dict factory functions.
    node_dict_factory = hmap
    node_attr_dict_factory = hmap
    adjlist_outer_dict_factory = hmap
    adjlist_inner_dict_factory = hmap
    edge_attr_dict_factory = hmap
    graph_attr_dict_factory = hmap

    def __eq__(self,other):
        return (self.graph, self._node, self._adj) == (other.graph,
                                                        other._node,
                                                        other._adj)

    def __hash__(self):
        return hash((self.graph, self._node, self._adj))




class HMultiGraph(nx.MultiGraph):
    """
    Analogous to hashable_containers.HGraph, but for the
    networkx.MultiGraph class.
    """

    #Use hashable_containers::hmap for all dict factory functions.
    node_dict_factory = hmap
    node_attr_dict_factory = hmap
    adjlist_outer_dict_factory = hmap
    adjlist_inner_dict_factory = hmap
    edge_key_dict_factory = hmap
    edge_attr_dict_factory = hmap
    graph_attr_dict_factory = hmap

    def __eq__(self,other):
        return (self.graph, self._node, self._adj) == (other.graph,
                                                        other._node,
                                                        other._adj)

    def __hash__(self):
        return hash((self.graph, self._node, self._adj))
         

if __name__ == '__main__': 
 
    owl = hmap() 
    owl = hmap({'a':1,'b':2,'c':2})
    for i in range(5):
        print(f"{i}: {owl}")
        owl = owl.fibers()
