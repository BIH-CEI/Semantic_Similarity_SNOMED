Übernommen und modifiziert von https://github.com/skfit-uni-luebeck/semantic-similarity 

### `GraphBuilder.py`

- Erstellen des Graphen
- Download einer SNOMED CT-Version (RF2)
- Benötigte Dateien in den Ordner `data` legen:
   - `sct2_Concept_Snapshot_INT_xxxxxxxx.txt`
   - `sct2_Relationship_Snapshot_INT_xxxxxxxx.txt`
   - `sct2_RelationshipConcreteValues_Snapshot_INT_xxxxxxxx.txt`
- Zwei Arten von Graphen möglich - immer die Richtungsabhänigkeit beachten
- Werden gespeichert für spätere Verwendung

#### 1. Graph mit nur *is-a-Relationen*

- Beim Erstellen des Graphen darauf achten, dass nur der Relationstyp **116680003 (`is-a`)** verwendet wird.

#### 2. Graph mit *allen Relationen*

- Enthält neben den *is-a*-Relationen auch alle Attributrelationen.
- Diese Variante kann zu spannenden Verbindungen durch Attributrelationen führen. 😉


### `Measures.py`
- Für mein Projekt war die Berechnung der Semantic Similarity zwischen 2 Konzepten relevant
- Verschiedene Ansätz aus Literatur implementiert
- Publikation: 10.1016/j.jbi.2010.09.002


### `Worker.py`
- Hilfsmethoden für die Berechnung der Semantic Similarity, wie Pfadlängen 