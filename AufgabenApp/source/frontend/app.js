/**
 * app.js - Frontend JavaScript für Automatisiertes Planungs-Interface
 * Verwaltet WebSocket-Verbindung, API-Calls und Cytoscape.js Integration
 */

class PlanningInterface {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/api';
        this.wsUrl = 'ws://localhost:8000/ws';
        this.websocket = null;
        this.clientId = this.generateClientId();
        this.currentGraph = null;
        this.currentGraphId = null;
        this.currentVersion = null;
        this.cytoscapeInstance = null;
        this.editMode = false;
        this.currentLayout = 'dagre';
        
        this.init();
    }

    generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9);
    }

    async init() {
        console.log('🚀 Initialisiere Planning Interface...');
        
        // Event Listeners setup
        this.setupEventListeners();
        
        // WebSocket verbinden
        await this.connectWebSocket();
        
        // Cytoscape initialisieren
        this.initCytoscape();
        
        // Neo4j Status prüfen
        await this.checkNeo4jStatus();
        
        console.log('✅ Planning Interface bereit');
    }

    setupEventListeners() {
        // Plan Generation Form
        document.getElementById('plan-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generatePlan();
        });

        // Graph Management Buttons
        document.getElementById('save-graph-btn').addEventListener('click', () => {
            this.saveCurrentGraph();
        });

        document.getElementById('load-graphs-btn').addEventListener('click', () => {
            this.loadGraphsList();
        });

        // Control Buttons
        document.getElementById('fit-btn').addEventListener('click', () => {
            if (this.cytoscapeInstance) {
                this.cytoscapeInstance.fit();
            }
        });

        document.getElementById('layout-btn').addEventListener('click', () => {
            this.changeLayout();
        });

        document.getElementById('edit-btn').addEventListener('click', () => {
            this.toggleEditMode();
        });

        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportGraph();
        });

        // Window Events
        window.addEventListener('beforeunload', () => {
            if (this.websocket) {
                this.websocket.close();
            }
        });
    }

    async connectWebSocket() {
        try {
            console.log('🔗 Verbinde WebSocket...');
            this.websocket = new WebSocket(`${this.wsUrl}/${this.clientId}`);

            this.websocket.onopen = () => {
                console.log('✅ WebSocket verbunden');
                this.updateConnectionStatus(true);
            };

            this.websocket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };

            this.websocket.onclose = () => {
                console.log('🔌 WebSocket getrennt');
                this.updateConnectionStatus(false);
                
                // Auto-Reconnect nach 3 Sekunden
                setTimeout(() => {
                    if (!this.websocket || this.websocket.readyState === WebSocket.CLOSED) {
                        this.connectWebSocket();
                    }
                }, 3000);
            };

            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket Fehler:', error);
                this.updateConnectionStatus(false);
            };

        } catch (error) {
            console.error('❌ WebSocket Verbindung fehlgeschlagen:', error);
            this.updateConnectionStatus(false);
        }
    }

    handleWebSocketMessage(message) {
        console.log('📨 WebSocket Nachricht:', message);

        switch (message.type) {
            case 'pong':
                console.log('🏓 Pong erhalten');
                break;
                
            case 'graph_updated':
                this.showSuccessMessage(`Graph ${message.graph_id} wurde aktualisiert (Version ${message.version})`);
                break;
                
            case 'neo4j_updated':
                this.showSuccessMessage(`Neo4j Update abgeschlossen (${message.statements_count} Statements)`);
                break;
                
            case 'neo4j_error':
                this.showErrorMessage(`Neo4j Fehler: ${message.error}`);
                break;
                
            case 'graph_deleted':
                this.showSuccessMessage(`Graph ${message.graph_id} wurde gelöscht`);
                this.loadGraphsList(); // Liste aktualisieren
                break;
                
            default:
                console.log('🤔 Unbekannte Nachricht:', message);
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        const statusText = statusElement.querySelector('span');
        
        if (connected) {
            statusElement.className = 'status-indicator status-connected';
            statusText.textContent = 'WebSocket verbunden';
        } else {
            statusElement.className = 'status-indicator status-disconnected';
            statusText.textContent = 'Verbindung getrennt - Verbinde neu...';
        }
    }

    initCytoscape() {
        console.log('🌐 Initialisiere Cytoscape.js...');
        
        // Register dagre extension falls verfügbar
        if (typeof cytoscape !== 'undefined' && typeof dagre !== 'undefined') {
            if (cytoscape.use && cytoscapeDagre) {
                cytoscape.use(cytoscapeDagre);
            }
        }

        this.cytoscapeInstance = cytoscape({
            container: document.getElementById('cy'),
            
            elements: [], // Initially empty
            
            style: this.getCytoscapeStyle(),
            
            layout: {
                name: 'dagre',
                directed: true,
                padding: 20,
                rankDir: 'TB',
                ranker: 'longest-path'
            },

            // Interaction options
            zoomingEnabled: true,
            userZoomingEnabled: true,
            panningEnabled: true,
            userPanningEnabled: true,
            boxSelectionEnabled: true,
            selectionType: 'single',
            autoungrabify: false,
            autounselectify: false
        });

        // Event Listeners für Cytoscape
        this.setupCytoscapeEvents();
        
        console.log('✅ Cytoscape.js initialisiert');
    }

    setupCytoscapeEvents() {
        // Node Selection
        this.cytoscapeInstance.on('tap', 'node', (event) => {
            const node = event.target;
            const data = node.data();
            console.log('🔘 Node selected:', data);
            
            if (this.editMode) {
                this.selectNode(node);
            } else {
                this.showNodeInfo(data);
            }
        });

        // Edge Selection
        this.cytoscapeInstance.on('tap', 'edge', (event) => {
            const edge = event.target;
            const data = edge.data();
            console.log('🔗 Edge selected:', data);
            
            if (this.editMode) {
                this.selectEdge(edge);
            }
        });

        // Background Click
        this.cytoscapeInstance.on('tap', (event) => {
            if (event.target === this.cytoscapeInstance) {
                this.clearSelection();
            }
        });

        // Graph Changes (für Edit-Mode)
        this.cytoscapeInstance.on('add remove move', () => {
            if (this.editMode) {
                this.onGraphChanged();
            }
        });
    }

    getCytoscapeStyle() {
        return [
            {
                selector: 'node',
                style: {
                    'content': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-family': 'Arial, sans-serif',
                    'font-size': '12px',
                    'color': '#333',
                    'border-width': 2,
                    'border-color': '#000',
                    'text-wrap': 'wrap',
                    'text-max-width': '80px',
                    'shape': 'ellipse',
                    'width': '60px',
                    'height': '60px',
                    'background-color': '#4ECDC4'
                }
            },
            {
                selector: 'node[type="objective"]',
                style: {
                    'background-color': '#FF6B6B',
                    'width': '80px',
                    'height': '80px'
                }
            },
            {
                selector: 'node[type="project"]',
                style: {
                    'background-color': '#4ECDC4',
                    'width': '70px',
                    'height': '70px'
                }
            },
            {
                selector: 'node[type="task"]',
                style: {
                    'background-color': '#45B7D1',
                    'width': '60px',
                    'height': '60px'
                }
            },
            {
                selector: 'node[type="actor"]',
                style: {
                    'background-color': '#96CEB4',
                    'width': '50px',
                    'height': '50px'
                }
            },
            {
                selector: 'node[type="object"]',
                style: {
                    'background-color': '#FFEAA7',
                    'width': '50px',
                    'height': '50px'
                }
            },
            {
                selector: 'node[type="knowledge"]',
                style: {
                    'background-color': '#DDA0DD',
                    'width': '50px',
                    'height': '50px'
                }
            },
            {
                selector: 'node[type="budget"]',
                style: {
                    'background-color': '#F39C12',
                    'width': '50px',
                    'height': '50px'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 3,
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.5
                }
            },
            {
                selector: 'edge[relationship="CONTAINS"]',
                style: {
                    'line-color': '#2C3E50',
                    'target-arrow-color': '#2C3E50'
                }
            },
            {
                selector: 'edge[relationship="REQUIRES"]',
                style: {
                    'line-color': '#E74C3C',
                    'target-arrow-color': '#E74C3C'
                }
            },
            {
                selector: 'edge[relationship="PRECEDES"]',
                style: {
                    'line-color': '#9B59B6',
                    'target-arrow-color': '#9B59B6'
                }
            },
            {
                selector: ':selected',
                style: {
                    'border-width': 4,
                    'border-color': '#667eea'
                }
            }
        ];
    }

    async generatePlan() {
        const goal = document.getElementById('goal-input').value.trim();
        const provider = document.getElementById('llm-provider').value;
        
        if (!goal) {
            this.showErrorMessage('Bitte geben Sie eine Zielbeschreibung ein.');
            return;
        }

        console.log(`🤖 Generiere Plan: "${goal}" mit ${provider}`);
        
        // Loading Modal zeigen
        this.showModal('loading-modal');
        
        // Button deaktivieren
        const generateBtn = document.getElementById('generate-btn');
        generateBtn.disabled = true;

        try {
            const response = await fetch(`${this.apiBaseUrl}/generate-plan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    goal: goal,
                    provider: provider
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Plan-Generierung fehlgeschlagen');
            }

            console.log('✅ Plan generiert:', data);
            
            // Graph aktualisieren
            this.currentGraphId = data.graph_id;
            this.currentVersion = data.version;
            this.loadGraphData(data.cytoscape_elements, data.version_info);
            
            // Success Message
            this.showSuccessMessage(`Plan erfolgreich generiert! Graph ID: ${data.graph_id}`);

        } catch (error) {
            console.error('❌ Plan-Generierung fehlgeschlagen:', error);
            this.showErrorMessage(`Plan-Generierung fehlgeschlagen: ${error.message}`);
        } finally {
            // Loading Modal schließen
            this.closeModal('loading-modal');
            
            // Button wieder aktivieren
            generateBtn.disabled = false;
        }
    }

    loadGraphData(cytoscapeElements, versionInfo = null) {
        console.log(`🔄 Lade Graph mit ${cytoscapeElements.length} Elementen`);
        
        // Elements in Cytoscape laden
        this.cytoscapeInstance.elements().remove();
        this.cytoscapeInstance.add(cytoscapeElements);
        
        // Layout anwenden
        this.applyLayout(this.currentLayout);
        
        // Graph Info aktualisieren
        this.updateGraphInfo(cytoscapeElements, versionInfo);
        
        // Version Indicator aktualisieren
        this.updateVersionIndicator(versionInfo);
        
        // Save Button aktivieren
        document.getElementById('save-graph-btn').disabled = false;
        
        console.log('✅ Graph geladen');
    }

    updateGraphInfo(elements, versionInfo) {
        const nodes = elements.filter(el => !el.data.source);
        const edges = elements.filter(el => el.data.source);
        
        document.getElementById('nodes-count').textContent = nodes.length;
        document.getElementById('edges-count').textContent = edges.length;
        
        if (versionInfo) {
            document.getElementById('current-version').textContent = versionInfo.version || '-';
            document.getElementById('graph-source').textContent = versionInfo.source || '-';
        }
        
        document.getElementById('graph-info').style.display = 'block';
    }

    updateVersionIndicator(versionInfo) {
        const indicator = document.getElementById('version-indicator');
        
        if (versionInfo) {
            document.getElementById('version-number').textContent = versionInfo.version || '?';
            document.getElementById('version-source').textContent = 
                versionInfo.source === 'llm_generated' ? 'LLM Generated' : 'User Edited';
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }

    applyLayout(layoutName = 'dagre') {
        const layouts = {
            dagre: {
                name: 'dagre',
                directed: true,
                padding: 20,
                rankDir: 'TB',
                ranker: 'longest-path'
            },
            circle: {
                name: 'circle',
                padding: 20
            },
            grid: {
                name: 'grid',
                padding: 20
            },
            cose: {
                name: 'cose',
                padding: 20,
                nodeRepulsion: 400000,
                idealEdgeLength: 100
            }
        };
        
        const layout = layouts[layoutName] || layouts.dagre;
        
        try {
            this.cytoscapeInstance.layout(layout).run();
            this.currentLayout = layoutName;
        } catch (error) {
            console.error('❌ Layout-Fehler:', error);
            // Fallback zu Grid
            this.cytoscapeInstance.layout(layouts.grid).run();
        }
    }

    changeLayout() {
        const layouts = ['dagre', 'circle', 'grid', 'cose'];
        const currentIndex = layouts.indexOf(this.currentLayout);
        const nextIndex = (currentIndex + 1) % layouts.length;
        const nextLayout = layouts[nextIndex];
        
        console.log(`🔄 Wechsle Layout zu: ${nextLayout}`);
        this.applyLayout(nextLayout);
    }

    toggleEditMode() {
        this.editMode = !this.editMode;
        const editBtn = document.getElementById('edit-btn');
        
        if (this.editMode) {
            editBtn.innerHTML = '<i class="fas fa-eye"></i>';
            editBtn.style.background = '#e53e3e';
            editBtn.title = 'Ansicht-Modus';
            console.log('✏️ Edit-Modus aktiviert');
        } else {
            editBtn.innerHTML = '<i class="fas fa-edit"></i>';
            editBtn.style.background = 'rgba(255,255,255,0.9)';
            editBtn.title = 'Edit-Modus';
            console.log('👀 Ansicht-Modus aktiviert');
        }
        
        // Selection zurücksetzen
        this.clearSelection();
    }

    selectNode(node) {
        this.clearSelection();
        node.select();
        console.log('🔘 Node selected for editing:', node.data());
    }

    selectEdge(edge) {
        this.clearSelection();
        edge.select();
        console.log('🔗 Edge selected for editing:', edge.data());
    }

    clearSelection() {
        if (this.cytoscapeInstance) {
            this.cytoscapeInstance.elements().unselect();
        }
    }

    showNodeInfo(nodeData) {
        console.log('ℹ️ Node info:', nodeData);
        // TODO: Implement node info panel
    }

    onGraphChanged() {
        if (!this.editMode || !this.currentGraphId) return;
        
        console.log('📝 Graph wurde geändert');
        
        // Debounced Update (warte 1 Sekunde nach letzter Änderung)
        clearTimeout(this.updateTimeout);
        this.updateTimeout = setTimeout(() => {
            this.saveGraphChanges();
        }, 1000);
    }

    async saveGraphChanges() {
        if (!this.currentGraphId || !this.editMode) return;
        
        try {
            console.log('💾 Speichere Graph-Änderungen...');
            
            // Aktuelle Elements sammeln
            const elements = this.cytoscapeInstance.elements().jsons();
            
            const response = await fetch(`${this.apiBaseUrl}/update-graph`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    graph_id: this.currentGraphId,
                    elements: elements
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Graph-Update fehlgeschlagen');
            }

            console.log('✅ Graph-Änderungen gespeichert:', data);
            
            // Version aktualisieren
            this.currentVersion = data.version;
            this.updateVersionIndicator(data.version_info);
            
        } catch (error) {
            console.error('❌ Graph-Update fehlgeschlagen:', error);
            this.showErrorMessage(`Graph-Update fehlgeschlagen: ${error.message}`);
        }
    }

    async saveCurrentGraph() {
        if (!this.currentGraphId) {
            this.showErrorMessage('Kein Graph zum Speichern verfügbar.');
            return;
        }

        // Graph ist bereits automatisch gespeichert via API
        this.showSuccessMessage('Graph ist bereits gespeichert!');
    }

    async loadGraphsList() {
        try {
            console.log('📂 Lade Graph-Liste...');
            
            const response = await fetch(`${this.apiBaseUrl}/graphs`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error('Graph-Liste laden fehlgeschlagen');
            }

            console.log(`📋 ${data.length} Graphen gefunden`);
            this.displayGraphsList(data);
            
        } catch (error) {
            console.error('❌ Graph-Liste laden fehlgeschlagen:', error);
            this.showErrorMessage(`Graph-Liste laden fehlgeschlagen: ${error.message}`);
        }
    }

    displayGraphsList(graphs) {
        const listContainer = document.getElementById('graph-list');
        
        if (graphs.length === 0) {
            listContainer.innerHTML = '<div class="graph-item">Keine Graphen verfügbar</div>';
        } else {
            listContainer.innerHTML = graphs.map(graph => `
                <div class="graph-item ${graph.graph_id === this.currentGraphId ? 'active' : ''}" 
                     onclick="planningInterface.loadGraph('${graph.graph_id}')">
                    <div>
                        <strong>Graph ${graph.graph_id.substring(0, 8)}...</strong>
                        <div class="graph-info-item">Version ${graph.latest_version} | ${graph.total_versions} Versionen</div>
                    </div>
                    <div class="graph-item-info">
                        ${graph.source} | ${new Date(graph.created_at).toLocaleDateString()}
                    </div>
                </div>
            `).join('');
        }
        
        listContainer.style.display = 'block';
    }

    async loadGraph(graphId, version = null) {
        try {
            console.log(`📂 Lade Graph ${graphId} Version ${version || 'latest'}...`);
            
            const url = version ? 
                `${this.apiBaseUrl}/graph/${graphId}?version=${version}` :
                `${this.apiBaseUrl}/graph/${graphId}`;
            
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Graph laden fehlgeschlagen');
            }

            console.log('✅ Graph geladen:', data);
            
            // Graph in Interface laden
            this.currentGraphId = graphId;
            this.currentVersion = data.version;
            this.loadGraphData(data.cytoscape_elements || [], data.version_info);
            
            // Liste aktualisieren
            this.displayGraphsList(await this.getGraphsList());
            
        } catch (error) {
            console.error('❌ Graph laden fehlgeschlagen:', error);
            this.showErrorMessage(`Graph laden fehlgeschlagen: ${error.message}`);
        }
    }

    async getGraphsList() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/graphs`);
            return await response.json();
        } catch (error) {
            console.error('❌ Graph-Liste abrufen fehlgeschlagen:', error);
            return [];
        }
    }

    exportGraph() {
        if (!this.cytoscapeInstance) return;
        
        try {
            const png64 = this.cytoscapeInstance.png({
                output: 'base64uri',
                bg: 'white',
                full: true,
                scale: 2
            });
            
            const link = document.createElement('a');
            link.download = `graph_${this.currentGraphId || 'export'}.png`;
            link.href = png64;
            link.click();
            
            this.showSuccessMessage('Graph als Bild exportiert!');
            
        } catch (error) {
            console.error('❌ Export fehlgeschlagen:', error);
            this.showErrorMessage('Export fehlgeschlagen: ' + error.message);
        }
    }

    async checkNeo4jStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/neo4j/status`);
            const data = await response.json();
            
            const statusElement = document.getElementById('neo4j-status');
            const statusText = statusElement.querySelector('span');
            
            if (data.connected) {
                statusElement.className = 'status-indicator status-connected';
                statusText.textContent = 'Neo4j verbunden';
            } else {
                statusElement.className = 'status-indicator status-disconnected';
                statusText.textContent = `Neo4j getrennt${data.error ? ': ' + data.error : ''}`;
            }
            
        } catch (error) {
            console.error('❌ Neo4j Status prüfen fehlgeschlagen:', error);
            
            const statusElement = document.getElementById('neo4j-status');
            const statusText = statusElement.querySelector('span');
            statusElement.className = 'status-indicator status-disconnected';
            statusText.textContent = 'Neo4j Status unbekannt';
        }
    }

    // Utility Functions
    showModal(modalId) {
        document.getElementById(modalId).style.display = 'block';
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    showErrorMessage(message) {
        document.getElementById('error-message').textContent = message;
        this.showModal('error-modal');
        
        // Auto-close nach 5 Sekunden
        setTimeout(() => {
            this.closeModal('error-modal');
        }, 5000);
    }

    showSuccessMessage(message) {
        document.getElementById('success-message').textContent = message;
        this.showModal('success-modal');
        
        // Auto-close nach 3 Sekunden
        setTimeout(() => {
            this.closeModal('success-modal');
        }, 3000);
    }

    // Test WebSocket
    pingWebSocket() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'ping',
                timestamp: new Date().toISOString()
            }));
        }
    }
}

// Global Functions für HTML Event Handlers
function closeModal(modalId) {
    if (window.planningInterface) {
        window.planningInterface.closeModal(modalId);
    }
}

// Initialize App when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM geladen - Starte Planning Interface');
    window.planningInterface = new PlanningInterface();
    
    // Test WebSocket alle 30 Sekunden
    setInterval(() => {
        if (window.planningInterface) {
            window.planningInterface.pingWebSocket();
        }
    }, 30000);
});