import json
import math

import networkx as nx

def find_shortest_path(ontology, root, start, end):
    lca = get_lowest_common_ancestor(ontology, root, end, start)
    if lca == end:
        return nx.shortest_path(ontology, start, end)
    elif lca == start:
        return nx.shortest_path(ontology, end, start)
    else:
        path_to_lca = nx.shortest_path(ontology, end, lca)
        path_from_lca = nx.shortest_path(ontology, start, lca)
        path_from_lca.remove(lca)
        path_from_lca.reverse()
        return path_to_lca + path_from_lca


def find_longest_path(ontology, root, start, end):
    lca = get_lowest_common_ancestor(ontology, root, start, end)
    if lca == start or lca == end:
        return __find_longest_path(list(nx.all_simple_paths(ontology, start, end)))
    else:
        path_to_lca = __find_longest_path(list(nx.all_simple_paths(ontology, lca, start)))
        path_from_lca = __find_longest_path(list(nx.all_simple_paths(ontology, lca, end)))
        path_from_lca.remove(lca)
        path_from_lca.reverse()
        return path_to_lca + path_from_lca


def __find_longest_path(paths):
    paths.sort(key=len)
    if len(paths) > 0:
        return paths[-1]
    else:
        return None


def length_of_shortest_path(ontology, root, start, end):
    return len(find_shortest_path(ontology, root, end, start)) - 1


def calculate_depth(ontology, root, concept):
    if concept == root:
        return 0
    else:
        return length_of_shortest_path(ontology, root, root, concept)


def get_max_node_identifier(ontology):
    return max([int(x) for x in list(ontology)])


def calculate_common_specificity(ontology, root, cluster, concept1, concept2):
    lca = get_lowest_common_ancestor(ontology, root, concept1, concept2)
    lca_depth = calculate_depth(ontology, root, lca)
    return cluster.depth - lca_depth


def level_difference(ontology, root, concept1, concept2):
    concept1_root = length_of_shortest_path(ontology, root, concept1, root)
    concept2_root = length_of_shortest_path(ontology, root, concept2, root)
    return abs(concept1_root - concept2_root)


def get_lowest_common_ancestor(ontology, root, concept1, concept2):
    step = float('inf')
    candidates = []
    an1 = nx.descendants(ontology, concept1)    # to get the ancestors
    an2 = nx.descendants(ontology, concept2)
    an2.add(concept2)

    z = [an1, an2]
    z1 = set.intersection(*map(set, z))

    for commonNode in z1:
        x = nx.shortest_path_length(ontology, concept1, commonNode) + \
            nx.shortest_path_length(ontology, concept2, commonNode)
        if step > x:
            step = x
            candidates = [commonNode]
        elif step == x:
            step = x
            candidates.append(commonNode)

    result = list(set(candidates))
    return result[0]


def get_all_ancestors(ontology, root, concept):
    return nx.shortest_path(ontology, concept, root)


def calculating_information_content(ontology, number_of_concepts, concept):
    # number of subsumers of concept
    number_subsumers = len(nx.ancestors(ontology, concept))
    # probability p(c)
    p = float(number_subsumers / (number_of_concepts))
    # IC
    ic = -1 * float(math.log2(p) if p != 0 else -math.inf)
    return ic

