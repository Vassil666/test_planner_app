# 🚀 Automatisiertes Planungs-Interface

ClaudeCode Project für automatisierte Projekte Steuerung mit LLM-Integration und Neo4j-Backend.

## ✨ Features

### 🎯 Vollautomatisierter Workflow
- **Initial Form** → LLM-Anfrage → **Version 1 Neo4j Graph**
- **Cytoscape-Editor** → User-Bearbeitung → **Version 2 Neo4j Graph** 
- **Real-time Updates** über WebSocket
- **Parallele Verarbeitung** im Hintergrund

### 🤖 LLM-Integration
- **Ollama** (Lokal) - llama3.2, llama2
- **Claude API** - Anthropic Claude-3
- **ChatGPT API** - OpenAI GPT-4

### 📊 Graph-Management
- **Interactive Cytoscape.js** Editor mit Edit-Modus
- **Version Management** (V1: LLM-generiert, V2: User-editiert)
- **Automatische Neo4j Synchronisation**
- **Export** als PNG/JSON

### 🗄️ Multi-Database Support
- **Neo4j Aura Cloud** - Graph Database
- **Oracle Cloud** - Autonomous Database (ATP/ADW)
- **Local Storage** - Version Management

## 🏗️ Architektur

```
source/
├── backend/                 # FastAPI Server
│   ├── app.py              # Haupt-Server
│   ├── neo4j_manager.py    # Neo4j Integration
│   ├── version_manager.py  # Graph-Versioning
│   ├── start_server.py     # Server-Starter
│   ├── Input2Plan.py       # LLM-Integration
│   ├── Plan2Graph.py       # JSON → NetworkX → Cypher
│   ├── CytoscapeShow.py    # NetworkX → Cytoscape.js
│   ├── Cytoscape2Graph.py  # Cytoscape.js → NetworkX
│   ├── myNeo.py           # Neo4j Client
│   └── myOracle.py        # Oracle Client
├── frontend/               # Web Interface
│   ├── index.html         # React-ähnliches Interface
│   └── app.js             # WebSocket + API Client
```

## 🚀 Installation & Setup

### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 2. API-Keys konfigurieren

```bash
# Konfigurationsdatei bearbeiten
nano config/app_config.env

# Füge deine API-Keys ein:
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-claude-api-key-here
```

**API-Keys erhalten:**
- **OpenAI:** https://platform.openai.com/api-keys
- **Claude:** https://console.anthropic.com/

### 3. Server starten

```bash
cd source/backend
python start_server.py
```

## 🌐 Nutzung

### Web Interface
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs  
- **WebSocket:** ws://localhost:8000/ws/test-client

### Workflow
1. **📝 Projekt beschreiben** in der Web-UI
2. **🤖 LLM-Provider auswählen** (Ollama/Claude/ChatGPT)  
3. **🚀 "Plan Generieren"** → Automatische Version 1 in Neo4j
4. **✏️ Edit-Modus aktivieren** → Graph interaktiv bearbeiten
5. **💾 Änderungen** werden automatisch als Version 2 gespeichert
6. **📊 Real-time Updates** über WebSocket

### API Endpoints

```http
POST /api/generate-plan
POST /api/update-graph  
GET  /api/graph/{graph_id}
GET  /api/graphs
DELETE /api/graph/{graph_id}
GET  /api/neo4j/status
GET  /api/health
```

### WebSocket Events

```json
{
  "type": "graph_updated",
  "graph_id": "uuid", 
  "version": 2,
  "timestamp": "2024-07-21T..."
}
```

## 🔧 Konfiguration

Die komplette Konfiguration erfolgt über `config/app_config.env`:

```bash
# Beispiel-Konfiguration
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
NEO4J_URI=neo4j+s://2560410f.databases.neo4j.io:7687
SERVER_PORT=8000
DEBUG_MODE=true
```

### Neo4j Setup
- **Cloud:** Neo4j Aura (bereits vorkonfiguriert)
- **Credentials:** Bereits in `app_config.env` gesetzt

### LLM Provider

#### Ollama (Lokal)
```bash
# Installation
curl -fsSL https://ollama.com/install.sh | sh

# Model herunterladen  
ollama pull llama3.2
ollama serve
```

