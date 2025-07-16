#!/usr/bin/env python3
"""
GraphShow.py - Visualisierung von NetworkX-Graphen
Stellt verschiedene Methoden zur Darstellung von Projekt-Graphen bereit
"""

import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
import json
from dataclasses import dataclass
from Plan2Graph import PlanGraphConverter, load_plan_from_file, get_sample_plan


@dataclass
class GraphStyle:
    """Konfiguration für Graph-Styling"""
    node_colors: Dict[str, str]
    node_sizes: Dict[str, int]
    edge_colors: Dict[str, str]
    layout: str = "spring"
    
    @classmethod
    def default(cls):
        return cls(
            node_colors={
                "objective": "#FF6B6B",    # Rot für Ziele
                "project": "#4ECDC4",      # Türkis für Projekte  
                "task": "#45B7D1",         # Blau für Tasks
                "actor": "#96CEB4",        # Grün für Akteure
                "object": "#FFEAA7",       # Gelb für Objekte
                "knowledge": "#DDA0DD",    # Lila für Wissen
                "budget": "#F39C12"        # Orange für Budget
            },
            node_sizes={
                "objective": 1500,
                "project": 1000,
                "task": 800,
                "actor": 600,
                "object": 600,
                "knowledge": 600,
                "budget": 600
            },
            edge_colors={
                "CONTAINS": "#2C3E50",     # Dunkelblau für Hierarchie
                "REQUIRES": "#E74C3C",     # Rot für Abhängigkeiten
                "PRECEDES": "#9B59B6"      # Lila für Reihenfolge
            }
        )


