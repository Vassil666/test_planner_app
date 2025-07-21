#!/usr/bin/env python3
"""
myOracle.py - Oracle Cloud Database Verbindung
Verbindung zu Oracle Autonomous Database (ATP/ADW) in Oracle Cloud
"""

import oracledb
import sys
import os
from typing import Dict, Any, List
import requests

# Oracle Cloud Database Konfiguration
# Ersetze diese Werte mit deinen Oracle Cloud Credentials
ORACLE_CONFIG = {
    "user": "ADMIN",  # Dein Oracle DB Username (meist ADMIN)
    "password": "HareKrishna2024!",  # Dein Oracle DB Passwort
    "dsn": "WNPY0OKH9TKLQVVQ_high",  # Connection String (z.B. "mydb_high")
    "config_dir": "./wallet",  # Pfad zum Wallet-Verzeichnis
    "wallet_location": "./wallet",  # Pfad zum Wallet
    "wallet_password": "ManOMan25!"  # Wallet-Passwort (falls gesetzt)
}

class OracleCloudConnection:
    """Oracle Cloud Database Verbindungsklasse"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        
    def connect(self) -> bool:
        """Stellt Verbindung zur Oracle Cloud DB her"""
        try:
            # Thick Mode für Wallet-Unterstützung aktivieren
            if not oracledb.is_thin_mode():
                print("🔧 Oracle Client im Thick Mode")
            else:
                print("⚠️ Aktiviere Thick Mode für Wallet-Unterstützung...")
                try:
                    oracledb.init_oracle_client(lib_dir='/Users/vassil/Downloads/instantclient_23_3')
                except Exception as e:
                    print(f"⚠️ Thick Mode konnte nicht aktiviert werden: {e}")
                    print("💡 Versuche Thin Mode mit Easy Connect...")
            print('hey yoiu' , requests.get("https://ipinfo.io/ip").text)

            # Verbindung herstellen
            if self.config.get("config_dir") and os.path.exists(self.config["config_dir"]):
                # Mit Wallet verbinden
                print(f"🔐 Verbinde mit Wallet aus: {self.config['config_dir']}")
                self.connection = oracledb.connect(
                    user=self.config["user"],
                    password=self.config["password"],
                    dsn=self.config["dsn"],
                    config_dir=self.config["config_dir"],
                    wallet_location=self.config["wallet_location"],
                    wallet_password=self.config.get("wallet_password")
                )
            else:
                # Ohne Wallet (Easy Connect)
                print("🌐 Verbinde ohne Wallet (Easy Connect)")
                # Format: host:port/service_name
                dsn = self.config["dsn"]
                self.connection = oracledb.connect(
                    user=self.config["user"],
                    password=self.config["password"],
                    dsn=dsn
                )
            
            print("✅ Erfolgreich mit Oracle Cloud Database verbunden!")
            return True
            
        except oracledb.Error as e:
            print(f"❌ Oracle Datenbankfehler: {e}")
            return False
        except Exception as e:
            print(f"❌ Allgemeiner Fehler: {e}")
            return False
    
    def test_connection(self):
        """Testet die Datenbankverbindung"""
        if not self.connection:
            print("❌ Keine aktive Verbindung!")
            return False
            
        try:
            with self.connection.cursor() as cursor:
                # Basis-Test Query
                cursor.execute("SELECT 'Hello Oracle Cloud!' as message FROM dual")
                result = cursor.fetchone()
                print(f"📝 Test: {result[0]}")
                
                # Datenbankinfo abfragen
                cursor.execute("""
                    SELECT 
                        sys_context('USERENV', 'DB_NAME') as db_name,
                        sys_context('USERENV', 'SERVICE_NAME') as service_name,
                        sys_context('USERENV', 'SERVER_HOST') as server_host
                    FROM dual
                """)
                
                db_info = cursor.fetchone()
                print(f"🏢 Datenbank: {db_info[0]}")
                print(f"🔗 Service: {db_info[1]}")
                print(f"🖥️ Host: {db_info[2]}")
                
                # Version abfragen
                cursor.execute("SELECT banner FROM v$version WHERE rownum = 1")
                version = cursor.fetchone()
                print(f"📊 Version: {version[0]}")
                
                return True
                
        except oracledb.Error as e:
            print(f"❌ Test-Query Fehler: {e}")
            return False
    
    def execute_query(self, query: str, params: List = None) -> List[Dict]:
        """Führt eine Query aus und gibt Ergebnisse zurück"""
        if not self.connection:
            print("❌ Keine aktive Verbindung!")
            return []
        
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Column names holen
                columns = [desc[0] for desc in cursor.description]
                
                # Daten als Dictionary-Liste zurückgeben
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except oracledb.Error as e:
            print(f"❌ Query-Fehler: {e}")
            return []
    
    def execute_dml(self, query: str, params: List = None) -> bool:
        """Führt INSERT/UPDATE/DELETE aus"""
        if not self.connection:
            print("❌ Keine aktive Verbindung!")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                self.connection.commit()
                print(f"✅ {cursor.rowcount} Zeilen betroffen")
                return True
                
        except oracledb.Error as e:
            print(f"❌ DML-Fehler: {e}")
            self.connection.rollback()
            return False
    
    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.connection:
            self.connection.close()
            print("🔒 Oracle Verbindung geschlossen")


def setup_wallet_info():
    """Zeigt Anleitung für Wallet-Setup"""
    print("""
