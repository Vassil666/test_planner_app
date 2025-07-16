#!/usr/bin/env python3
"""
Plan2Graph.py - Konvertierung von JSON-Plänen zu Graphstrukturen
Wandelt generierte Pläne in NetworkX-Graphen und Cypher-Statements um
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple
import networkx as nx
from dataclasses import dataclass, asdict


@dataclass
class GraphNode:
    """Datenklasse für Graph-Knoten"""
    id: str
    name: str
    node_type: str  # 'objective', 'project', 'task'
    description: str = ""
    status: str = "pending"
    start_time: str = ""
    end_time: str = ""
    estimated_hours: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResourceNode:
    """Datenklasse für Ressourcen-Knoten"""
    id: str
    name: str
    resource_type: str  # 'actor', 'object', 'knowledge', 'budget'
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PlanGraphConverter:
    """Konvertiert JSON-Pläne zu NetworkX-Graphen und Cypher-Statements"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = {}
        self.resources = {}
        
    def json_to_networkx(self, plan_json: Dict[str, Any]) -> nx.DiGraph:
        """Konvertiert JSON-Plan zu NetworkX-Graph"""
        self.graph.clear()
        self.nodes.clear()
        self.resources.clear()
        
        # 1. Haupt-Ziel erstellen
        objective_id = str(uuid.uuid4())
        objective = GraphNode(
            id=objective_id,
            name=plan_json.get("objective", "Unbekanntes Ziel"),
            node_type="objective",
            description=plan_json.get("objective", "")
        )
        
        self.nodes[objective_id] = objective
        self.graph.add_node(objective_id, **objective.to_dict())
        
        # 2. Projekte hinzufügen
        projects = plan_json.get("projects", [])
        for project_data in projects:
            project_id = self._add_project(project_data, objective_id)
            
            # 3. Tasks für jedes Projekt hinzufügen
            tasks = project_data.get("tasks", [])
            task_ids = []
            
            for task_data in tasks:
                task_id = self._add_task(task_data, project_id)
                task_ids.append(task_id)
                
                # 4. Ressourcen für Task hinzufügen
                self._add_resources(task_data.get("resources", {}), task_id)
            
            # 5. Task-Abhängigkeiten erstellen
            self._create_task_dependencies(tasks, task_ids)
        
        return self.graph
    
    def _add_project(self, project_data: Dict[str, Any], objective_id: str) -> str:
        """Fügt Projekt-Knoten hinzu"""
        project_id = str(uuid.uuid4())
        project = GraphNode(
            id=project_id,
            name=project_data.get("name", "Unbekanntes Projekt"),
            node_type="project",
            description=project_data.get("description", "")
        )
        
        self.nodes[project_id] = project
        self.graph.add_node(project_id, **project.to_dict())
        
        # Verbindung vom Ziel zum Projekt
        self.graph.add_edge(objective_id, project_id, relationship="CONTAINS")
        
        return project_id
    
    def _add_task(self, task_data: Dict[str, Any], project_id: str) -> str:
        """Fügt Task-Knoten hinzu"""
        task_id = str(uuid.uuid4())
        task = GraphNode(
            id=task_id,
            name=task_data.get("name", "Unbekannte Aufgabe"),
            node_type="task",
            description=task_data.get("description", ""),
            estimated_hours=task_data.get("estimated_hours", 0)
        )
        
        self.nodes[task_id] = task
        self.graph.add_node(task_id, **task.to_dict())
        
        # Verbindung vom Projekt zur Aufgabe
        self.graph.add_edge(project_id, task_id, relationship="CONTAINS")
        
        return task_id
    
    def _add_resources(self, resources_data: Dict[str, Any], task_id: str):
        """Fügt Ressourcen-Knoten hinzu und verbindet sie mit Tasks"""
        resource_types = {
            "actors": "actor",
            "objects": "object", 
            "knowledge": "knowledge",
            "budget": "budget"
        }
        
        for res_type, res_list in resources_data.items():
            if res_type == "budget" and isinstance(res_list, (int, float)):
                # Budget als einzelner Wert
                if res_list > 0:
                    resource_id = str(uuid.uuid4())
                    resource = ResourceNode(
                        id=resource_id,
                        name=f"Budget: {res_list}€",
                        resource_type="budget",
                        description=f"Budgetbedarf: {res_list}€"
                    )
                    
                    self.resources[resource_id] = resource
                    self.graph.add_node(resource_id, **resource.to_dict())
                    self.graph.add_edge(task_id, resource_id, relationship="REQUIRES")
                    
            elif isinstance(res_list, list):
                # Listen von Ressourcen
                for resource_name in res_list:
                    if resource_name and resource_name.strip():
                        resource_id = str(uuid.uuid4())
                        resource = ResourceNode(
                            id=resource_id,
                            name=resource_name.strip(),
                            resource_type=resource_types.get(res_type, "unknown"),
                            description=f"{resource_types.get(res_type, 'Resource')}: {resource_name}"
                        )
                        
                        self.resources[resource_id] = resource
                        self.graph.add_node(resource_id, **resource.to_dict())
                        self.graph.add_edge(task_id, resource_id, relationship="REQUIRES")
    
    def _create_task_dependencies(self, tasks: List[Dict], task_ids: List[str]):
        """Erstellt Abhängigkeiten zwischen Tasks"""
        task_name_to_id = {}
        for i, task_data in enumerate(tasks):
            task_name = task_data.get("name", "")
            if task_name:
                task_name_to_id[task_name] = task_ids[i]
        
        for i, task_data in enumerate(tasks):
            dependencies = task_data.get("dependencies", [])
            current_task_id = task_ids[i]
            
            for dep_name in dependencies:
                if dep_name in task_name_to_id:
                    dep_task_id = task_name_to_id[dep_name]
                    # Abhängigkeit: dep_task -> current_task
                    self.graph.add_edge(dep_task_id, current_task_id, relationship="PRECEDES")
    
    def generate_cypher_statements(self) -> List[str]:
        """Generiert Cypher INSERT-Statements für Neo4j"""
        statements = []
        
        # 1. Knoten erstellen
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("node_type") in ["objective", "project", "task"]:
                # Hauptknoten (Ziele, Projekte, Tasks)
                cypher = self._create_node_cypher(node_id, node_data)
                statements.append(cypher)
            elif node_data.get("resource_type"):
                # Ressourcen-Knoten
                cypher = self._create_resource_cypher(node_id, node_data)
                statements.append(cypher)
        
        # 2. Beziehungen erstellen
        for source, target, edge_data in self.graph.edges(data=True):
            cypher = self._create_relationship_cypher(source, target, edge_data)
            statements.append(cypher)
        
        return statements
    
    def _create_node_cypher(self, node_id: str, node_data: Dict[str, Any]) -> str:
        """Erstellt Cypher-Statement für Hauptknoten"""
        node_type = node_data.get("node_type", "").upper()
        
        # Eigenschaften für Cypher formatieren
        props = []
        for key, value in node_data.items():
            if key not in ["node_type"] and value:
                if isinstance(value, str):
                    props.append(f'{key}: "{value}"')
                else:
                    props.append(f'{key}: {value}')
        
        props_str = ", ".join(props)
        
        return f'CREATE (n:{node_type} {{{props_str}}})'
    
    def _create_resource_cypher(self, resource_id: str, resource_data: Dict[str, Any]) -> str:
        """Erstellt Cypher-Statement für Ressourcen"""
        resource_type = resource_data.get("resource_type", "").upper()
        
        # Eigenschaften für Cypher formatieren
        props = []
        for key, value in resource_data.items():
            if key not in ["resource_type"] and value:
                if isinstance(value, str):
                    props.append(f'{key}: "{value}"')
                else:
                    props.append(f'{key}: {value}')
        
        props_str = ", ".join(props)
        
        return f'CREATE (r:RESOURCE:{resource_type} {{{props_str}}})'
    
    def _create_relationship_cypher(self, source_id: str, target_id: str, edge_data: Dict[str, Any]) -> str:
        """Erstellt Cypher-Statement für Beziehungen"""
        relationship = edge_data.get("relationship", "RELATED_TO")
        
        return f'''
MATCH (a), (b)
WHERE a.id = "{source_id}" AND b.id = "{target_id}"
CREATE (a)-[:{relationship}]->(b)
'''
    
    def export_graph_info(self) -> Dict[str, Any]:
        """Exportiert Graph-Informationen für Debugging"""
        return {
            "nodes_count": self.graph.number_of_nodes(),
            "edges_count": self.graph.number_of_edges(),
            "node_types": {
                node_data.get("node_type", "unknown"): len([
                    n for n, d in self.graph.nodes(data=True) 
                    if d.get("node_type") == node_data.get("node_type")
                ])
                for _, node_data in self.graph.nodes(data=True)
            },
            "nodes": [
                {
                    "id": node_id,
                    "name": node_data.get("name", ""),
                    "type": node_data.get("node_type", node_data.get("resource_type", "unknown"))
                }
                for node_id, node_data in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "relationship": edge_data.get("relationship", "RELATED_TO")
                }
                for source, target, edge_data in self.graph.edges(data=True)
            ]
        }


