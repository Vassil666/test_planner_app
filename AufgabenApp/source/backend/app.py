#!/usr/bin/env python3
"""
app.py - Hauptserver für das automatisierte Planungs-Interface
FastAPI-Server mit WebSocket-Support für Real-time Graph-Updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Konfiguration laden  
config_path = Path(__file__).parent.parent.parent / "config" / "app_config.env"
config_path = config_path.resolve()  # Absoluter Pfad
if config_path.exists():
    load_dotenv(config_path)
    print(f"✅ Konfiguration geladen: {config_path}")
else:
    print(f"⚠️ Konfigurationsdatei nicht gefunden: {config_path}")
    load_dotenv()  # Fallback zu .env oder Umgebungsvariablen

# Lokale Imports
sys.path.append(os.path.dirname(__file__))
from Input2Plan import LLMClient, LLMProvider
from Plan2Graph import PlanGraphConverter
from CytoscapeShow import CytoscapeVisualizer
from Cytoscape2Graph import Cytoscape2GraphConverter
from neo4j_manager import Neo4jManager
from version_manager import GraphVersionManager

# FastAPI App initialisieren
app = FastAPI(
    title="Automatisiertes Planungs-Interface",
    description="Web-Interface für LLM-basierte Projektplanung mit Neo4j-Integration",
    version="1.0.0"
)

# CORS für Frontend-Zugriff  
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globale Manager-Instanzen
version_manager = GraphVersionManager()
neo4j_manager = Neo4jManager()
active_connections: Dict[str, WebSocket] = {}

# Frontend Pfad definieren
frontend_path = Path(__file__).parent.parent / "frontend"

@app.on_event("startup")
async def startup_event():
    """Server-Startup Event"""
    print("🚀 Starte Automatisiertes Planungs-Interface...")
    print(f"📁 Frontend Pfad: {frontend_path}")
    
    # Neo4j Verbindung testen
    if await neo4j_manager.test_connection():
        print("✅ Neo4j Verbindung erfolgreich")
    else:
        print("⚠️ Neo4j Verbindung fehlgeschlagen - prüfe Konfiguration")

@app.on_event("shutdown")
async def shutdown_event():
    """Server-Shutdown Event"""
    print("🛑 Server wird heruntergefahren...")
    await neo4j_manager.close()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"🔗 WebSocket verbunden: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"🔌 WebSocket getrennt: {client_id}")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# === API Endpoints ===

@app.get("/")
async def root():
    """Hauptseite - Frontend HTML"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        with open(frontend_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <h1>🚀 Automatisiertes Planungs-Interface</h1>
        <p>Frontend wird geladen...</p>
        <script>setTimeout(() => location.reload(), 2000);</script>
        """)

@app.post("/api/generate-plan")
async def generate_plan(
    background_tasks: BackgroundTasks,
    request: Dict[str, Any]
):
    """
    Generiert Plan via LLM und erstellt Version 1 im Neo4j
    """
    try:
        goal = request.get("goal", "").strip()
        provider = request.get("provider", "ollama")
        
        if not goal:
            raise HTTPException(status_code=400, detail="Kein Ziel angegeben")
        
        # LLM Provider vorbereiten
        if provider.lower() == "ollama":
            llm_provider = LLMProvider.OLLAMA
        elif provider.lower() == "claude":
            llm_provider = LLMProvider.CLAUDE
        elif provider.lower() == "chatgpt":
            llm_provider = LLMProvider.CHATGPT
        else:
            raise HTTPException(status_code=400, detail=f"Unbekannter LLM Provider: {provider}")
        
        llm_client = LLMClient(llm_provider)
        
        print(f"🤖 Generiere Plan für: '{goal}' mit {provider}")
        
        # Plan von LLM generieren
        plan_data = await llm_client.generate_plan(goal)
        
        if "error" in plan_data:
            raise HTTPException(status_code=500, detail=f"LLM Fehler: {plan_data['error']}")
        
        # Plan zu Graph konvertieren
        converter = PlanGraphConverter()
        graph = converter.json_to_networkx(plan_data)
        
        # Graph-ID generieren
        graph_id = str(uuid.uuid4())
        
        # Version 1 erstellen und in Neo4j speichern
        version_info = await version_manager.create_version(
            graph_id=graph_id,
            version=1,
            source="llm_generated",
            data=plan_data,
            graph=graph
        )
        
        # Background Task für Neo4j Update
        background_tasks.add_task(
            update_neo4j_background,
            graph_id,
            1,
            converter.generate_cypher_statements()
        )
        
        # Cytoscape-Elemente für Frontend generieren
        visualizer = CytoscapeVisualizer()
        cytoscape_elements = visualizer.networkx_to_cytoscape(graph)
        
        return JSONResponse({
            "success": True,
            "graph_id": graph_id,
            "version": 1,
            "plan_data": plan_data,
            "cytoscape_elements": cytoscape_elements,
            "version_info": version_info.to_dict(),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Fehler bei Plan-Generierung: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-graph")
async def update_graph(
    background_tasks: BackgroundTasks,
    request: Dict[str, Any]
):
    """
    Aktualisiert Graph basierend auf Cytoscape-Edits und erstellt Version 2
    """
    try:
        graph_id = request.get("graph_id")
        cytoscape_elements = request.get("elements", [])
        
        if not graph_id or not cytoscape_elements:
            raise HTTPException(status_code=400, detail="Graph-ID oder Elemente fehlen")
        
        print(f"🔄 Aktualisiere Graph {graph_id} mit {len(cytoscape_elements)} Elementen")
        
        # Cytoscape zu Graph konvertieren
        converter = Cytoscape2GraphConverter()
        converter.load_cytoscape_json(cytoscape_elements)
        updated_graph = converter.cytoscape_to_networkx()
        
        # Version 2 erstellen
        version_info = await version_manager.create_version(
            graph_id=graph_id,
            version=2,
            source="user_edited",
            data={"elements": cytoscape_elements},
            graph=updated_graph
        )
        
        # Background Task für Neo4j Update
        cypher_statements = converter.cytoscape_to_cypher()
        background_tasks.add_task(
            update_neo4j_background,
            graph_id,
            2,
            cypher_statements
        )
        
        # WebSocket Broadcast für Live-Updates
        await manager.broadcast({
            "type": "graph_updated",
            "graph_id": graph_id,
            "version": 2,
            "timestamp": datetime.now().isoformat()
        })
        
        return JSONResponse({
            "success": True,
            "graph_id": graph_id,
            "version": 2,
            "version_info": version_info.to_dict(),
            "cypher_statements_count": len(cypher_statements),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Fehler bei Graph-Update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/{graph_id}")
async def get_graph(graph_id: str, version: Optional[int] = None):
    """
    Lädt spezifischen Graph und Version
    """
    try:
        graph_info = await version_manager.get_version(graph_id, version)
        
        if not graph_info:
            raise HTTPException(status_code=404, detail="Graph nicht gefunden")
        
        # GraphVersion-Objekt zu dict konvertieren
        if hasattr(graph_info, 'to_dict'):
            return JSONResponse(graph_info.to_dict())
        else:
            return JSONResponse(graph_info)
        
    except Exception as e:
        print(f"❌ Fehler beim Laden des Graphs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graphs")
async def list_graphs():
    """
    Listet alle verfügbaren Graphen auf
    """
    try:
        graphs = await version_manager.list_graphs()
        return JSONResponse(graphs)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Graph-Liste: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/graph/{graph_id}")
async def delete_graph(graph_id: str):
    """
    Löscht Graph und alle Versionen
    """
    try:
        success = await version_manager.delete_graph(graph_id)
        
        if success:
            # Auch aus Neo4j löschen
            await neo4j_manager.delete_graph(graph_id)
            
            # WebSocket Broadcast
            await manager.broadcast({
                "type": "graph_deleted",
                "graph_id": graph_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return JSONResponse({"success": True, "message": "Graph gelöscht"})
        else:
            raise HTTPException(status_code=404, detail="Graph nicht gefunden")
            
    except Exception as e:
        print(f"❌ Fehler beim Löschen des Graphs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/neo4j/status")
async def neo4j_status():
    """
    Prüft Neo4j Verbindungsstatus
    """
    try:
        is_connected = await neo4j_manager.test_connection()
        
        return JSONResponse({
            "connected": is_connected,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

# === WebSocket Endpoint ===

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket für Real-time Updates
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Warte auf Nachrichten vom Client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo zurück für Ping-Test
            if message.get("type") == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# === Background Tasks ===

async def update_neo4j_background(graph_id: str, version: int, cypher_statements: List[str]):
    """
    Background Task für Neo4j Updates
    """
    try:
        print(f"🔄 Neo4j Update für Graph {graph_id} Version {version}")
        
        # Neo4j Namespace für Version
        namespace = f"{graph_id}_v{version}"
        
        # Alte Version löschen falls vorhanden
        await neo4j_manager.clear_namespace(namespace)
        
        # Neue Statements ausführen
        for statement in cypher_statements:
            # Statement anpassen für Namespace
            namespaced_statement = statement.replace("CREATE (", f"CREATE ({namespace}_")
            await neo4j_manager.execute_query(namespaced_statement)
        
        print(f"✅ Neo4j Update abgeschlossen: {len(cypher_statements)} Statements")
        
        # WebSocket Broadcast über Completion
        await manager.broadcast({
            "type": "neo4j_updated",
            "graph_id": graph_id,
            "version": version,
            "statements_count": len(cypher_statements),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Fehler bei Neo4j Background Update: {e}")
        
        # Fehler an WebSocket senden
        await manager.broadcast({
            "type": "neo4j_error",
            "graph_id": graph_id,
            "version": version,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

# === Gesundheitscheck ===

@app.get("/api/health")
async def health_check():
    """
    Gesundheitscheck für alle Services
    """
    try:
        neo4j_ok = await neo4j_manager.test_connection()
        
        return JSONResponse({
            "status": "healthy",
            "services": {
                "api": True,
                "neo4j": neo4j_ok,
                "websocket": len(manager.active_connections) > 0
            },
            "active_connections": len(manager.active_connections),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=503)

# === Static Files Mount (nach allen API-Routen) ===

# Static Files für Frontend
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# === Server Start ===

if __name__ == "__main__":
    print("🌐 Starte Automatisiertes Planungs-Interface")
    print("📋 API Dokumentation: http://localhost:8000/docs")
    print("🔗 WebSocket Test: ws://localhost:8000/ws/test-client")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )