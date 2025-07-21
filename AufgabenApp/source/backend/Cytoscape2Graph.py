#!/usr/bin/env python3
"""
Cytoscape2Graph.py - Konvertierung von Cytoscape.js-JSON zu NetworkX und Neo4j
Konvertiert editierte Cytoscape.js-Graphen zurück zu NetworkX-Graphen und Neo4j-Cypher-Statements
"""

import json
import uuid
import networkx as nx
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass


class CytoscapeElement:
    """Klasse für Cytoscape.js-Elemente"""
    
    def __init__(self, data: Dict[str, Any], classes: str = "", position: Optional[Dict[str, float]] = None, **kwargs):
        """Initialisiert Element und ignoriert unbekannte Felder"""
        self.data = data
        self.classes = classes
        self.position = position
        # Zusätzliche Felder ignorieren (z.B. 'group', 'selected', etc.)
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def is_node(self) -> bool:
        """Prüft ob Element ein Knoten ist"""
        return 'source' not in self.data and 'target' not in self.data
    
    def is_edge(self) -> bool:
        """Prüft ob Element eine Kante ist"""
        return 'source' in self.data and 'target' in self.data


class Cytoscape2GraphConverter:
    """Konvertiert Cytoscape.js-JSON zu NetworkX-Graphen und Neo4j-Cypher-Statements"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.elements = []
        self.nodes_data = {}
        self.edges_data = {}
    
    def load_cytoscape_json(self, filepath_or_data: Union[str, List[Dict[str, Any]]]) -> bool:
        """Lädt Cytoscape.js-JSON-Datei oder direkte Daten"""
        try:
            if isinstance(filepath_or_data, str):
                # Von Datei laden
                with open(filepath_or_data, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Prüfe Format
                if 'elements' in data and isinstance(data['elements'], list):
                    self.elements = data['elements']
                elif isinstance(data, list):
                    self.elements = data
                else:
                    print(f"❌ Unbekanntes JSON-Format in {filepath_or_data}")
                    return False
            else:
                # Direkte Daten
                self.elements = filepath_or_data
            
            print(f"✅ {len(self.elements)} Cytoscape-Elemente geladen")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Laden: {e}")
            return False
    
    def cytoscape_to_networkx(self) -> nx.DiGraph:
        """Konvertiert Cytoscape.js-Elemente zu NetworkX-Graph"""
        self.graph.clear()
        self.nodes_data.clear()
        self.edges_data.clear()
        
        # 1. Knoten hinzufügen
        for element in self.elements:
            cyto_elem = CytoscapeElement(**element)
            
            if cyto_elem.is_node():
                self._add_networkx_node(cyto_elem)
        
        # 2. Kanten hinzufügen
        for element in self.elements:
            cyto_elem = CytoscapeElement(**element)
            
            if cyto_elem.is_edge():
                self._add_networkx_edge(cyto_elem)
        
        print(f"🔄 NetworkX-Graph erstellt: {self.graph.number_of_nodes()} Knoten, {self.graph.number_of_edges()} Kanten")
        return self.graph
    
    def _add_networkx_node(self, element: CytoscapeElement):
        """Fügt Knoten zu NetworkX-Graph hinzu"""
        node_id = element.data.get('id')
        if not node_id:
            node_id = str(uuid.uuid4())
        
        # Node-Attribute aufbereiten
        node_attrs = {
            'name': element.data.get('label', element.data.get('name', str(node_id))),
            'node_type': element.data.get('type', 'unknown'),
            'description': element.data.get('description', ''),
            'status': element.data.get('status', 'pending'),
            'estimated_hours': element.data.get('estimated_hours', 0)
        }
        
        # Zusätzliche Cytoscape-spezifische Attribute
        if element.position:
            node_attrs['x'] = element.position.get('x', 0)
            node_attrs['y'] = element.position.get('y', 0)
        
        if element.classes:
            node_attrs['classes'] = element.classes
        
        # Icon-Information beibehalten
        if 'icon' in element.data:
            node_attrs['icon'] = element.data['icon']
        
        self.graph.add_node(node_id, **node_attrs)
        self.nodes_data[node_id] = node_attrs
    
    def _add_networkx_edge(self, element: CytoscapeElement):
        """Fügt Kante zu NetworkX-Graph hinzu"""
        source = element.data.get('source')
        target = element.data.get('target')
        
        if not source or not target:
            print(f"⚠️ Kante ohne Quelle/Ziel ignoriert: {element.data}")
            return
        
        # Edge-Attribute aufbereiten
        edge_attrs = {
            'relationship': element.data.get('relationship', 'RELATED_TO')
        }
        
        if element.classes:
            edge_attrs['classes'] = element.classes
        
        # Zusätzliche Edge-Daten
        for key, value in element.data.items():
            if key not in ['id', 'source', 'target', 'relationship']:
                edge_attrs[key] = value
        
        self.graph.add_edge(source, target, **edge_attrs)
        edge_id = element.data.get('id', f"{source}-{target}")
        self.edges_data[edge_id] = edge_attrs
    
    def cytoscape_to_cypher(self) -> List[str]:
        """Konvertiert Cytoscape.js-Elemente zu Neo4j-Cypher-Statements"""
        if not self.elements:
            print("❌ Keine Cytoscape-Elemente zum Konvertieren vorhanden")
            return []
        
        # Erst NetworkX erstellen um Daten zu strukturieren
        self.cytoscape_to_networkx()
        
        statements = []
        
        # 1. Knoten-Statements erstellen
        for node_id, node_data in self.nodes_data.items():
            cypher = self._create_node_cypher(node_id, node_data)
            statements.append(cypher)
        
        # 2. Beziehungs-Statements erstellen
        for edge_id, edge_data in self.edges_data.items():
            # Finde Source und Target für diese Edge
            source, target = None, None
            for element in self.elements:
                if element.get('data', {}).get('id') == edge_id:
                    source = element['data'].get('source')
                    target = element['data'].get('target')
                    break
            
            if source and target:
                cypher = self._create_relationship_cypher(source, target, edge_data)
                statements.append(cypher)
        
        print(f"🔄 {len(statements)} Cypher-Statements erstellt")
        return statements
    
    def _create_node_cypher(self, node_id: str, node_data: Dict[str, Any]) -> str:
        """Erstellt Cypher-Statement für Knoten"""
        node_type = node_data.get('node_type', 'UNKNOWN').upper()
        
        # Spezielle Behandlung für Ressourcen-Knoten
        if node_type in ['ACTOR', 'OBJECT', 'KNOWLEDGE', 'BUDGET']:
            label = f"RESOURCE:{node_type}"
        else:
            label = node_type
        
        # Eigenschaften für Cypher formatieren
        props = []
        for key, value in node_data.items():
            if key not in ['node_type', 'classes', 'x', 'y', 'icon'] and value is not None:
                if isinstance(value, str):
                    # Escape Anführungszeichen
                    escaped_value = value.replace('"', '\\"').replace('\n', '\\n')
                    props.append(f'{key}: "{escaped_value}"')
                elif isinstance(value, (int, float)):
                    props.append(f'{key}: {value}')
                elif isinstance(value, bool):
                    props.append(f'{key}: {str(value).lower()}')
        
        props_str = ", ".join(props)
        
        return f'CREATE (n:{label} {{{props_str}}})'
    
    def _create_relationship_cypher(self, source_id: str, target_id: str, edge_data: Dict[str, Any]) -> str:
        """Erstellt Cypher-Statement für Beziehungen"""
        relationship = edge_data.get('relationship', 'RELATED_TO').upper()
        
        # Zusätzliche Eigenschaften für Beziehung
        props = []
        for key, value in edge_data.items():
            if key not in ['relationship', 'classes'] and value is not None:
                if isinstance(value, str):
                    escaped_value = value.replace('"', '\\"').replace('\n', '\\n')
                    props.append(f'{key}: "{escaped_value}"')
                elif isinstance(value, (int, float)):
                    props.append(f'{key}: {value}')
        
        props_str = f" {{{', '.join(props)}}}" if props else ""
        
        return f'''MATCH (a), (b)
WHERE a.id = "{source_id}" AND b.id = "{target_id}"
CREATE (a)-[:{relationship}{props_str}]->(b)'''
    
    def export_networkx_to_file(self, output_file: str = "converted_graph.gpickle") -> str:
        """Exportiert NetworkX-Graph in Datei"""
        try:
            if not self.graph.nodes():
                print("❌ Kein Graph zum Exportieren vorhanden")
                return ""
            
            # Als Pickle exportieren für vollständige NetworkX-Kompatibilität
            nx.write_gpickle(self.graph, output_file)
            print(f"💾 NetworkX-Graph exportiert: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Fehler beim Exportieren: {e}")
            return ""
    
    def export_cypher_to_file(self, output_file: str = "graph_cypher.cyp") -> str:
        """Exportiert Cypher-Statements in Datei"""
        try:
            statements = self.cytoscape_to_cypher()
            
            if not statements:
                print("❌ Keine Cypher-Statements zum Exportieren vorhanden")
                return ""
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("// Automatisch generierte Cypher-Statements\n")
                f.write(f"// Erstellt am: {datetime.now().isoformat()}\n\n")
                
                for i, statement in enumerate(statements, 1):
                    f.write(f"// Statement {i}:\n")
                    f.write(statement.strip())
                    f.write(";\n\n")
            
            print(f"💾 Cypher-Statements exportiert: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Fehler beim Exportieren: {e}")
            return ""
    
    def get_conversion_summary(self) -> Dict[str, Any]:
        """Gibt Zusammenfassung der Konvertierung zurück"""
        node_types = {}
        edge_types = {}
        
        # Knoten-Typen zählen
        for node_data in self.nodes_data.values():
            node_type = node_data.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        # Edge-Typen zählen
        for edge_data in self.edges_data.values():
            edge_type = edge_data.get('relationship', 'RELATED_TO')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        return {
            'total_elements': len(self.elements),
            'nodes_count': len(self.nodes_data),
            'edges_count': len(self.edges_data),
            'node_types': node_types,
            'edge_types': edge_types,
            'networkx_nodes': self.graph.number_of_nodes(),
            'networkx_edges': self.graph.number_of_edges()
        }


def main():
    """Hauptfunktion für Tests und CLI-Verwendung"""
    print("🔄 Cytoscape.js zu Graph Konverter")
    print("=" * 40)
    
    # Datei-Input
    filepath = input("Geben Sie den Pfad zur Cytoscape.js-JSON-Datei ein: ").strip()
    
    if not filepath:
        print("❌ Kein Dateipfad angegeben!")
        return
    
    # Konverter erstellen
    converter = Cytoscape2GraphConverter()
    
    # JSON laden
    print(f"\n📄 Lade Cytoscape-Daten aus {filepath}...")
    if not converter.load_cytoscape_json(filepath):
        return
    
    # Konvertierungen durchführen
    print("\n🔄 Konvertiere zu NetworkX...")
    graph = converter.cytoscape_to_networkx()
    
    print("\n🔄 Generiere Cypher-Statements...")
    cypher_statements = converter.cytoscape_to_cypher()
    
    # Zusammenfassung anzeigen
    print("\n📊 Konvertierungs-Zusammenfassung:")
    summary = converter.get_conversion_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # Export-Optionen
    print("\n💾 Export-Optionen:")
    
    export_nx = input("NetworkX-Graph exportieren? (y/n): ").strip().lower()
    if export_nx in ['y', 'yes', 'ja']:
        nx_file = converter.export_networkx_to_file()
        if nx_file:
            print(f"✅ NetworkX exportiert: {nx_file}")
    
    export_cypher = input("Cypher-Statements exportieren? (y/n): ").strip().lower()
    if export_cypher in ['y', 'yes', 'ja']:
        cypher_file = converter.export_cypher_to_file()
        if cypher_file:
            print(f"✅ Cypher exportiert: {cypher_file}")
    
    # Cypher-Statements anzeigen (erste 3)
    print(f"\n🔗 Erste {min(3, len(cypher_statements))} Cypher-Statements:")
    for i, statement in enumerate(cypher_statements[:3], 1):
        print(f"\n-- Statement {i}:")
        print(statement.strip())
    
    if len(cypher_statements) > 3:
        print(f"\n... und {len(cypher_statements) - 3} weitere Statements")
    
    print(f"\n✅ Konvertierung abgeschlossen!")


if __name__ == "__main__":
    main()