def get_sample_plan() -> Dict[str, Any]:
    """Gibt einen Beispiel-JSON-Plan zurück"""
    return {
        "objective": "Website-Relaunch durchführen",
        "projects": [
            {
                "name": "Frontend-Entwicklung",
                "description": "Neue Benutzeroberfläche entwickeln",
                "tasks": [
                    {
                        "name": "Design erstellen",
                        "description": "UI/UX-Design für neue Website",
                        "estimated_hours": 40,
                        "dependencies": [],
                        "resources": {
                            "actors": ["UI/UX Designer"],
                            "objects": ["Figma", "Design-System"],
                            "knowledge": ["Design Principles"],
                            "budget": 5000
                        }
                    },
                    {
                        "name": "Frontend implementieren",
                        "description": "React-Frontend entwickeln",
                        "estimated_hours": 80,
                        "dependencies": ["Design erstellen"],
                        "resources": {
                            "actors": ["Frontend Developer"],
                            "objects": ["React", "TypeScript"],
                            "knowledge": ["Web Development"],
                            "budget": 8000
                        }
                    }
                ]
            }
        ]
    }


def load_plan_from_file(filepath: str) -> Dict[str, Any]:
    """Lädt einen JSON-Plan aus einer Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Datei nicht gefunden: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ JSON-Fehler: {e}")
        return {}
    except Exception as e:
        print(f"❌ Fehler beim Laden: {e}")
        return {}


def main():
    """Hauptfunktion"""
    print("📋 Plan zu Graph Konverter")
    print("=" * 40)
    
    # Frage nach Eingabetyp
    print("\nOptionen:")
    print("1. Beispiel-Plan verwenden")
    print("2. JSON-Datei laden")
    
    choice = input("Wählen Sie eine Option (1-2): ").strip()
    
    if choice == "1":
        print("📄 Verwende Beispiel-Plan...")
        plan = get_sample_plan()
    elif choice == "2":
        filepath = input("Geben Sie den Pfad zur JSON-Datei ein: ").strip()
        if not filepath:
            print("❌ Kein Dateipfad angegeben!")
            return
        
        print(f"📄 Lade Plan aus {filepath}...")
        plan = load_plan_from_file(filepath)
        
        if not plan:
            print("❌ Konnte Plan nicht laden!")
            return
    else:
        print("❌ Ungültige Auswahl!")
        return
    
    # Konverter testen
    converter = PlanGraphConverter()
    
    print("\n🔄 Konvertiere JSON zu NetworkX Graph...")
    graph = converter.json_to_networkx(plan)
    
    print("\n📊 Graph-Informationen:")
    info = converter.export_graph_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))
    
    print("\n🔗 Cypher-Statements:")
    cypher_statements = converter.generate_cypher_statements()
    for i, statement in enumerate(cypher_statements, 1):
        print(f"\n-- Statement {i}:")
        print(statement.strip())


if __name__ == "__main__":
    main()