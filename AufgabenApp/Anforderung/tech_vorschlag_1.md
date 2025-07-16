# Architektur-Ansatz 1: Modern Web Stack

## UI (Frontend)
- **React.js mit TypeScript** - Typsicherheit und moderne Entwicklung
- **D3.js oder Cytoscape.js** - Netzwerkgraph-Visualisierung mit editierbaren Knoten
- **Material-UI oder Ant Design** - UI-Komponenten für schnelle Entwicklung
- **Redux Toolkit** - State Management für komplexe Graph-Zustände

## Backend (Optionen)

### Option A: Node.js
- **Node.js mit Express.js/Fastify** - Schnelle API-Entwicklung
- **GraphQL API** - Flexible Datenabfragen für Graph-Strukturen
- **OpenAI API oder Anthropic Claude** - LLM-Integration für Planvorschläge
- **WebSocket** - Echtzeit-Updates für kollaborative Bearbeitung

### Option B: Python (Empfohlen)
- **FastAPI** - Moderne, schnelle Python API mit automatischer OpenAPI-Dokumentation
- **Strawberry GraphQL** - GraphQL für Python mit TypeScript-ähnlicher Syntax
- **httpx** - Async HTTP-Client für LLM-API-Calls
- **WebSockets** - Über FastAPI für Echtzeit-Updates
- **LangChain** - Bessere LLM-Integration und Orchestrierung
- **NetworkX** - Graph-Algorithmen für Planoptimierung

## Database
- **Neo4j** - Graphdatenbank für Knoten (Ziele, Projekte, Tasks) und Beziehungen
- **PostgreSQL** - Metadaten, Benutzerinformationen, Ressourcen-Details
- **Redis** - Caching und Sessions für Performance

## Kostenlose Cloud-Deployment-Optionen (Prototyp Phase)

### Backend Hosting

#### Internationale Anbieter
- **Vercel** - Kostenlos für Node.js/Python APIs (serverless functions)
- **Railway** - $5/Monat Startguthaben, danach pay-as-you-go
- **Render** - Kostenloser Tier für Web Services (mit Sleep-Modus)
- **Heroku** - Kostenlose Dyno-Stunden (begrenzt)
- **Fly.io** - Datacenter in Amsterdam/Frankfurt, kostenloser Tier

#### Europäische Anbieter (DSGVO-konform)

**Deutschland:**
- **Hetzner Cloud** - Sehr günstig, €3.29/Monat für VPS, Datacenter Falkenstein/Nürnberg
- **ionos Cloud** - Deutsche Infrastruktur, kostenlose Testphase
- **STRATO** - Deutscher Anbieter mit Cloud-Hosting

**Frankreich:**
- **Scaleway** - Kostenloser Tier verfügbar, €0.007/Stunde, Paris/Amsterdam DC
- **OVHcloud** - Große europäische Alternative, günstige VPS, mehrere EU-Standorte
- **Clever Cloud** - Kostenloser Tier für kleine Apps, PaaS für Python/Node.js
- **Platform.sh** - 30-Tage-Trial, spezialisiert auf Web-Apps

**Niederlande:**
- **DigitalOcean Amsterdam** - Europäische Datacenter, $6/Monat VPS

### Datenbanken
- **Neo4j AuraDB Free** - Kostenlose Graphdatenbank (50.000 Knoten, 175.000 Beziehungen)
- **PostgreSQL:**
  - **Neon** - Kostenlos 10GB
  - **Supabase** - Kostenlos 500MB + Auth
  - **ElephantSQL** - Kostenlos 20MB
- **Redis:**
  - **Upstash** - Kostenlos 10.000 Requests/Tag
  - **Redis Cloud** - Kostenlos 30MB

### Frontend Hosting
- **Vercel** - Kostenlos für React-Apps
- **Netlify** - Kostenlos mit CI/CD
- **GitHub Pages** - Kostenlos für statische Sites

### Empfohlene Prototyp-Kombinationen

#### Internationale Lösung (Kostenlos)
1. **Frontend**: Vercel (React deployment)
2. **Backend**: Render Free Tier oder Railway
3. **Graphdatenbank**: Neo4j AuraDB Free
4. **Relational DB**: Neon PostgreSQL
5. **Cache**: Upstash Redis
6. **LLM**: OpenAI API (Pay-per-use, günstig für Prototyp)

#### Europäische Lösung (DSGVO-konform)
1. **Frontend**: Vercel (React deployment)
2. **Backend**: Scaleway (kostenloser Tier) oder Clever Cloud
3. **Graphdatenbank**: Neo4j AuraDB Free (EU-Datacenter verfügbar)
4. **Relational DB**: Neon PostgreSQL (EU-Region) oder OVHcloud PostgreSQL
5. **Cache**: Upstash Redis (EU-Region)
6. **LLM**: OpenAI API (pay-per-use) oder lokale Modelle

#### Günstige EU-Lösung (nach Prototyp)
1. **Frontend**: Vercel
2. **Backend**: Hetzner Cloud VPS (€3.29/Monat)
3. **Graphdatenbank**: Neo4j Community auf Hetzner
4. **Relational DB**: PostgreSQL auf Hetzner
5. **Cache**: Redis auf Hetzner
6. **LLM**: Lokale Modelle (Ollama) oder OpenAI API

**Empfehlung**: Für Prototyping mit **Scaleway** oder **Clever Cloud** starten, später zu **Hetzner** wechseln für Production.