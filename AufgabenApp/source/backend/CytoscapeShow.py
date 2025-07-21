#!/usr/bin/env python3
"""
CytoscapeShow.py - Cytoscape.js Visualisierung von NetworkX-Graphen
Erstellt interaktive Web-Visualisierungen mit Cytoscape.js
"""

import networkx as nx
import json
import webbrowser
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from Plan2Graph import PlanGraphConverter, load_plan_from_file, get_sample_plan


@dataclass
class CytoscapeStyle:
    """Styling-Konfiguration für Cytoscape.js"""
    node_colors: Dict[str, str]
    node_sizes: Dict[str, int]
    edge_colors: Dict[str, str]
    
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
                "objective": 80,
                "project": 60,
                "task": 50,
                "actor": 40,
                "object": 40,
                "knowledge": 40,
                "budget": 40
            },
            edge_colors={
                "CONTAINS": "#2C3E50",     # Dunkelblau für Hierarchie
                "REQUIRES": "#E74C3C",     # Rot für Abhängigkeiten
                "PRECEDES": "#9B59B6"      # Lila für Reihenfolge
            }
        )


class CytoscapeVisualizer:
    """Erstellt Cytoscape.js-Visualisierungen aus NetworkX-Graphen"""
    
    def __init__(self, style: Optional[CytoscapeStyle] = None):
        self.style = style if style else CytoscapeStyle.default()
    
    def networkx_to_cytoscape(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Konvertiert NetworkX-Graph zu Cytoscape.js-Format"""
        
        elements = []
        
        # Knoten konvertieren
        for node_id, node_data in graph.nodes(data=True):
            node_type = node_data.get('node_type', node_data.get('resource_type', 'unknown'))
            
            # Icon mapping für verschiedene Knotentypen
            icon_map = {
                "objective": "\uf3a5",  # Flag
                "project": "\uf07b",   # Folder
                "task": "\uf0ae",      # Tasks
                "actor": "\uf007",     # User
                "object": "\uf1b2",    # Cube
                "knowledge": "\uf02d", # Book
                "budget": "\uf155"     # Dollar
            }
            
            cytoscape_node = {
                "data": {
                    "id": str(node_id),
                    "label": node_data.get('name', str(node_id)),
                    "icon": icon_map.get(node_type, "\uf128"),  # Default: question mark
                    "type": node_type,
                    "description": node_data.get('description', ''),
                    "estimated_hours": node_data.get('estimated_hours', 0),
                    "status": node_data.get('status', 'pending')
                },
                "classes": node_type
            }
            
            elements.append(cytoscape_node)
        
        # Kanten konvertieren
        for source, target, edge_data in graph.edges(data=True):
            relationship = edge_data.get('relationship', 'RELATED_TO')
            
            cytoscape_edge = {
                "data": {
                    "id": f"{source}-{target}",
                    "source": str(source),
                    "target": str(target),
                    "relationship": relationship
                },
                "classes": relationship
            }
            
            elements.append(cytoscape_edge)
        
        print(f"Created {len([e for e in elements if 'source' not in e['data']])} nodes and {len([e for e in elements if 'source' in e['data']])} edges")
        
        return elements
    
    def generate_cytoscape_style(self) -> List[Dict[str, Any]]:
        """Generiert Cytoscape.js-Stylesheet"""
        
        style = []
        
        # Basis-Knoten-Style
        style.append({
            "selector": "node",
            "style": {
                "content": "data(icon)",
                "text-valign": "center",
                "text-halign": "center",
                "font-family": "FontAwesome, Arial, sans-serif",
                "font-size": "24px",
                "color": "#333",
                "border-width": 2,
                "border-color": "#000",
                "text-wrap": "wrap",
                "text-max-width": "100px",
                "shape": "ellipse"
            }
        })
        
        # Label-Style für Hover
        style.append({
            "selector": "node:selected",
            "style": {
                "content": "data(label)",
                "font-size": "10px",
                "font-family": "Arial, sans-serif",
                "text-valign": "bottom",
                "text-margin-y": "5px"
            }
        })
        
        # Knotentyp-spezifische Styles mit Icons
        icon_map = {
            "objective": "\uf3a5",  # Flag
            "project": "\uf07b",   # Folder
            "task": "\uf0ae",      # Tasks
            "actor": "\uf007",     # User
            "object": "\uf1b2",    # Cube
            "knowledge": "\uf02d", # Book
            "budget": "\uf155"     # Dollar
        }
        
        for node_type, color in self.style.node_colors.items():
            icon_char = icon_map.get(node_type, '\uf128')  # Default: question mark
            style.append({
                "selector": f".{node_type}",
                "style": {
                    "background-color": color,
                    "width": f"{self.style.node_sizes.get(node_type, 50)}px",
                    "height": f"{self.style.node_sizes.get(node_type, 50)}px",
                    "content": f"'{icon_char}'"
                }
            })
        
        # Basis-Kanten-Style
        style.append({
            "selector": "edge",
            "style": {
                "width": 3,
                "line-color": "#ccc",
                "target-arrow-color": "#ccc",
                "target-arrow-shape": "triangle",
                "curve-style": "bezier",
                "arrow-scale": 1.5
            }
        })
        
        # Beziehungstyp-spezifische Styles
        for relationship, color in self.style.edge_colors.items():
            style.append({
                "selector": f".{relationship}",
                "style": {
                    "line-color": color,
                    "target-arrow-color": color
                }
            })
        
        # Hover-Effekte
        style.append({
            "selector": "node:selected",
            "style": {
                "border-width": 4,
                "border-color": "#000"
            }
        })
        
        # Tooltip-Style beim Hover
        style.append({
            "selector": "node:active",
            "style": {
                "overlay-opacity": 0.2,
                "overlay-color": "#000"
            }
        })
        
        return style
    
    def generate_html_template(self, cytoscape_elements: List[Dict[str, Any]], 
                             title: str = "Graph Visualisierung") -> str:
        """Generiert HTML-Template für Cytoscape.js"""
        
        style_json = json.dumps(self.generate_cytoscape_style(), indent=2)
        data_json = json.dumps(cytoscape_elements, indent=2)
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <script src="https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
    <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }}
        
        #cy {{
            width: 100%;
            height: 80vh;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .controls {{
            margin-bottom: 20px;
            text-align: center;
        }}
        
        button {{
            background-color: #4ECDC4;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        select {{
            background-color: #4ECDC4;
            color: white;
            border: none;
            padding: 10px 15px;
            margin: 0 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            min-width: 200px;
        }}
        
        select option {{
            background-color: white;
            color: black;
            padding: 5px;
        }}
        
        button:hover {{
            background-color: #45B7D1;
        }}
        
        .edit-controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .edit-controls button {{
            display: block;
            width: 100%;
            margin: 5px 0;
            background-color: #27AE60;
        }}
        
        .edit-controls button:hover {{
            background-color: #2ECC71;
        }}
        
        .edit-controls button.delete {{
            background-color: #E74C3C;
        }}
        
        .edit-controls button.delete:hover {{
            background-color: #C0392B;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.4);
        }}
        
        .modal-content {{
            background-color: white;
            margin: 15% auto;
            padding: 20px;
            border: 1px solid #888;
            border-radius: 5px;
            width: 400px;
            max-width: 90%;
        }}
        
        .modal-content h3 {{
            margin-top: 0;
        }}
        
        .modal-content input, .modal-content select, .modal-content textarea {{
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 3px;
            box-sizing: border-box;
        }}
        
        .modal-content textarea {{
            height: 100px;
            resize: vertical;
        }}
        
        .modal-buttons {{
            text-align: right;
            margin-top: 20px;
        }}
        
        .modal-buttons button {{
            margin-left: 10px;
        }}
        
        .context-menu {{
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 5px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            display: none;
        }}
        
        .context-menu-item {{
            padding: 8px 15px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .context-menu-item:hover {{
            background-color: #f5f5f5;
        }}
        
        .info-panel {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            max-width: 300px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: none;
        }}
        
        .info-panel h3 {{
            margin-top: 0;
            color: #333;
        }}
        
        .legend {{
            margin-top: 20px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            border: 1px solid #000;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            color: #333;
        }}
        
        .legend-edge {{
            width: 30px;
            height: 3px;
            margin-right: 10px;
            border-radius: 2px;
            position: relative;
            display: flex;
            align-items: center;
        }}
        
        .legend-edge::after {{
            content: '';
            position: absolute;
            right: -3px;
            top: 50%;
            transform: translateY(-50%);
            width: 0;
            height: 0;
            border-left: 6px solid currentColor;
            border-top: 3px solid transparent;
            border-bottom: 3px solid transparent;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="controls">
        <button onclick="resetView()">🔄 Ansicht zurücksetzen</button>
        <button onclick="fitToScreen()">🔍 An Bildschirm anpassen</button>
        <select id="layout-select" onchange="changeLayout()">
            <option value="0">📐 Dagre (Hierarchisch)</option>
            <option value="1">🌳 Breadth-First (Baum)</option>
            <option value="2">⭕ Kreis</option>
            <option value="3">🎯 Konzentrisch</option>
            <option value="4">⏹️ Gitter</option>
            <option value="5">🎲 Zufällig</option>
            <option value="6">📌 Voreinstellung</option>
            <option value="7">🔗 COSE (Kraft-basiert)</option>
        </select>
        <button onclick="exportImage()">📸 Bild exportieren</button>
        <button onclick="toggleEditMode()">✏️ Edit-Modus</button>
    </div>
    
    <div id="cy"></div>
    
    <div id="info-panel" class="info-panel">
        <h3>Knoten-Information</h3>
        <div id="node-info"></div>
    </div>
    
    <div id="edit-controls" class="edit-controls" style="display: none;">
        <h4>Edit-Modus</h4>
        <button onclick="addNode()">➕ Knoten hinzufügen</button>
        <button onclick="addEdge()">🔗 Kante hinzufügen</button>
        <button onclick="deleteSelected()" class="delete">🗑️ Löschen</button>
        <button onclick="editSelected()">✏️ Bearbeiten</button>
        <button onclick="saveGraph()">💾 Speichern</button>
    </div>
    
    <div id="context-menu" class="context-menu">
        <div class="context-menu-item" onclick="editNode()">Bearbeiten</div>
        <div class="context-menu-item" onclick="deleteNode()">Löschen</div>
        <div class="context-menu-item" onclick="addConnection()">Verbindung hinzufügen</div>
    </div>
    
    <!-- Modal für Knoten-Bearbeitung -->
    <div id="node-modal" class="modal">
        <div class="modal-content">
            <h3>Knoten bearbeiten</h3>
            <label>Name:</label>
            <input type="text" id="node-name" placeholder="Knoten-Name">
            <label>Typ:</label>
            <select id="node-type">
                <option value="objective">Ziel</option>
                <option value="project">Projekt</option>
                <option value="task">Aufgabe</option>
                <option value="actor">Akteur</option>
                <option value="object">Objekt</option>
                <option value="knowledge">Wissen</option>
                <option value="budget">Budget</option>
            </select>
            <label>Beschreibung:</label>
            <textarea id="node-description" placeholder="Beschreibung"></textarea>
            <label>Geschätzte Stunden:</label>
            <input type="number" id="node-hours" placeholder="0">
            <label>Status:</label>
            <select id="node-status">
                <option value="pending">Ausstehend</option>
                <option value="in_progress">In Bearbeitung</option>
                <option value="completed">Abgeschlossen</option>
            </select>
            <div class="modal-buttons">
                <button onclick="closeModal()">Abbrechen</button>
                <button onclick="saveNode()">Speichern</button>
            </div>
        </div>
    </div>
    
    <!-- Modal für Kanten-Bearbeitung -->
    <div id="edge-modal" class="modal">
        <div class="modal-content">
            <h3>Kante hinzufügen</h3>
            <label>Von Knoten:</label>
            <select id="edge-source"></select>
            <label>Zu Knoten:</label>
            <select id="edge-target"></select>
            <label>Beziehungstyp:</label>
            <select id="edge-type">
                <option value="CONTAINS">Enthält</option>
                <option value="REQUIRES">Benötigt</option>
                <option value="PRECEDES">Geht voraus</option>
            </select>
            <div class="modal-buttons">
                <button onclick="closeModal()">Abbrechen</button>
                <button onclick="saveEdge()">Speichern</button>
            </div>
        </div>
    </div>
    
    <div class="legend">
        <h3>Legende</h3>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FF6B6B;"><i class="fas fa-flag"></i></div>
            <span>Ziel (Objective)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #4ECDC4;"><i class="fas fa-folder"></i></div>
            <span>Projekt (Project)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #45B7D1;"><i class="fas fa-tasks"></i></div>
            <span>Aufgabe (Task)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #96CEB4;"><i class="fas fa-user"></i></div>
            <span>Akteur (Actor)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FFEAA7;"><i class="fas fa-cube"></i></div>
            <span>Objekt (Object)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #DDA0DD;"><i class="fas fa-book"></i></div>
            <span>Wissen (Knowledge)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #F39C12;"><i class="fas fa-dollar-sign"></i></div>
            <span>Budget</span>
        </div>
        
        <h4>Kanten (Beziehungen)</h4>
        <div class="legend-item">
            <div class="legend-edge" style="background-color: #2C3E50; color: #2C3E50;"></div>
            <span>Enthält (CONTAINS)</span>
        </div>
        <div class="legend-item">
            <div class="legend-edge" style="background-color: #E74C3C; color: #E74C3C;"></div>
            <span>Benötigt (REQUIRES)</span>
        </div>
        <div class="legend-item">
            <div class="legend-edge" style="background-color: #9B59B6; color: #9B59B6;"></div>
            <span>Geht voraus (PRECEDES)</span>
        </div>
    </div>
    
    <script>
        var cy;
        var currentLayout = 'dagre';
        var editMode = false;
        var selectedNode = null;
        var nextNodeId = 1;
        
        document.addEventListener('DOMContentLoaded', function() {{
            // Register dagre extension
            if (typeof cytoscape === 'function' && typeof dagre !== 'undefined') {{
                cytoscape.use(cytoscapeDagre);
            }}
            
            cy = cytoscape({{
                container: document.getElementById('cy'),
                
                elements: {data_json},
                
                style: {style_json},
                
                layout: {{
                    name: 'dagre',
                    directed: true,
                    padding: 20,
                    rankDir: 'TB',
                    ranker: 'longest-path'
                }}
            }});
            
            console.log('Cytoscape initialized with', cy.nodes().length, 'nodes and', cy.edges().length, 'edges');
            
            // Event-Handler für Knoten-Klick
            cy.on('tap', 'node', function(event) {{
                var node = event.target;
                var data = node.data();
                
                if (editMode) {{
                    selectedNode = node;
                    cy.nodes().removeClass('selected');
                    node.addClass('selected');
                }} else {{
                    var infoPanel = document.getElementById('info-panel');
                    var nodeInfo = document.getElementById('node-info');
                    
                    var html = '<strong>' + data.label + '</strong><br>';
                    html += 'Typ: ' + data.type + '<br>';
                    if (data.description) html += 'Beschreibung: ' + data.description + '<br>';
                    if (data.estimated_hours) html += 'Geschätzte Stunden: ' + data.estimated_hours + '<br>';
                    if (data.status) html += 'Status: ' + data.status + '<br>';
                    
                    nodeInfo.innerHTML = html;
                    infoPanel.style.display = 'block';
                }}
            }});
            
            // Event-Handler für Hintergrund-Klick
            cy.on('tap', function(event) {{
                if (event.target === cy) {{
                    document.getElementById('info-panel').style.display = 'none';
                    hideContextMenu();
                    if (editMode) {{
                        selectedNode = null;
                        cy.nodes().removeClass('selected');
                    }}
                }}
            }});
            
            // Rechtsklick für Context-Menu
            cy.on('cxttap', 'node', function(event) {{
                if (editMode) {{
                    selectedNode = event.target;
                    showContextMenu(event.renderedPosition || event.position);
                }}
            }});
            
            // Tooltip für Node-Hover
            cy.on('mouseover', 'node', function(event) {{
                var node = event.target;
                var pos = node.renderedPosition();
                var label = node.data('label');
                
                // Erstelle Tooltip
                var tooltip = document.createElement('div');
                tooltip.id = 'node-tooltip';
                tooltip.innerHTML = label;
                tooltip.style.cssText = `
                    position: absolute;
                    background: #333;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 12px;
                    z-index: 1000;
                    pointer-events: none;
                    left: ${{pos.x + 20}}px;
                    top: ${{pos.y - 30}}px;
                `;
                
                document.body.appendChild(tooltip);
            }});
            
            cy.on('mouseout', 'node', function(event) {{
                var tooltip = document.getElementById('node-tooltip');
                if (tooltip) {{
                    tooltip.remove();
                }}
            }});
        }});
        
        function resetView() {{
            cy.fit();
            cy.center();
        }}
        
        function fitToScreen() {{
            cy.fit();
        }}
        
        var layouts = [
            {{
                name: 'dagre',
                title: 'Dagre (Hierarchisch)',
                options: {{
                    name: 'dagre',
                    directed: true,
                    padding: 20,
                    rankDir: 'TB',
                    ranker: 'longest-path'
                }}
            }},
            {{
                name: 'breadthfirst',
                title: 'Breadth-First (Baum)',
                options: {{
                    name: 'breadthfirst',
                    directed: true,
                    padding: 20,
                    spacingFactor: 1.2
                }}
            }},
            {{
                name: 'circle',
                title: 'Kreis',
                options: {{
                    name: 'circle',
                    padding: 20,
                    radius: 200
                }}
            }},
            {{
                name: 'concentric',
                title: 'Konzentrisch',
                options: {{
                    name: 'concentric',
                    padding: 20,
                    minNodeSpacing: 50,
                    concentric: function(node) {{
                        return node.degree();
                    }}
                }}
            }},
            {{
                name: 'grid',
                title: 'Gitter',
                options: {{
                    name: 'grid',
                    padding: 20,
                    rows: undefined,
                    cols: undefined
                }}
            }},
            {{
                name: 'random',
                title: 'Zufällig',
                options: {{
                    name: 'random',
                    padding: 20
                }}
            }},
            {{
                name: 'preset',
                title: 'Voreinstellung',
                options: {{
                    name: 'preset',
                    padding: 20
                }}
            }},
            {{
                name: 'cose',
                title: 'COSE (Kraft-basiert)',
                options: {{
                    name: 'cose',
                    padding: 20,
                    nodeRepulsion: 400000,
                    nodeOverlap: 10,
                    idealEdgeLength: 100,
                    edgeElasticity: 100,
                    nestingFactor: 5,
                    gravity: 80,
                    numIter: 1000,
                    initialTemp: 200,
                    coolingFactor: 0.95,
                    minTemp: 1.0
                }}
            }}
        ];
        
        var currentLayoutIndex = 0;
        
        function changeLayout() {{
            var select = document.getElementById('layout-select');
            var layoutIndex = parseInt(select.value);
            var layout = layouts[layoutIndex];
            
            console.log('Wechsle zu Layout:', layout.title);
            
            try {{
                cy.layout(layout.options).run();
                currentLayout = layout.name;
                currentLayoutIndex = layoutIndex;
            }} catch (error) {{
                console.error('Layout-Fehler:', error);
                // Fallback zu dagre
                cy.layout({{
                    name: 'dagre',
                    directed: true,
                    padding: 20,
                    rankDir: 'TB'
                }}).run();
            }}
        }}
        
        function toggleLayout() {{
            currentLayoutIndex = (currentLayoutIndex + 1) % layouts.length;
            var select = document.getElementById('layout-select');
            select.value = currentLayoutIndex;
            changeLayout();
        }}
        
        // Fallback if dagre doesn't work
        function fallbackLayout() {{
            if (cy.nodes().length === 0) {{
                console.error('No nodes found in graph');
                return;
            }}
            
            cy.layout({{
                name: 'breadthfirst',
                directed: true,
                padding: 20
            }}).run();
        }}
        
        // Try fallback after 2 seconds if graph is empty
        setTimeout(function() {{
            if (cy && cy.nodes().length === 0) {{
                console.log('No nodes detected, trying fallback...');
                fallbackLayout();
            }}
        }}, 2000);
        
        function exportImage() {{
            var png64 = cy.png({{
                output: 'base64uri',
                bg: 'white',
                full: true,
                scale: 2
            }});
            
            var link = document.createElement('a');
            link.download = 'graph.png';
            link.href = png64;
            link.click();
        }}
        
        // Edit-Modus Funktionen
        function toggleEditMode() {{
            editMode = !editMode;
            var editControls = document.getElementById('edit-controls');
            var button = event.target;
            
            if (editMode) {{
                editControls.style.display = 'block';
                button.textContent = '👀 Ansicht-Modus';
                button.style.backgroundColor = '#E74C3C';
            }} else {{
                editControls.style.display = 'none';
                button.textContent = '✏️ Edit-Modus';
                button.style.backgroundColor = '#4ECDC4';
                selectedNode = null;
                cy.nodes().removeClass('selected');
            }}
        }}
        
        function addNode() {{
            document.getElementById('node-modal').style.display = 'block';
            document.getElementById('node-name').value = '';
            document.getElementById('node-type').value = 'task';
            document.getElementById('node-description').value = '';
            document.getElementById('node-hours').value = '';
            document.getElementById('node-status').value = 'pending';
        }}
        
        function editSelected() {{
            if (!selectedNode) {{
                alert('Bitte wählen Sie einen Knoten aus.');
                return;
            }}
            
            var data = selectedNode.data();
            document.getElementById('node-modal').style.display = 'block';
            document.getElementById('node-name').value = data.label || '';
            document.getElementById('node-type').value = data.type || 'task';
            document.getElementById('node-description').value = data.description || '';
            document.getElementById('node-hours').value = data.estimated_hours || '';
            document.getElementById('node-status').value = data.status || 'pending';
        }}
        
        function deleteSelected() {{
            if (!selectedNode) {{
                alert('Bitte wählen Sie einen Knoten aus.');
                return;
            }}
            
            if (confirm('Knoten wirklich löschen?')) {{
                cy.remove(selectedNode);
                selectedNode = null;
            }}
        }}
        
        function addEdge() {{
            populateNodeSelects();
            document.getElementById('edge-modal').style.display = 'block';
        }}
        
        function saveNode() {{
            var name = document.getElementById('node-name').value;
            var type = document.getElementById('node-type').value;
            var description = document.getElementById('node-description').value;
            var hours = document.getElementById('node-hours').value;
            var status = document.getElementById('node-status').value;
            
            if (!name) {{
                alert('Bitte geben Sie einen Namen ein.');
                return;
            }}
            
            var nodeData = {{
                label: name,
                type: type,
                description: description,
                estimated_hours: hours ? parseInt(hours) : 0,
                status: status,
                icon: getIconForType(type)
            }};
            
            if (selectedNode) {{
                // Bearbeitung
                selectedNode.data(nodeData);
            }} else {{
                // Neuer Knoten
                var nodeId = 'node_' + nextNodeId++;
                nodeData.id = nodeId;
                
                cy.add({{
                    data: nodeData,
                    classes: type
                }});
            }}
            
            closeModal();
        }}
        
        function saveEdge() {{
            var source = document.getElementById('edge-source').value;
            var target = document.getElementById('edge-target').value;
            var type = document.getElementById('edge-type').value;
            
            if (!source || !target) {{
                alert('Bitte wählen Sie Quell- und Zielknoten aus.');
                return;
            }}
            
            if (source === target) {{
                alert('Quell- und Zielknoten müssen unterschiedlich sein.');
                return;
            }}
            
            var edgeId = source + '-' + target;
            
            cy.add({{
                data: {{
                    id: edgeId,
                    source: source,
                    target: target,
                    relationship: type
                }},
                classes: type
            }});
            
            closeModal();
        }}
        
        function closeModal() {{
            document.getElementById('node-modal').style.display = 'none';
            document.getElementById('edge-modal').style.display = 'none';
        }}
        
        function showContextMenu(position) {{
            var menu = document.getElementById('context-menu');
            menu.style.left = position.x + 'px';
            menu.style.top = position.y + 'px';
            menu.style.display = 'block';
        }}
        
        function hideContextMenu() {{
            document.getElementById('context-menu').style.display = 'none';
        }}
        
        function editNode() {{
            hideContextMenu();
            editSelected();
        }}
        
        function deleteNode() {{
            hideContextMenu();
            deleteSelected();
        }}
        
        function addConnection() {{
            hideContextMenu();
            addEdge();
        }}
        
        function populateNodeSelects() {{
            var sourceSelect = document.getElementById('edge-source');
            var targetSelect = document.getElementById('edge-target');
            
            sourceSelect.innerHTML = '';
            targetSelect.innerHTML = '';
            
            cy.nodes().forEach(function(node) {{
                var option = document.createElement('option');
                option.value = node.id();
                option.textContent = node.data('label');
                sourceSelect.appendChild(option.cloneNode(true));
                targetSelect.appendChild(option);
            }});
        }}
        
        function getIconForType(type) {{
            var iconMap = {{
                'objective': '\\f3a5',
                'project': '\\f07b',
                'task': '\\f0ae',
                'actor': '\\f007',
                'object': '\\f1b2',
                'knowledge': '\\f02d',
                'budget': '\\f155'
            }};
            return iconMap[type] || '\\f128';
        }}
        
        function saveGraph() {{
            var elements = cy.elements().jsons();
            var graphData = {{
                elements: elements,
                timestamp: new Date().toISOString()
            }};
            
            var dataStr = JSON.stringify(graphData, null, 2);
            var dataBlob = new Blob([dataStr], {{type: 'application/json'}});
            
            var link = document.createElement('a');
            link.download = 'edited_graph.json';
            link.href = URL.createObjectURL(dataBlob);
            link.click();
            
            console.log('Graph gespeichert:', graphData);
        }}
        
        // Modal schließen bei Klick außerhalb
        window.onclick = function(event) {{
            var nodeModal = document.getElementById('node-modal');
            var edgeModal = document.getElementById('edge-modal');
            
            if (event.target === nodeModal) {{
                nodeModal.style.display = 'none';
            }}
            if (event.target === edgeModal) {{
                edgeModal.style.display = 'none';
            }}
        }}
        
        // Finde höchste Node-ID für nextNodeId
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                var maxId = 0;
                cy.nodes().forEach(function(node) {{
                    var id = node.id();
                    if (id.startsWith('node_')) {{
                        var num = parseInt(id.substring(5));
                        if (num > maxId) maxId = num;
                    }}
                }});
                nextNodeId = maxId + 1;
            }}, 100);
        }});
    </script>
</body>
</html>
"""
        return html_template
    
    def create_visualization(self, graph: nx.DiGraph, output_file: str = "graph_cytoscape.html",
                           title: str = "Graph Visualisierung", open_browser: bool = True) -> str:
        """Erstellt komplette Cytoscape.js-Visualisierung"""
        
        # NetworkX zu Cytoscape konvertieren
        cytoscape_elements = self.networkx_to_cytoscape(graph)
        
        # HTML generieren
        html_content = self.generate_html_template(cytoscape_elements, title)
        
        # Datei schreiben
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 Cytoscape.js-Visualisierung erstellt: {output_file}")
        
        # Browser öffnen
        if open_browser:
            file_path = os.path.abspath(output_file)
            webbrowser.open(f"file://{file_path}")
        
        return output_file
    
    def export_cytoscape_json(self, graph: nx.DiGraph, output_file: str = "graph_cytoscape.json") -> str:
        """Exportiert Graph als Cytoscape.js-JSON"""
        
        cytoscape_elements = self.networkx_to_cytoscape(graph)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cytoscape_elements, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Cytoscape.js-JSON exportiert: {output_file}")
        return output_file
    
    def create_visualization_from_cytoscape(self, elements: List[Dict[str, Any]], 
                                          output_file: str = "graph_cytoscape.html",
                                          title: str = "Editierter Graph", 
                                          open_browser: bool = True) -> str:
        """Erstellt Cytoscape.js-Visualisierung direkt aus Cytoscape-Elementen"""
        
        # HTML generieren
        html_content = self.generate_html_template(elements, title)
        
        # Datei schreiben
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 Cytoscape.js-Visualisierung aus editiertem Graph erstellt: {output_file}")
        
        # Browser öffnen
        if open_browser:
            file_path = os.path.abspath(output_file)
            webbrowser.open(f"file://{file_path}")
        
        return output_file


def load_cytoscape_from_file(filepath: str) -> List[Dict[str, Any]]:
    """Lädt eine editierte Cytoscape.js-JSON-Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Prüfe ob es eine editierte Graph-Datei ist
        if 'elements' in data and isinstance(data['elements'], list):
            print(f"✅ Cytoscape-Graph geladen: {len(data['elements'])} Elemente")
            return data['elements']
        
        # Fallback: Versuche als normale Plan-Datei zu laden
        print("⚠️ Nicht als Cytoscape-Graph erkannt, versuche als Plan-Datei...")
        return []
    except Exception as e:
        print(f"❌ Fehler beim Laden der Cytoscape-Datei: {e}")
        return []


def create_test_graph() -> nx.DiGraph:
    """Erstellt einen einfachen Test-Graph"""
    test_graph = nx.DiGraph()
    
    # Knoten hinzufügen
    test_graph.add_node("obj1", name="Website Relaunch", node_type="objective")
    test_graph.add_node("proj1", name="Frontend", node_type="project")
    test_graph.add_node("task1", name="Design", node_type="task")
    test_graph.add_node("task2", name="Implementation", node_type="task")
    test_graph.add_node("res1", name="Designer", resource_type="actor")
    test_graph.add_node("res2", name="React", resource_type="object")
    
    # Kanten hinzufügen
    test_graph.add_edge("obj1", "proj1", relationship="CONTAINS")
    test_graph.add_edge("proj1", "task1", relationship="CONTAINS")
    test_graph.add_edge("proj1", "task2", relationship="CONTAINS")
    test_graph.add_edge("task1", "task2", relationship="PRECEDES")
    test_graph.add_edge("task1", "res1", relationship="REQUIRES")
    test_graph.add_edge("task2", "res2", relationship="REQUIRES")
    
    return test_graph


def main():
    """Hauptfunktion für Cytoscape.js-Visualisierung"""
    print("🌐 Cytoscape.js Graph Visualisierung")
    print("=" * 40)
    
    # Optionen für Graph-Quelle
    print("\nOptionen:")
    print("1. Test-Graph verwenden")
    print("2. Beispiel-Plan verwenden")
    print("3. JSON-Datei laden (Plan-Format)")
    print("4. Editierte Cytoscape.js-JSON laden")
    
    choice = input("Wählen Sie eine Option (1-4): ").strip()
    
    if choice == "1":
        print("🧪 Verwende Test-Graph...")
        graph = create_test_graph()
        title = "Test-Graph Visualisierung"
        
    elif choice == "2":
        print("📄 Verwende Beispiel-Plan...")
        plan = get_sample_plan()
        converter = PlanGraphConverter()
        graph = converter.json_to_networkx(plan)
        title = "Beispiel-Plan Visualisierung"
        
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
        title = f"Graph aus {os.path.basename(filepath)}"
        
    elif choice == "4":
        filepath = input("Geben Sie den Pfad zur editierten Cytoscape.js-JSON-Datei ein: ").strip()
        if not filepath:
            print("❌ Kein Dateipfad angegeben!")
            return
        
        print(f"📄 Lade editierten Graph aus {filepath}...")
        elements = load_cytoscape_from_file(filepath)
        
        if not elements:
            print("❌ Konnte editierten Graph nicht laden!")
            return
        
        # Direkte Visualisierung ohne NetworkX-Konvertierung
        visualizer = CytoscapeVisualizer()
        output_file = input("Output-Datei (Enter für 'edited_graph.html'): ").strip()
        if not output_file:
            output_file = "edited_graph.html"
        
        title = f"Editierter Graph aus {os.path.basename(filepath)}"
        visualizer.create_visualization_from_cytoscape(elements, output_file, title)
        
        print(f"\n✅ Fertig! Öffne {output_file} in deinem Browser.")
        return
        
    else:
        print("❌ Ungültige Auswahl!")
        return
    
    # Visualizer erstellen
    visualizer = CytoscapeVisualizer()
    
    # Output-Datei festlegen
    output_file = input("Output-Datei (Enter für 'graph_cytoscape.html'): ").strip()
    if not output_file:
        output_file = "graph_cytoscape.html"
    
    # Visualisierung erstellen
    print(f"\n🔄 Erstelle Cytoscape.js-Visualisierung...")
    visualizer.create_visualization(graph, output_file, title)
    
    # Optional: JSON export
    export_json = input("JSON-Export erstellen? (y/n): ").strip().lower()
    if export_json in ['y', 'yes', 'ja']:
        json_file = output_file.replace('.html', '.json')
        visualizer.export_cytoscape_json(graph, json_file)
    
    print(f"\n✅ Fertig! Öffne {output_file} in deinem Browser.")


if __name__ == "__main__":
    main()