#### Claude API
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### ChatGPT API  
```bash
export OPENAI_API_KEY="sk-..."
```

### Oracle Cloud (Optional)
- **Wallet** in `./wallet/` Verzeichnis
- **Connection String** in `myOracle.py`
- **Credentials** konfigurieren

## 📊 Graph-Struktur

### Node-Types
- **🎯 Objective** - Hauptziele (rot)
- **📁 Project** - Projekte (türkis)  
- **✅ Task** - Aufgaben (blau)
- **👤 Actor** - Akteure (grün)
- **📦 Object** - Objekte (gelb)
- **📚 Knowledge** - Wissen (lila)
- **💰 Budget** - Budget (orange)

### Relationships
- **CONTAINS** - Hierarchie (Ziel → Projekt → Task)
- **REQUIRES** - Abhängigkeiten (Task → Ressource)  
- **PRECEDES** - Reihenfolge (Task1 → Task2)

### Neo4j Queries

```cypher
// Alle Graphen anzeigen
MATCH (v:GraphVersion) 
RETURN v.graph_id, v.version, v.created_at

// Graph Version laden
MATCH (n) 
WHERE n.id STARTS WITH 'graph-uuid_v1_'
RETURN n

// Abhängigkeiten finden
MATCH (t:TASK)-[r:REQUIRES]->(resource) 
RETURN t.name, type(r), resource.name
```

## 🔍 Debugging

### Logs
```bash
# Server Logs
tail -f logs/app.log

# Neo4j Status prüfen
curl http://localhost:8000/api/neo4j/status

# Health Check
curl http://localhost:8000/api/health
```

### WebSocket Test
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/test-client');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
ws.send(JSON.stringify({type: 'ping'}));
```

### API Test
```bash
# Plan generieren
curl -X POST http://localhost:8000/api/generate-plan \
  -H "Content-Type: application/json" \
  -d '{"goal": "Website entwickeln", "provider": "ollama"}'

# Graphen auflisten  
curl http://localhost:8000/api/graphs
```

## 📈 Performance

- **WebSocket:** Real-time Updates ohne Polling
- **Background Tasks:** Neo4j Updates laufen parallel  
- **Caching:** Version Manager mit In-Memory Cache
- **Lazy Loading:** Cytoscape-Elemente on-demand

## 🔒 Security

- **CORS:** Konfiguriert für localhost:3000, localhost:8080
- **Input Validation:** Pydantic Models
- **API Keys:** Environment Variables
- **Database:** Prepared Statements gegen Injection

## 🚀 Deployment

### Docker (empfohlen)
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY source/ /app/source/
WORKDIR /app/source/backend  
CMD ["python", "start_server.py"]
```

### Systemd Service
```ini
[Unit]
Description=Planning Interface
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/app/source/backend
ExecStart=python start_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🧪 Testing

```bash
# Unit Tests
pytest source/backend/tests/

# Integration Test
python source/backend/test_workflow.py

# Load Test  
ab -n 100 -c 10 http://localhost:8000/api/health
```

## 📚 Development

### Neue Features hinzufügen

1. **Backend:** API Endpoint in `app.py`
2. **Frontend:** UI Update in `index.html` + `app.js`  
3. **WebSocket:** Event-Handler erweitern
4. **Database:** Migration für Neo4j Schema

### Code Style
```bash
black source/
flake8 source/  
mypy source/
```

## 🐛 Troubleshooting

### Häufige Probleme

**Neo4j Verbindung:**
```bash
# URI prüfen
echo $NEO4J_URI

# Credentials testen  
python source/backend/myNeo.py
```

**LLM Provider:**
```bash
# Ollama Status
ollama list

# API Keys prüfen
echo $ANTHROPIC_API_KEY | cut -c1-10
```

**WebSocket:**
```bash
# Browser Konsole
planningInterface.pingWebSocket()
```

**Dependencies:**
```bash
pip list | grep fastapi
pip install --upgrade -r requirements.txt
```

## 📄 License

MIT License - siehe LICENSE Datei

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen
3. Changes committen  
4. Pull Request erstellen

## 📞 Support

- **Issues:** GitHub Issues
- **Docs:** http://localhost:8000/docs
- **Chat:** WebSocket Interface

---

**Entwickelt mit ❤️ für automatisierte Projektplanung**