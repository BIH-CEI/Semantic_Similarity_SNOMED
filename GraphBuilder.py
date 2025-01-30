import networkx as nx
import pickle


def builtEdge(graph, lines, without_attribute_relation):
    for line in lines:
        parts = line.split("	")
        # parts = line.split(";")
        active = parts[2]
        focus_concept = parts[4]
        attribute_value = parts[5]
        relation_type = parts[7]
        if without_attribute_relation:
            b = (active == '1' and relation_type == '116680003')
        else:
            b = (active == '1')
        if b:

            if not graph.has_edge(focus_concept, attribute_value):
                graph.add_edge(focus_concept, attribute_value, label=relation_type)
    return graph


def builtNode(graph, lines):
    for line in lines:
        parts = line.split("	")
        node = parts[0]
        active = parts[2]
        if active == '1':
            graph.add_node(node)
    return graph


def createGraph(name, without_attribute_relation):
    file0 = open('data/sct2_Concept_Snapshot_INT_20230430.txt', 'r')
    Lines0 = file0.readlines()
    file1 = open('data/sct2_Relationship_Snapshot_INT_20230430.txt', 'r')
    Lines1 = file1.readlines()
    #file2 = open('data/sct2_RelationshipConcreteValues_Snapshot_INT_20230430.txt', 'r')
    #Lines2 = file2.readlines()

    graph = nx.DiGraph()
    graph = builtNode(graph, Lines0)
    graph = builtEdge(graph, Lines1, without_attribute_relation)
    #graph = builtEdge(graph, Lines2, without_attribute_relation)

    with open(name + ".pkl", "wb") as f:
        pickle.dump(graph, f)
    print(graph)


if __name__ == '__main__':
    print("--GRAPH BUILDER--")

    createGraph('snomed-20230430_dag_is-a', True)
    createGraph('snomed-20230430_dag_rel', False)

    print("--FINISH--")
