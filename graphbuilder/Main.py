import pickle

import Measure
import Worker

root = '138875005' # SNOMED CT root concept (SNOMED CT Concept ID: 138875005)


def calculateSimilarity(ontology, measure_name, concept1, concept2):
    if measure_name == "WuPalmer":
        output = Measure.calculate_relatedness_WuPalmer(ontology=ontology, concept1=concept1, concept2=concept2)
    elif measure_name == "ChoiKim":
        output = Measure.calculate_relatedness_ChoiKim(ontology=ontology, concept1=concept1, concept2=concept2)
    elif measure_name == "LeacockChodorow":
        output = Measure.calculate_relatedness_LeacockChodorow(ontology=ontology, concept1=concept1, concept2=concept2)
    elif measure_name == "BatetSanchezValls":
        output = Measure.calculate_relatedness_BatetSanchezValls(ontology=ontology, concept1=concept1,
                                                                 concept2=concept2)
    elif measure_name == "Resnik":
        output = Measure.calculate_relatedness_Resnik(ontology=ontology, concept1=concept1, concept2=concept2)
    elif measure_name == "Lin":
        output = Measure.calculate_relatedness_Lin(ontology=ontology, concept1=concept1, concept2=concept2)
    elif measure_name == "JiangConrathDissimilarity":
        output = Measure.calculate_relatedness_JiangConrathDissimilarity(ontology=ontology, concept1=concept1,
                                                                         concept2=concept2)
    else:
        output = "Wrong measure name!"

    return output


def load_graph(file):
    with open(file, 'rb') as f:
        return pickle.load(f)


if __name__ == '__main__':
    ontology_graph_sim = load_graph('data/snomed-20250401_dag_is-a.pkl')
    ontology_graph_rel = load_graph('data/snomed-20250401_dag_rel.pkl')

    ontology = {
        "rel": ontology_graph_rel,
        "sim": ontology_graph_sim,
    }

    print('--- MAIN ---')
    #print(calculateSimilarity(ontology, 'BatetSanchezValls', '125605004', '284003005'))
    #print(calculateSimilarity(ontology, 'BatetSanchezValls', '125605004', '71388002'))

    #print(Worker.length_of_shortest_path(ontology['sim'], root, '125605004', '284003005'))
    #print(Worker.length_of_shortest_path(ontology['sim'], root, '404684003', '125605004'))

   # print(Worker.length_of_shortest_path(ontology['rel'], root, '363680008', '165197003')) # Radiographic Imaging procedure (procedure) -|> Imaging (procedure) -|> Evaluation procedure (procedure) <|- Diagnostic assessment (procedure) = distance 3 
    print(Worker.length_of_shortest_path(ontology['rel'], root, '363680008', '58147004')) # Radiographic Imaging procedure (procedure) --> "Clinical (qualifier value)" -> nonsense beispiel mit Wert 9 