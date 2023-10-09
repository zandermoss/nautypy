#! /usr/bin/python3
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stat
import nautypy as nty
from time import time
from random_graphs import random_multigraph, randomize_colors, random_isomorph,recolor_random_vertex, recolor_random_edge
from networkx.algorithms import isomorphism
from sympy.combinatorics import Permutation, PermutationGroup
from sympy.combinatorics.named_groups import SymmetricGroup
from colorama import Fore, Style

def att_match(d1,d2):
    return d1==d2


def colstate(state):
    if state:
        return Fore.GREEN + Style.BRIGHT + str(state) + Style.RESET_ALL
    else:
        return Fore.RED + Style.BRIGHT + str(state) + Style.RESET_ALL


def compare(mg,mg2,verbose=False):
    """Compares isomorphism matching outputs from nautypy and VF2 (through networkx)

    Given two multigraphs, ``mg``, ``mg2``, calls both VF2 and `nautypy.canonize_multigraph`
    to determine if they are isomorphic, and, if so, what node relabeling map realizes 
    the isomorphism. The test breaks into three checks:

    1. Do nautypy and VF2 agree on the isomorphism of the two multigraphs (mg~mg2)?
    2. If they agree, do nautypy and VF2 produce mappings realizing the isomorphism
        which agree up to automorphisms of mg and mg2?
    3. If ``mg`` and ``mg2`` yield different canonical maps, are they related by an
        automorphism? Nautypy has been designed to yield canonical maps which are
        unambiguous under automorphism, so the answer should be **no**.
    """

    data = dict()
    #VF2 Matching
    matcher = isomorphism.GraphMatcher(mg, mg2, node_match = att_match,
                                       edge_match = att_match)
    iso_q = matcher.is_isomorphic()
    data['vf2_iso']=iso_q
    vf2_match_map = matcher.mapping
    vf2_match_map = {key:vf2_match_map[key] for key in sorted(vf2_match_map.keys())}
    data['vf2_matchmap']=vf2_match_map
    vf2mapped = nx.relabel_nodes(mg,vf2_match_map,copy=True)
    data['vf2_matchmap_valid'] = nx.utils.graphs_equal(mg2,vf2mapped)
    #NAUTY Matching
    mg_canonical,mg_autgens,mg_canonical_map = nty.canonize_multigraph(mg) 
    mg2_canonical,mg2_autgens,mg2_canonical_map = nty.canonize_multigraph(mg2) 
    data['nauty_iso']=nx.utils.graphs_equal(mg_canonical,mg2_canonical)
    nauty_match_map = {val:mg2_canonical_map[key] for key,val in mg_canonical_map.items()}
    nauty_match_map = {key:nauty_match_map[key] for key in sorted(nauty_match_map.keys())}
    data['nauty_matchmap']=nauty_match_map
    nautymapped = nx.relabel_nodes(mg,nauty_match_map,copy=True)
    data['nauty_matchmap_valid'] = nx.utils.graphs_equal(mg2,nautymapped)
    #Check iso agreement
    iso_ok = (data['vf2_iso']==data['nauty_iso'])
    data['iso_ok'] = iso_ok
    assert iso_ok, "VF2 and NAUTYPY disagree on mg~mg2 isomorphism."
    #Check matchmap agreement
    data['matchmaps_equal'] = (vf2_match_map==nauty_match_map)
    data['matchmaps_aut_equiv'] = nx.utils.graphs_equal(vf2mapped,nautymapped)
    if data['vf2_iso']:
        matchmaps_ok = (data['matchmaps_aut_equiv'] and data['nauty_matchmap_valid'])
    else:
        matchmaps_ok = True
    data['matchmaps_ok']= matchmaps_ok
    assert matchmaps_ok, "Inconsistent mg->mg2 mappings."
    data['nauty_canmaps_eq'] = (mg_canonical_map==mg2_canonical_map)
    #Check aut equivalence of canmaps
    if len(mg_autgens)>0:
        mg_auts = [Permutation([aut[key] for key in sorted(aut.keys())]) for aut in mg_autgens]
        mg_autgp = PermutationGroup(mg_auts)
        mg2_auts = [Permutation([aut[key] for key in sorted(aut.keys())]) for aut in mg2_autgens]
        mg2_autgp = PermutationGroup(mg2_auts)
        n = mg_auts[0].size
        G = SymmetricGroup(n)
        mg_canonical_perm = Permutation(list(mg_canonical_map.values())) 
        mg2_canonical_perm = Permutation(list(mg2_canonical_map.values())) 
        canonical_corep = ~(G._coset_representative(~mg_canonical_perm, mg_autgp))
        perm_canonical_corep = ~(G._coset_representative(~mg2_canonical_perm, mg2_autgp))
        data['nauty_canmaps_aut_equiv'] = (canonical_corep==perm_canonical_corep)
    else:
        data['nauty_canmaps_aut_equiv'] = data['nauty_canmaps_eq']
    #If canmaps are unequal, check that they are not equivalent mod automorphism. 
    if not data['nauty_canmaps_eq']:
        canmaps_ok = not data['nauty_canmaps_aut_equiv']
    else:
        canmaps_ok = True
    data['canmaps_ok']=canmaps_ok
    assert canmaps_ok, "Automorphism ambiguity in NAUTYPY canonical mapping."

    if verbose:
        print(f"VF2:   Isomorphic?    {colstate(iso_q)}")
        print(f'NAUTY: Isomorphic?    {colstate(nx.utils.graphs_equal(mg_canonical,mg2_canonical))}')
        print(f'ISO_OK?   {colstate(iso_ok)}')
        print()
        print(f"Match Maps Equal?                {colstate(data['matchmaps_equal'])}")
        print(f"Maps Automorphism Equivalent?    {colstate(data['matchmaps_aut_equiv'])}")
        print(f"VF2 Mapping Valid?               {colstate(data['vf2_matchmap_valid'])}")
        print(f"NAUTY Mapping Valid?             {colstate(data['nauty_matchmap_valid'])}")
        print(f'VF2:   Match Map (mg->mg2)   {vf2_match_map}')
        print(f'NAUTY: Match Map (mg->mg2)   {nauty_match_map}')
        print(f"MATCHMAPS_OK?    {colstate(matchmaps_ok)}")
        print()
        print(f'mg  Canonical Map:    {mg_canonical_map}')
        print(f'mg2 Canonical Map:    {mg2_canonical_map}')
        print(f"NAUTY: Canonical Maps Equal?                      {colstate(data['nauty_canmaps_eq'])}")
        print(f"NAUTY: Canonical Maps Automorphism-Equivalent?    {colstate(data['nauty_canmaps_aut_equiv'])}")
        # print(f'mg_canonical_perm       : {[mg_canonical_perm(i) for i in range(n)]}')
        # print(f'mg2_canonical_perm  : {[mg2_canonical_perm(i) for i in range(n)]}')
        # print(f'canonical_corep         : {[canonical_corep(i) for i in range(n)]}')
        # print(f'perm_canonical_corep    : {[perm_canonical_corep(i) for i in range(n)]}')
        print(f'CANMAPS_OK?    {colstate(canmaps_ok)}')
        print()

    graphs=dict()
    graphs['A'] = mg
    graphs['B'] = mg2
    graphs['Ac'] = mg_canonical
    graphs['Bc'] = mg2_canonical

    state = iso_ok and matchmaps_ok and canmaps_ok

    return state,data,graphs
