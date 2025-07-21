from neo4j import GraphDatabase
import sys

#https://console-preview.neo4j.io/projects/905ad068-a364-520b-82e8-40e62cc8efdd/instances

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j+s://2560410f.databases.neo4j.io:7687"
AUTH = ("neo4j", "90tlZVxa3R8dc3UwE4zuXViQLRjDW_MG_Xba-39Q1mc")  # Changed to 'neo4j' username

try:
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("✅ Erfolgreich mit Neo4j Aura verbunden!")
        
        # Test query
        with driver.session() as session:
            result = session.run("RETURN 'Hello Neo4j!' as message")
            for record in result:
                print(f"📝 Test: {record['message']}")
                
except Exception as e:
    print(f"❌ Verbindungsfehler: {e}")
    print("\n🔧 Prüfe:")
    print("1. URI korrekt? (mit :7687 Port)")
    print("2. Username 'neo4j' statt Email?")
    print("3. Passwort korrekt?")
    print("4. Neo4j Aura DB gestartet?")
    sys.exit(1)