📋 Oracle Cloud Wallet Setup:

1. In Oracle Cloud Console → Autonomous Database
2. Wähle deine Database aus
3. Klicke auf "DB Connection"
4. Download "Instance Wallet" (ZIP-Datei)
5. Entpacke ZIP in './wallet' Verzeichnis
6. Wallet sollte enthalten:
   - tnsnames.ora
   - sqlnet.ora  
   - cwallet.sso
   - ewallet.p12
   - keystore.jks
   - truststore.jks

7. Connection String aus tnsnames.ora kopieren
   (z.B. "mydb_high", "mydb_medium", "mydb_low")
    """)


def main():
    """Hauptfunktion für Tests"""
    print("🔗 Oracle Cloud Database Verbindungstest")
    print("=" * 50)
    
    # Prüfe ob Wallet existiert
    if not os.path.exists("./wallet"):
        print("⚠️ Wallet-Verzeichnis './wallet' nicht gefunden!")
        setup_wallet_info()
        
        # Alternative: Easy Connect versuchen
        use_easy_connect = input("\nEasy Connect ohne Wallet versuchen? (y/n): ").strip().lower()
        if use_easy_connect not in ['y', 'yes', 'ja']:
            sys.exit(1)
        
        # Easy Connect Parameter abfragen
        host = input("Host (z.B. adb.eu-frankfurt-1.oraclecloud.com): ").strip()
        port = input("Port (Standard 1522): ").strip() or "1522"
        service = input("Service Name: ").strip()
        
        ORACLE_CONFIG["dsn"] = f"{host}:{port}/{service}"
        ORACLE_CONFIG["config_dir"] = None
        ORACLE_CONFIG["wallet_location"] = None
    
    # Credentials eingeben
    print("\n🔐 Oracle Credentials:")
    '''username = input(f"Username (Standard: {ORACLE_CONFIG['user']}): ").strip()
    if username:
        ORACLE_CONFIG["user"] = username
    
    password = input("Password: ").strip()
    if password:
        ORACLE_CONFIG["password"] = password
    
    if ORACLE_CONFIG["config_dir"]:
        dsn = input(f"Connection String (z.B. mydb_high): ").strip()
        if dsn:
            ORACLE_CONFIG["dsn"] = dsn
    '''
    # Verbindung testen
    print(f"\n🔄 Verbinde zu Oracle Cloud...")
    oracle_conn = OracleCloudConnection(ORACLE_CONFIG)
    
    if oracle_conn.connect():
        print("\n🧪 Teste Verbindung...")
        if oracle_conn.test_connection():
            print("\n✅ Oracle Cloud Database bereit!")
            
            # Beispiel-Query
            print("\n📊 Beispiel-Abfrage:")
            results = oracle_conn.execute_query("""
                SELECT 
                    table_name, 
                    num_rows 
                FROM user_tables 
                WHERE rownum <= 5
            """)
            
            for result in results:
                print(f"  📋 Tabelle: {result.get('TABLE_NAME', 'N/A')}, "
                      f"Zeilen: {result.get('NUM_ROWS', 'N/A')}")
        
        oracle_conn.close()
    else:
        print("\n❌ Verbindung fehlgeschlagen!")
        print("\n🔧 Troubleshooting:")
        print("1. Wallet korrekt entpackt?")
        print("2. Connection String richtig?")
        print("3. Username/Password korrekt?")
        print("4. Firewall/Network OK?")
        print("5. Database gestartet?")


if __name__ == "__main__":
    # Prüfe ob oracledb installiert ist
    try:
        import oracledb
    except ImportError:
        print("❌ Oracle Client nicht installiert!")
        print("📦 Installation:")
        print("   pip install oracledb")
        print("   # oder für ältere Python-Versionen:")
        print("   pip install cx_Oracle")
        sys.exit(1)
    
    main()