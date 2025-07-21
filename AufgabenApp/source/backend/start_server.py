#!/usr/bin/env python3
"""
start_server.py - Server-Starter für das automatisierte Planungs-Interface
Einfacher Starter-Script mit Umgebungsprüfung und Konfiguration
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
from dotenv import load_dotenv

def check_requirements():
    """Prüft ob alle Requirements installiert sind"""
    try:
        import fastapi
        import uvicorn
        import websockets
        import networkx
        import neo4j
        print("✅ Alle Requirements verfügbar")
        return True
    except ImportError as e:
        print(f"❌ Fehlende Dependency: {e}")
        print("💡 Führe aus: pip install -r requirements.txt")
        return False

def check_environment():
    """Prüft Umgebungsvariablen und Konfiguration"""
    issues = []
    
    # Neo4j Konfiguration prüfen
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not neo4j_uri:
        issues.append("⚠️ NEO4J_URI nicht gesetzt - verwende Standard")
    
    if not neo4j_password:
        issues.append("⚠️ NEO4J_PASSWORD nicht gesetzt - verwende Standard")
    
    # LLM API Keys prüfen
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not anthropic_key:
        issues.append("⚠️ ANTHROPIC_API_KEY nicht gesetzt - Claude nicht verfügbar")
    
    if not openai_key:
        issues.append("⚠️ OPENAI_API_KEY nicht gesetzt - ChatGPT nicht verfügbar")
    
    # Ollama prüfen
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama verfügbar")
        else:
            issues.append("⚠️ Ollama nicht verfügbar - nur API-LLMs nutzbar")
    except FileNotFoundError:
        issues.append("⚠️ Ollama nicht installiert - nur API-LLMs nutzbar")
    
    if issues:
        print("\n".join(issues))
        print("\n💡 Das System ist trotzdem funktionsfähig.")
    
    return True

def setup_directories():
    """Erstellt notwendige Verzeichnisse"""
    directories = [
        "graph_versions",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Verzeichnis erstellt: {directory}")

async def check_services():
    """Prüft externe Services"""
    print("🔍 Prüfe externe Services...")
    
    # Neo4j testen
    try:
        from neo4j_manager import Neo4jManager
        manager = Neo4jManager()
        
        if await manager.test_connection():
            print("✅ Neo4j Verbindung OK")
        else:
            print("❌ Neo4j Verbindung fehlgeschlagen")
            
        await manager.close()
    except Exception as e:
        print(f"❌ Neo4j Test fehlgeschlagen: {e}")

def print_startup_info():
    """Zeigt Startup-Informationen"""
    print("=" * 60)
    print("🚀 AUTOMATISIERTES PLANUNGS-INTERFACE")
    print("=" * 60)
    print("📋 LLM-basierte Projektplanung mit Neo4j-Integration")
    print("🌐 Web-Interface: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/ws/test-client")
    print("=" * 60)

def print_usage_instructions():
    """Zeigt Nutzungsanweisungen"""
    print("""
🎯 NUTZUNG:

1. 📝 Projekt beschreiben:
   - Öffne http://localhost:8000
   - Gib dein Ziel/Projekt ein
   - Wähle LLM-Provider (Ollama/Claude/ChatGPT)
   - Klicke "Plan Generieren"

2. 🎨 Graph bearbeiten:
   - Aktiviere Edit-Modus
   - Bearbeite Knoten und Kanten
   - Änderungen werden automatisch gespeichert
   - Version 2 wird parallel in Neo4j erstellt

3. 💾 Graph verwalten:
   - Speichere und lade verschiedene Graphen
   - Betrachte verschiedene Versionen
   - Exportiere als Bild

4. 🔍 Neo4j erkunden:
   - Verbinde zu Neo4j Browser
   - URI: neo4j+s://2560410f.databases.neo4j.io:7687
   - Username: neo4j
   - Passwort: siehe myNeo.py

⚡ Features:
- Real-time WebSocket Updates
- Parallel Version Management
- Interactive Cytoscape.js Editor
- Multiple LLM Provider Support
- Neo4j Cloud Integration
    """)

def load_config():
    """Lädt Konfigurationsdatei"""
    config_path = Path(__file__).parent.parent.parent / "config" / "app_config.env"
    config_path = config_path.resolve()  # Absoluter Pfad
    if config_path.exists():
        load_dotenv(config_path)
        print(f"✅ Konfiguration geladen: {config_path}")
        return True
    else:
        print(f"⚠️ Konfigurationsdatei nicht gefunden: {config_path}")
        print("💡 Erstelle config/app_config.env mit deinen API-Keys")
        load_dotenv()  # Fallback zu Standard .env
        return False

def main():
    """Haupt-Startfunktion"""
    print_startup_info()
    
    # Konfiguration laden
    load_config()
    
    # System prüfen
    if not check_requirements():
        sys.exit(1)
    
    # Umgebung prüfen
    check_environment()
    
    # Verzeichnisse setup
    setup_directories()
    
    # Services prüfen
    try:
        asyncio.run(check_services())
    except Exception as e:
        print(f"⚠️ Service-Check fehlgeschlagen: {e}")
    
    print_usage_instructions()
    
    print("🚀 Starte Server...")
    print("🛑 Zum Beenden: Ctrl+C\n")
    
    # Server starten
    try:
        import uvicorn
        
        # App importieren
        sys.path.append(os.path.dirname(__file__))
        
        # Server-Konfiguration aus Environment
        server_host = os.getenv("SERVER_HOST", "0.0.0.0")
        server_port = int(os.getenv("SERVER_PORT", "8000"))
        debug_mode = os.getenv("DEBUG_MODE", "true").lower() == "true"
        
        uvicorn.run(
            "app:app",
            host=server_host,
            port=server_port,
            reload=debug_mode,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server gestoppt durch Benutzer")
    except Exception as e:
        print(f"❌ Server-Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()