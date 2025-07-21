#!/usr/bin/env python3
"""
version_manager.py - Graph Version Management System
Verwaltet verschiedene Versionen von Graphen (LLM-generiert vs User-editiert)
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import uuid
import pickle
import networkx as nx
from dataclasses import dataclass, asdict
import os

@dataclass
class GraphVersion:
    """Datenstruktur für Graph-Versionen"""
    graph_id: str
    version: int
    source: str  # 'llm_generated', 'user_edited'
    created_at: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    file_path: Optional[str] = None
    neo4j_namespace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class GraphVersionManager:
    """
    Verwaltet Graph-Versionen im lokalen Dateisystem
    """
    
    def __init__(self, storage_dir: str = None):
        """Initialisiert Version Manager"""
        
        self.storage_dir = Path(storage_dir) if storage_dir else Path("graph_versions")
        self.storage_dir.mkdir(exist_ok=True)
        
        # Metadaten-Datei
        self.metadata_file = self.storage_dir / "versions_metadata.json"
        
        # In-Memory Cache
        self.versions_cache: Dict[str, Dict[int, GraphVersion]] = {}
        
        print(f"📁 Version Manager initialisiert: {self.storage_dir}")
        
        # Existierende Versionen laden
        asyncio.create_task(self._load_existing_versions())
    
    async def _load_existing_versions(self):
        """Lädt existierende Versionen beim Start"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                for graph_id, versions_data in metadata.items():
                    self.versions_cache[graph_id] = {}
                    for version_str, version_data in versions_data.items():
                        version_num = int(version_str)
                        version_obj = GraphVersion(**version_data)
                        self.versions_cache[graph_id][version_num] = version_obj
                
                total_versions = sum(len(versions) for versions in self.versions_cache.values())
                print(f"📋 {total_versions} Versionen aus {len(self.versions_cache)} Graphen geladen")
        
        except Exception as e:
            print(f"⚠️ Fehler beim Laden existierender Versionen: {e}")
            self.versions_cache = {}
    
    async def _save_metadata(self):
        """Speichert Metadaten persistent"""
        try:
            metadata = {}
            for graph_id, versions in self.versions_cache.items():
                metadata[graph_id] = {}
                for version_num, version_obj in versions.items():
                    metadata[graph_id][str(version_num)] = version_obj.to_dict()
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Metadaten: {e}")
    
    def _generate_file_path(self, graph_id: str, version: int, file_type: str) -> Path:
        """Generiert Dateipfad für Graph-Daten"""
        graph_dir = self.storage_dir / graph_id
        graph_dir.mkdir(exist_ok=True)
        
        return graph_dir / f"v{version}_{file_type}"
    
    async def create_version(self, 
                           graph_id: str, 
                           version: int, 
                           source: str,
                           data: Dict[str, Any],
                           graph: nx.DiGraph = None,
                           metadata: Dict[str, Any] = None) -> GraphVersion:
        """
        Erstellt neue Graph-Version
        """
        try:
            # Metadaten vorbereiten
            if not metadata:
                metadata = {}
            
            metadata.update({
                "nodes_count": graph.number_of_nodes() if graph else 0,
                "edges_count": graph.number_of_edges() if graph else 0,
                "source": source
            })
            
            # Version-Objekt erstellen
            version_obj = GraphVersion(
                graph_id=graph_id,
                version=version,
                source=source,
                created_at=datetime.now().isoformat(),
                data=data,
                metadata=metadata,
                neo4j_namespace=f"{graph_id}_v{version}"
            )
            
            # Daten in Dateien speichern
            if data:
                json_path = self._generate_file_path(graph_id, version, "data.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                version_obj.file_path = str(json_path)
            
            # NetworkX Graph speichern
            if graph:
                graph_path = self._generate_file_path(graph_id, version, "graph.pickle")
                with open(graph_path, 'wb') as f:
                    pickle.dump(graph, f)
            
            # In Cache speichern
            if graph_id not in self.versions_cache:
                self.versions_cache[graph_id] = {}
            
            self.versions_cache[graph_id][version] = version_obj
            
            # Metadaten persistieren
            await self._save_metadata()
            
            print(f"✅ Version erstellt: {graph_id} v{version} ({source})")
            return version_obj
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Version: {e}")
            raise
    
    async def get_version(self, graph_id: str, version: Optional[int] = None) -> Optional[GraphVersion]:
        """
        Lädt spezifische Graph-Version
        """
        try:
            if graph_id not in self.versions_cache:
                return None
            
            versions = self.versions_cache[graph_id]
            
            if version is None:
                # Neueste Version
                if not versions:
                    return None
                latest_version = max(versions.keys())
                return versions[latest_version]
            
            return versions.get(version)
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der Version: {e}")
            return None
    
    async def get_graph_data(self, graph_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Lädt Graph-Daten aus Datei
        """
        try:
            version_obj = await self.get_version(graph_id, version)
            if not version_obj or not version_obj.file_path:
                return None
            
            file_path = Path(version_obj.file_path)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"❌ Fehler beim Laden der Graph-Daten: {e}")
            return None
    
    async def get_networkx_graph(self, graph_id: str, version: Optional[int] = None) -> Optional[nx.DiGraph]:
        """
        Lädt NetworkX Graph aus Datei
        """
        try:
            version_obj = await self.get_version(graph_id, version)
            if not version_obj:
                return None
            
            graph_path = self._generate_file_path(graph_id, version_obj.version, "graph.pickle")
            
            if not graph_path.exists():
                return None
            
            with open(graph_path, 'rb') as f:
                return pickle.load(f)
                
        except Exception as e:
            print(f"❌ Fehler beim Laden des NetworkX Graphs: {e}")
            return None
    
    async def list_graphs(self) -> List[Dict[str, Any]]:
        """
        Listet alle verfügbaren Graphen auf
        """
        try:
            graphs = []
            
            for graph_id, versions in self.versions_cache.items():
                if not versions:
                    continue
                
                # Neueste Version finden
                latest_version_num = max(versions.keys())
                latest_version = versions[latest_version_num]
                
                # Alle Versionen sammeln
                version_list = []
                for v_num, v_obj in sorted(versions.items()):
                    version_list.append({
                        "version": v_num,
                        "source": v_obj.source,
                        "created_at": v_obj.created_at,
                        "metadata": v_obj.metadata
                    })
                
                graphs.append({
                    "graph_id": graph_id,
                    "latest_version": latest_version_num,
                    "total_versions": len(versions),
                    "created_at": latest_version.created_at,
                    "source": latest_version.source,
                    "metadata": latest_version.metadata,
                    "versions": version_list
                })
            
            # Nach Erstellungsdatum sortieren
            graphs.sort(key=lambda x: x["created_at"], reverse=True)
            
            return graphs
            
        except Exception as e:
            print(f"❌ Fehler beim Auflisten der Graphen: {e}")
            return []
    
    async def delete_graph(self, graph_id: str) -> bool:
        """
        Löscht Graph und alle Versionen
        """
        try:
            if graph_id not in self.versions_cache:
                return False
            
            # Dateien löschen
            graph_dir = self.storage_dir / graph_id
            if graph_dir.exists():
                import shutil
                shutil.rmtree(graph_dir)
            
            # Aus Cache entfernen
            del self.versions_cache[graph_id]
            
            # Metadaten aktualisieren
            await self._save_metadata()
            
            print(f"🗑️ Graph gelöscht: {graph_id}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Löschen des Graphs: {e}")
            return False
    
    async def delete_version(self, graph_id: str, version: int) -> bool:
        """
        Löscht spezifische Version eines Graphs
        """
        try:
            if graph_id not in self.versions_cache:
                return False
            
            if version not in self.versions_cache[graph_id]:
                return False
            
            version_obj = self.versions_cache[graph_id][version]
            
            # Dateien löschen
            if version_obj.file_path:
                file_path = Path(version_obj.file_path)
                if file_path.exists():
                    file_path.unlink()
            
            graph_path = self._generate_file_path(graph_id, version, "graph.pickle")
            if graph_path.exists():
                graph_path.unlink()
            
            # Aus Cache entfernen
            del self.versions_cache[graph_id][version]
            
            # Wenn keine Versionen mehr, Graph-Dir löschen
            if not self.versions_cache[graph_id]:
                del self.versions_cache[graph_id]
                graph_dir = self.storage_dir / graph_id
                if graph_dir.exists():
                    graph_dir.rmdir()
            
            # Metadaten aktualisieren
            await self._save_metadata()
            
            print(f"🗑️ Version gelöscht: {graph_id} v{version}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Löschen der Version: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Gibt Storage-Statistiken zurück
        """
        try:
            total_graphs = len(self.versions_cache)
            total_versions = sum(len(versions) for versions in self.versions_cache.values())
            
            # Dateigröße berechnen
            total_size = 0
            file_count = 0
            
            for path in self.storage_dir.rglob("*"):
                if path.is_file():
                    total_size += path.stat().st_size
                    file_count += 1
            
            return {
                "storage_directory": str(self.storage_dir),
                "total_graphs": total_graphs,
                "total_versions": total_versions,
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Fehler beim Berechnen der Storage-Stats: {e}")
            return {"error": str(e)}

# Test-Funktionen
async def test_version_manager():
    """Test-Funktion für Version Manager"""
    print("🧪 Teste Version Manager...")
    
    manager = GraphVersionManager()
    
    # Test-Graph erstellen
    test_graph = nx.DiGraph()
    test_graph.add_node("n1", name="Test Node 1")
    test_graph.add_node("n2", name="Test Node 2")
    test_graph.add_edge("n1", "n2", relationship="TEST")
    
    # Test-Daten
    test_data = {
        "objective": "Test Objective",
        "projects": [{"name": "Test Project", "tasks": []}]
    }
    
    # Version 1 erstellen
    graph_id = str(uuid.uuid4())
    version1 = await manager.create_version(
        graph_id=graph_id,
        version=1,
        source="llm_generated",
        data=test_data,
        graph=test_graph
    )
    
    print(f"✅ Version 1 erstellt: {version1.graph_id}")
    
    # Version 2 erstellen (editiert)
    test_data["projects"][0]["name"] = "Edited Test Project"
    test_graph.add_node("n3", name="Added Node")
    
    version2 = await manager.create_version(
        graph_id=graph_id,
        version=2,
        source="user_edited",
        data=test_data,
        graph=test_graph
    )
    
    print(f"✅ Version 2 erstellt: {version2.graph_id}")
    
    # Graphen auflisten
    graphs = await manager.list_graphs()
    print(f"📋 Graphen gefunden: {len(graphs)}")
    
    # Storage Stats
    stats = await manager.get_storage_stats()
    print(f"📊 Storage Stats: {json.dumps(stats, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(test_version_manager())