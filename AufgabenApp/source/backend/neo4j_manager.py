#!/usr/bin/env python3
"""
neo4j_manager.py - Neo4j Database Manager für Graph-Versioning
Erweiterte Neo4j-Integration mit Versioning und Namespace-Support
"""

import asyncio
from neo4j import AsyncGraphDatabase
from typing import Dict, Any, List, Optional
import os
from datetime import datetime
import json

class Neo4jManager:
    """
    Erweiterte Neo4j-Manager-Klasse für Graph-Versioning
    """
    
    def __init__(self, uri: str = None, auth: tuple = None):
        """Initialisiert Neo4j Manager"""
        
        # Standard-Konfiguration aus Environment oder Defaults
        self.uri = uri or os.getenv("NEO4J_URI", "neo4j+s://2560410f.databases.neo4j.io:7687")
        self.auth = auth or (
            os.getenv("NEO4J_USERNAME", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "90tlZVxa3R8dc3UwE4zuXViQLRjDW_MG_Xba-39Q1mc")
        )
        
        self.driver = None
        print(f"🔗 Neo4j Manager initialisiert: {self.uri}")
    
    async def connect(self) -> bool:
        """Stellt Verbindung zur Neo4j-Datenbank her"""
        try:
            if not self.driver:
                self.driver = AsyncGraphDatabase.driver(self.uri, auth=self.auth)
            
            # Verbindung testen
            await self.driver.verify_connectivity()
            print("✅ Neo4j Verbindung erfolgreich")
            return True
            
        except Exception as e:
            print(f"❌ Neo4j Verbindungsfehler: {e}")
            return False
    
    async def close(self):
        """Schließt Neo4j-Verbindung"""
        if self.driver:
            await self.driver.close()
            print("🔒 Neo4j Verbindung geschlossen")
    
    async def test_connection(self) -> bool:
        """Testet Neo4j-Verbindung"""
        try:
            if not self.driver:
                await self.connect()
            
            async with self.driver.session() as session:
                result = await session.run("RETURN 'Neo4j Connection OK' as status")
                record = await result.single()
                
                if record:
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Neo4j Test fehlgeschlagen: {e}")
            return False
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Führt Neo4j Query aus und gibt Ergebnisse zurück
        """
        try:
            if not self.driver:
                await self.connect()
            
            async with self.driver.session() as session:
                if parameters:
                    result = await session.run(query, parameters)
                else:
                    result = await session.run(query)
                
                # Alle Records sammeln
                records = []
                async for record in result:
                    records.append(dict(record))
                
                return records
                
        except Exception as e:
            print(f"❌ Neo4j Query Fehler: {e}")
            print(f"📝 Query: {query}")
            return []
    
    async def execute_write_query(self, query: str, parameters: Dict[str, Any] = None) -> bool:
        """
        Führt Schreib-Query aus (CREATE, UPDATE, DELETE)
        """
        try:
            if not self.driver:
                await self.connect()
            
            async with self.driver.session() as session:
                if parameters:
                    await session.run(query, parameters)
                else:
                    await session.run(query)
                
                return True
                
        except Exception as e:
            print(f"❌ Neo4j Write Query Fehler: {e}")
            print(f"📝 Query: {query}")
            return False
    
    async def create_graph_version(self, graph_id: str, version: int, 
                                 cypher_statements: List[str]) -> bool:
        """
        Erstellt neue Graph-Version in Neo4j
        """
        try:
            namespace = f"{graph_id}_v{version}"
            
            print(f"🔄 Erstelle Neo4j Graph Version: {namespace}")
            
            # Alte Version löschen falls vorhanden
            await self.clear_namespace(namespace)
            
            # Version-Metadaten erstellen
            metadata_query = """
            CREATE (v:GraphVersion {
                graph_id: $graph_id,
                version: $version,
                namespace: $namespace,
                created_at: $timestamp,
                statement_count: $statement_count
            })
            """
            
            await self.execute_write_query(metadata_query, {
                "graph_id": graph_id,
                "version": version,
                "namespace": namespace,
                "timestamp": datetime.now().isoformat(),
                "statement_count": len(cypher_statements)
            })
            
            # Graph-Statements ausführen
            success_count = 0
            for i, statement in enumerate(cypher_statements):
                try:
                    # Namespace zu Node-IDs hinzufügen
                    namespaced_statement = self._add_namespace_to_statement(statement, namespace)
                    await self.execute_write_query(namespaced_statement)
                    success_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Statement {i+1} fehlgeschlagen: {e}")
                    continue
            
            print(f"✅ {success_count}/{len(cypher_statements)} Statements erfolgreich")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Fehler bei Graph-Version-Erstellung: {e}")
            return False
    
    def _add_namespace_to_statement(self, statement: str, namespace: str) -> str:
        """
        Fügt Namespace zu Cypher-Statement hinzu
        """
        # Einfache Namespace-Implementierung - erweitert Node-IDs
        # TODO: Könnte für komplexere Queries erweitert werden
        
        # Ersetze CREATE Patterns
        if "CREATE (" in statement:
            statement = statement.replace("CREATE (", f"CREATE ({namespace}_")
        
        # Ersetze MATCH Patterns 
        if "WHERE a.id =" in statement:
            statement = statement.replace('WHERE a.id =', f'WHERE a.id = "{namespace}_" +')
        if "WHERE b.id =" in statement:
            statement = statement.replace('WHERE b.id =', f'WHERE b.id = "{namespace}_" +')
        
        return statement
    
    async def clear_namespace(self, namespace: str) -> bool:
        """
        Löscht alle Knoten und Kanten eines Namespaces
        """
        try:
            # Lösche alle Knoten mit Namespace-Prefix
            delete_query = f"""
            MATCH (n)
            WHERE n.id STARTS WITH '{namespace}_'
            DETACH DELETE n
            """
            
            await self.execute_write_query(delete_query)
            
            # Lösche Version-Metadaten
            metadata_query = """
            MATCH (v:GraphVersion {namespace: $namespace})
            DELETE v
            """
            
            await self.execute_write_query(metadata_query, {"namespace": namespace})
            
            print(f"🗑️ Namespace gelöscht: {namespace}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Löschen des Namespaces: {e}")
            return False
    
    async def delete_graph(self, graph_id: str) -> bool:
        """
        Löscht alle Versionen eines Graphs
        """
        try:
            # Alle Versionen dieses Graphs finden
            versions_query = """
            MATCH (v:GraphVersion {graph_id: $graph_id})
            RETURN v.namespace as namespace
            """
            
            versions = await self.execute_query(versions_query, {"graph_id": graph_id})
            
            # Jede Version löschen
            for version_record in versions:
                namespace = version_record.get("namespace")
                if namespace:
                    await self.clear_namespace(namespace)
            
            print(f"🗑️ Graph komplett gelöscht: {graph_id}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Löschen des Graphs: {e}")
            return False
    
    async def get_graph_versions(self, graph_id: str) -> List[Dict[str, Any]]:
        """
        Gibt alle Versionen eines Graphs zurück
        """
        try:
            query = """
            MATCH (v:GraphVersion {graph_id: $graph_id})
            RETURN v.version as version, v.namespace as namespace, 
                   v.created_at as created_at, v.statement_count as statement_count
            ORDER BY v.version ASC
            """
            
            return await self.execute_query(query, {"graph_id": graph_id})
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der Graph-Versionen: {e}")
            return []
    
    async def get_graph_data(self, graph_id: str, version: int = None) -> Dict[str, Any]:
        """
        Lädt Graph-Daten aus Neo4j
        """
        try:
            if version:
                namespace = f"{graph_id}_v{version}"
            else:
                # Neueste Version finden
                versions = await self.get_graph_versions(graph_id)
                if not versions:
                    return {}
                namespace = versions[-1].get("namespace")
            
            # Knoten laden
            nodes_query = f"""
            MATCH (n)
            WHERE n.id STARTS WITH '{namespace}_'
            RETURN n
            """
            
            nodes = await self.execute_query(nodes_query)
            
            # Kanten laden
            edges_query = f"""
            MATCH (a)-[r]->(b)
            WHERE a.id STARTS WITH '{namespace}_' AND b.id STARTS WITH '{namespace}_'
            RETURN a.id as source, b.id as target, type(r) as relationship, properties(r) as props
            """
            
            edges = await self.execute_query(edges_query)
            
            return {
                "graph_id": graph_id,
                "version": version,
                "namespace": namespace,
                "nodes": nodes,
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der Graph-Daten: {e}")
            return {}
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Gibt Datenbank-Statistiken zurück
        """
        try:
            # Grundlegende Stats
            stats_query = """
            CALL db.stats.retrieve('GRAPH')
            """
            
            basic_stats = await self.execute_query(stats_query)
            
            # Version-spezifische Stats
            version_query = """
            MATCH (v:GraphVersion)
            RETURN count(v) as total_versions, 
                   count(DISTINCT v.graph_id) as unique_graphs
            """
            
            version_stats = await self.execute_query(version_query)
            
            return {
                "basic_stats": basic_stats,
                "version_stats": version_stats[0] if version_stats else {},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der DB-Stats: {e}")
            return {"error": str(e)}

# Singleton Instance für App-weite Verwendung
neo4j_manager = Neo4jManager()

async def test_neo4j_manager():
    """Test-Funktion für Neo4j Manager"""
    print("🧪 Teste Neo4j Manager...")
    
    manager = Neo4jManager()
    
    # Verbindung testen
    if await manager.test_connection():
        print("✅ Verbindung OK")
        
        # Stats laden
        stats = await manager.get_database_stats()
        print(f"📊 DB Stats: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
    await manager.close()

if __name__ == "__main__":
    asyncio.run(test_neo4j_manager())