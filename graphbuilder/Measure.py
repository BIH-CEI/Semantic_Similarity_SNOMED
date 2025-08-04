import Worker
from Worker import *

root = '138875005'

def calculate_relatedness_WuPalmer(ontology, concept1, concept2):
    graph_sim = ontology["sim"]     # LCA must be some hierarchy
    lca = Worker.get_lowest_common_ancestor(graph_sim, root, concept1, concept2)
    n1 = Worker.length_of_shortest_path(graph_sim, root, lca, concept1)
    n2 = Worker.length_of_shortest_path(graph_sim, root, lca, concept2)
    n3 = Worker.length_of_shortest_path(graph_sim, root, lca, root)

    result = (2 * n3) / (n1 + n2 + 2 * n3)
    return result


def calculate_relatedness_ChoiKim(ontology, concept1, concept2):
    graph_sim = ontology["sim"]
    max_level = nx.dag_longest_path_length(graph_sim)
    max_path = max_level - 1
    path_len = Worker.length_of_shortest_path(graph_sim, root, concept1, concept2)
    level_difference = Worker.level_difference(graph_sim, root, concept1, concept2)

    result = ((max_path - path_len) / max_path) * ((max_level - level_difference) / max_level)
    return result


def calculate_relatedness_LeacockChodorow(ontology, concept1, concept2):
    graph_sim = ontology["rel"]
    max_depth = nx.dag_longest_path_length(graph_sim)
    # +2: "number of nodes, including themselves"
    result = -math.log((Worker.length_of_shortest_path(graph_sim, root, concept1, concept2) + 2) / (2 * max_depth))
    return result


def calculate_relatedness_BatetSanchezValls(ontology, concept1, concept2):

    graph_sim = ontology["rel"]
    # super concepts of concept1 and concept itself, use nx.descants to get ancestors
    super_concept_c1 = list(set(nx.descendants(graph_sim, concept1)))
    super_concept_c1.append(concept1)
    # super concepts of concept2 and concept itself, use nx.descants to get ancestors
    super_concept_c2 = list(set(nx.descendants(graph_sim, concept2)))
    super_concept_c2.append(concept2)

    all_super_concepts = {}
    for i in super_concept_c1:
        all_super_concepts[i] = 1

    for i in super_concept_c2:
        if all_super_concepts.get(i) is not None:
            all_super_concepts[i] = all_super_concepts[i] + 1
        else:
            all_super_concepts[i] = 1

    # common super concepts -- freq of dict is > 1 (b.c. concept is super concept of both)
    common_super_concept = []

    # split all_super_concepts into common-list and non-common
    for i in all_super_concepts:
        if all_super_concepts[i] > 1:
            common_super_concept.append(i)

    non_common_super_concept = len(all_super_concepts) - len(common_super_concept)
    # calculation
    x = (non_common_super_concept) / len(all_super_concepts)

    result = -1 * float(math.log2(x) if x != 0 else -math.inf)
    return result


def calculate_relatedness_Resnik(ontology, concept1, concept2):
    graph_sim = ontology["sim"]
    graph_rel = ontology["rel"]
    lca = Worker.get_lowest_common_ancestor(graph_sim, root, concept1, concept2)
    if lca == root:
        result = 0.0
    else:
        result = Worker.calculating_information_content(graph_rel, len(list(graph_rel)), lca)
    return result


def calculate_relatedness_Lin(ontology, concept1, concept2):
    graph_rel = ontology["rel"]
    sim_resnik = calculate_relatedness_Resnik(ontology, concept1, concept2)
    result = (2 * sim_resnik) / (Worker.calculating_information_content(graph_rel, len(list(graph_rel)), concept1) + Worker.calculating_information_content(graph_rel, len(list(graph_rel)), concept2))
    return result


def calculate_relatedness_JiangConrathDissimilarity(ontology, concept1, concept2):
    graph_rel = ontology["rel"]
    sim_resnik = calculate_relatedness_Resnik(ontology, concept1, concept2)
    result = Worker.calculating_information_content(graph_rel, len(list(graph_rel)), concept1) + Worker.calculating_information_content(graph_rel, len(list(graph_rel)), concept2) - 2 * sim_resnik
    return result

