# Konfiguration für Automatisiertes Planungs-Interface

## Setup Instructions

### 1. API-Keys konfigurieren

Bearbeite `app_config.env` und füge deine API-Keys ein:

```bash
# OpenAI API Key (für ChatGPT)
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Claude API Key (für Anthropic Claude)  
ANTHROPIC_API_KEY=sk-ant-your-actual-claude-api-key-here
```

### 2. API-Keys erhalten

#### OpenAI API Key
1. Gehe zu https://platform.openai.com/api-keys
2. Erstelle einen neuen API-Key
3. Kopiere ihn in `app_config.env`

#### Claude API Key  
1. Gehe zu https://console.anthropic.com/
2. Erstelle einen neuen API-Key
3. Kopiere ihn in `app_config.env`

### 3. Lokale LLM Alternative (Ollama)

Falls du keine API-Keys haben möchtest, installiere Ollama:

```bash
# Installation (macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Model herunterladen
ollama pull llama3.2

# Server starten
ollama serve
```

### 4. Neo4j Konfiguration

Die Neo4j Aura Cloud Verbindung ist bereits konfiguriert:
- **URI:** neo4j+s://2560410f.databases.neo4j.io:7687
- **Username:** neo4j  
- **Passwort:** bereits gesetzt

### 5. Konfiguration testen

```bash
cd source/backend
python start_server.py
```

Das System zeigt an, welche Services verfügbar sind:
- ✅ = Service verfügbar und konfiguriert
- ⚠️ = Service nicht konfiguriert, aber optional

## Konfigurationsdateien

- `app_config.env` - Haupt-Konfiguration mit API-Keys
- `README.md` - Diese Anleitung

## Umgebungsvariablen Übersicht

| Variable | Beschreibung | Standard |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API Schlüssel | - |
| `ANTHROPIC_API_KEY` | Claude API Schlüssel | - |
| `NEO4J_URI` | Neo4j Datenbank URI | bereits gesetzt |
| `NEO4J_USERNAME` | Neo4j Benutzername | neo4j |
| `NEO4J_PASSWORD` | Neo4j Passwort | bereits gesetzt |
| `SERVER_HOST` | Server IP-Adresse | 0.0.0.0 |
| `SERVER_PORT` | Server Port | 8000 |
| `DEBUG_MODE` | Debug-Modus aktiviert | true |

## Sicherheitshinweise

⚠️ **Wichtig:**
- Teile deine API-Keys niemals öffentlich
- Füge `config/` NICHT zu Git hinzu
- Verwende separate Keys für Development/Production

## Support

Bei Problemen:
1. Prüfe ob alle API-Keys korrekt sind
2. Teste Neo4j Verbindung: `python source/backend/myNeo.py`  
3. Prüfe Server-Logs für Fehlermeldungen
4. Besuche http://localhost:8000/api/health für Status-Check