class GraphVisualizer:
    """Klasse für die Visualisierung von NetworkX-Graphen"""
    
    def __init__(self, style: Optional[GraphStyle] = None):
        self.style = style if style else GraphStyle.default()
        
    def show_matplotlib(self, graph: nx.DiGraph, layout: str = "spring", 
                       figsize: Tuple[int, int] = (15, 10), 
                       save_path: Optional[str] = None) -> None:
        """Zeigt Graph mit Matplotlib an"""
        
        plt.figure(figsize=figsize)
        
        # Layout berechnen
        pos = self._get_layout(graph, layout)
        
        # Knoten nach Typ gruppieren
        node_groups = self._group_nodes_by_type(graph)
        
        # Knoten zeichnen
        for node_type, nodes in node_groups.items():
            if nodes:
                nx.draw_networkx_nodes(
                    graph, pos, 
                    nodelist=nodes,
                    node_color=self.style.node_colors.get(node_type, "#CCCCCC"),
                    node_size=self.style.node_sizes.get(node_type, 500),
                    alpha=0.8,
                    label=node_type.capitalize()
                )
        
        # Kanten nach Beziehungstyp zeichnen
        edge_groups = self._group_edges_by_relationship(graph)
        
        for relationship, edges in edge_groups.items():
            if edges:
                nx.draw_networkx_edges(
                    graph, pos,
                    edgelist=edges,
                    edge_color=self.style.edge_colors.get(relationship, "#CCCCCC"),
                    alpha=0.6,
                    arrows=True,
                    arrowsize=20,
                    width=2
                )
        
        # Labels hinzufügen
        labels = {node: data.get("name", node)[:20] + "..." 
                 if len(data.get("name", node)) > 20 
                 else data.get("name", node)
                 for node, data in graph.nodes(data=True)}
        
        nx.draw_networkx_labels(graph, pos, labels, font_size=8, font_weight="bold")
        
        plt.title("Projekt-Graph Visualisierung", size=16, weight="bold")
        plt.legend(scatterpoints=1, loc="upper left", bbox_to_anchor=(1, 1))
        plt.axis("off")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"📊 Graph gespeichert: {save_path}")
        
        plt.show()
    
    def show_plotly_interactive(self, graph: nx.DiGraph, layout: str = "spring",
                               save_html: Optional[str] = None) -> go.Figure:
        """Erstellt interaktive Plotly-Visualisierung"""
        
        # Layout berechnen
        pos = self._get_layout(graph, layout)
        
        # Kanten-Traces
        edge_traces = []
        edge_groups = self._group_edges_by_relationship(graph)
        
        for relationship, edges in edge_groups.items():
            if not edges:
                continue
                
            edge_x, edge_y = [], []
            for edge in edges:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color=self.style.edge_colors.get(relationship, "#CCCCCC")),
                hoverinfo='none',
                mode='lines',
                name=f"{relationship} Edges",
                showlegend=True
            )
            edge_traces.append(edge_trace)
        
        # Knoten-Traces
        node_traces = []
        node_groups = self._group_nodes_by_type(graph)
        
        for node_type, nodes in node_groups.items():
            if not nodes:
                continue
                
            node_x = [pos[node][0] for node in nodes]
            node_y = [pos[node][1] for node in nodes]
            
            # Hover-Informationen
            hover_text = []
            for node in nodes:
                data = graph.nodes[node]
                text = f"<b>{data.get('name', 'Unbekannt')}</b><br>"
                text += f"Typ: {node_type}<br>"
                if data.get('description'):
                    text += f"Beschreibung: {data['description'][:100]}...<br>"
                if data.get('estimated_hours'):
                    text += f"Geschätzte Stunden: {data['estimated_hours']}<br>"
                if data.get('status'):
                    text += f"Status: {data['status']}"
                hover_text.append(text)
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hovertemplate='%{text}<extra></extra>',
                text=hover_text,
                textposition="middle center",
                marker=dict(
                    size=[self.style.node_sizes.get(node_type, 500) / 30 for _ in nodes],
                    color=self.style.node_colors.get(node_type, "#CCCCCC"),
                    line=dict(width=2, color="black")
                ),
                name=f"{node_type.capitalize()} Nodes",
                showlegend=True
            )
            node_traces.append(node_trace)
        
        # Figure erstellen
        fig = go.Figure(data=edge_traces + node_traces,
                       layout=go.Layout(
                           title="Interaktiver Projekt-Graph",
                           titlefont_size=16,
                           showlegend=True,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Klicken und ziehen Sie die Knoten zur Interaktion",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor="left", yanchor="bottom",
                               font=dict(color="#000000", size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                       ))
        
        if save_html:
            fig.write_html(save_html)
            print(f"📊 Interaktiver Graph gespeichert: {save_html}")
        
        fig.show()
        return fig
    
    def create_hierarchical_view(self, graph: nx.DiGraph) -> go.Figure:
        """Erstellt hierarchische Baum-Ansicht"""
        
        # Hierarchie-Layout für bessere Darstellung
        pos = nx.nx_agraph.graphviz_layout(graph, prog='dot') if hasattr(nx, 'nx_agraph') else self._get_layout(graph, "hierarchical")
        
        # Ebenen identifizieren
        levels = {}
        for node, data in graph.nodes(data=True):
            node_type = data.get('node_type', data.get('resource_type', 'unknown'))
            if node_type == 'objective':
                levels[node] = 0
            elif node_type == 'project':
                levels[node] = 1
            elif node_type == 'task':
                levels[node] = 2
            else:
                levels[node] = 3
        
        # Positionen nach Ebenen anordnen
        pos_hierarchical = {}
        level_counts = {}
        
        for node, level in levels.items():
            if level not in level_counts:
                level_counts[level] = 0
            
            x = level_counts[level] * 200
            y = -level * 150
            pos_hierarchical[node] = (x, y)
            level_counts[level] += 1
        
        return self.show_plotly_interactive(graph, layout="custom")
    
    def export_graph_stats(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Exportiert Graph-Statistiken"""
        
        node_types = {}
        for _, data in graph.nodes(data=True):
            node_type = data.get('node_type', data.get('resource_type', 'unknown'))
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        relationship_types = {}
        for _, _, data in graph.edges(data=True):
            rel_type = data.get('relationship', 'unknown')
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        return {
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "node_types": node_types,
            "relationship_types": relationship_types,
            "graph_density": nx.density(graph),
            "is_connected": nx.is_weakly_connected(graph),
            "number_of_components": nx.number_weakly_connected_components(graph)
        }
    
    def _get_layout(self, graph: nx.DiGraph, layout: str) -> Dict:
        """Berechnet Layout-Positionen"""
        
        layouts = {
            "spring": lambda g: nx.spring_layout(g, k=3, iterations=50),
            "circular": lambda g: nx.circular_layout(g),
            "random": lambda g: nx.random_layout(g),
            "shell": lambda g: nx.shell_layout(g),
            "hierarchical": lambda g: self._hierarchical_layout(g)
        }
        
        if layout in layouts:
            return layouts[layout](graph)
        else:
            return nx.spring_layout(graph, k=3, iterations=50)
    
    def _hierarchical_layout(self, graph: nx.DiGraph) -> Dict:
        """Erstellt hierarchisches Layout basierend auf Knotentypen"""
        pos = {}
        
        # Knoten nach Typ gruppieren
        levels = {
            "objective": 0,
            "project": 1, 
            "task": 2,
            "actor": 3,
            "object": 3,
            "knowledge": 3,
            "budget": 3
        }
        
        level_nodes = {}
        for node, data in graph.nodes(data=True):
            node_type = data.get('node_type', data.get('resource_type', 'unknown'))
            level = levels.get(node_type, 4)
            
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        # Positionen zuweisen
        for level, nodes in level_nodes.items():
            for i, node in enumerate(nodes):
                x = i * 2 - len(nodes)
                y = -level * 2
                pos[node] = (x, y)
        
        return pos
    
    def _group_nodes_by_type(self, graph: nx.DiGraph) -> Dict[str, List]:
        """Gruppiert Knoten nach Typ"""
        groups = {}
        
        for node, data in graph.nodes(data=True):
            node_type = data.get('node_type', data.get('resource_type', 'unknown'))
            if node_type not in groups:
                groups[node_type] = []
            groups[node_type].append(node)
        
        return groups
    
    def _group_edges_by_relationship(self, graph: nx.DiGraph) -> Dict[str, List]:
        """Gruppiert Kanten nach Beziehungstyp"""
        groups = {}
        
        for source, target, data in graph.edges(data=True):
            relationship = data.get('relationship', 'unknown')
            if relationship not in groups:
                groups[relationship] = []
            groups[relationship].append((source, target))
        
        return groups


def create_test_graph() -> nx.DiGraph:
    """Erstellt einen einfachen Test-Graph"""
    test_graph = nx.DiGraph()
    
    # Knoten hinzufügen
    test_graph.add_node("obj1", name="Website Relaunch", node_type="objective")
    test_graph.add_node("proj1", name="Frontend", node_type="project")
    test_graph.add_node("task1", name="Design", node_type="task")
    test_graph.add_node("task2", name="Implementation", node_type="task")
    test_graph.add_node("res1", name="Designer", resource_type="actor")
    
    # Kanten hinzufügen
    test_graph.add_edge("obj1", "proj1", relationship="CONTAINS")
    test_graph.add_edge("proj1", "task1", relationship="CONTAINS")
    test_graph.add_edge("proj1", "task2", relationship="CONTAINS")
    test_graph.add_edge("task1", "task2", relationship="PRECEDES")
    test_graph.add_edge("task1", "res1", relationship="REQUIRES")
    
    return test_graph


def main():
    """Hauptfunktion für Graph-Visualisierung"""
    print("📊 Graph Visualisierung")
    print("=" * 40)
    
    # Optionen für Graph-Quelle
    print("\nOptionen:")
    print("1. Test-Graph verwenden")
    print("2. Beispiel-Plan verwenden")
    print("3. JSON-Datei laden")
    
    choice = input("Wählen Sie eine Option (1-3): ").strip()
    
    if choice == "1":
        print("🧪 Verwende Test-Graph...")
        graph = create_test_graph()
        
    elif choice == "2":
        print("📄 Verwende Beispiel-Plan...")
        plan = get_sample_plan()
        converter = PlanGraphConverter()
        graph = converter.json_to_networkx(plan)
        
    elif choice == "3":
        filepath = input("Geben Sie den Pfad zur JSON-Datei ein: ").strip()
        if not filepath:
            print("❌ Kein Dateipfad angegeben!")
            return
        
        print(f"📄 Lade Plan aus {filepath}...")
        plan = load_plan_from_file(filepath)
        
        if not plan:
            print("❌ Konnte Plan nicht laden!")
            return
        
        converter = PlanGraphConverter()
        graph = converter.json_to_networkx(plan)
        
    else:
        print("❌ Ungültige Auswahl!")
        return
    
    # Visualizer erstellen
    visualizer = GraphVisualizer()
    
    print("\n📊 Graph-Statistiken:")
    stats = visualizer.export_graph_stats(graph)
    print(json.dumps(stats, indent=2))
    
    # Visualisierungsoptionen
    print("\nVisualisierungsoptionen:")
    print("1. Matplotlib (statisch)")
    print("2. Plotly (interaktiv)")
    print("3. Beide")
    
    viz_choice = input("Wählen Sie eine Visualisierung (1-3): ").strip()
    
    if viz_choice in ["1", "3"]:
        print("\n🎨 Zeige Matplotlib-Visualisierung...")
        visualizer.show_matplotlib(graph, save_path="graph_visualization.png")
    
    if viz_choice in ["2", "3"]:
        print("\n🎨 Zeige interaktive Plotly-Visualisierung...")
        visualizer.show_plotly_interactive(graph, save_html="graph_visualization.html")


if __name__ == "__main__":
    main()