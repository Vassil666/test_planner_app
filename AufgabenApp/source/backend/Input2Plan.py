#!/usr/bin/env python3
"""
Input2Plan.py - KI-gestützte Projekt- und Aufgabenplanung
Nimmt Ziel/Projekt-Input entgegen und generiert Plan über LLM
"""

import asyncio
import json
import os
from enum import Enum
from typing import Optional, Dict, Any
import httpx
import subprocess
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(Enum):
    OLLAMA = "ollama"
    CLAUDE = "claude"
    CHATGPT = "chatgpt"


class LLMClient:
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        
    async def generate_plan(self, goal: str) -> Dict[str, Any]:
        """Generiert einen Plan basierend auf dem Ziel"""
        prompt = self._create_planning_prompt(goal)
        
        if self.provider == LLMProvider.OLLAMA:
            return await self._call_ollama(prompt)
        elif self.provider == LLMProvider.CLAUDE:
            return await self._call_claude(prompt)
        elif self.provider == LLMProvider.CHATGPT:
            return await self._call_chatgpt(prompt)
        else:
            raise ValueError(f"Unbekannter LLM Provider: {self.provider}")
    
    def _create_planning_prompt(self, goal: str) -> str:
        return f"""
Erstelle einen detaillierten Projektplan für folgendes Ziel:
"{goal}"

Strukturiere die Antwort als JSON mit folgender Struktur:
{{
    "objective": "{goal}",
    "projects": [
        {{
            "name": "Projektname",
            "description": "Beschreibung",
            "tasks": [
                {{
                    "name": "Aufgabenname",
                    "description": "Aufgabenbeschreibung",
                    "estimated_hours": 8,
                    "dependencies": [],
                    "resources": {{
                        "actors": ["Person/Rolle"],
                        "objects": ["Artefakt"],
                        "knowledge": ["Wissen"],
                        "budget": 0
                    }}
                }}
            ]
        }}
    ]
}}

Denke in konkreten, umsetzbaren Schritten und berücksichtige Abhängigkeiten zwischen Aufgaben.
"""

    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """Ruft lokales OLLAMA-Modell auf"""
        try:
            # Prüfe ob OLLAMA läuft
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("OLLAMA nicht verfügbar. Starte mit: ollama serve")
            
            # Standard-Modell: llama3.2 oder llama2
            model = "llama3.2"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return json.loads(result["response"])
                else:
                    raise Exception(f"OLLAMA Fehler: {response.status_code}")
                    
        except Exception as e:
            print(f"OLLAMA Fehler: {e}")
            return {"error": str(e), "provider": "ollama"}

    async def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """Ruft Claude API auf"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY nicht gesetzt", "provider": "claude"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-sonnet-20240229",
                        "max_tokens": 4000,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["content"][0]["text"]
                    # Extrahiere JSON aus der Antwort
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    return json.loads(content[json_start:json_end])
                else:
                    error_text = response.text
                    raise Exception(f"Claude API Fehler: {response.status_code} - {error_text}")
                    
        except Exception as e:
            print(f"Claude Fehler: {e}")
            return {"error": str(e), "provider": "claude"}

    async def _call_chatgpt(self, prompt: str) -> Dict[str, Any]:
        """Ruft ChatGPT API auf"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OPENAI_API_KEY nicht gesetzt", "provider": "chatgpt"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "system", "content": "Du bist ein Experte für Projektplanung. Antworte immer mit validen JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 4000,
                        "temperature": 0.7
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    # Extrahiere JSON aus der Antwort
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    return json.loads(content[json_start:json_end])
                else:
                    raise Exception(f"OpenAI API Fehler: {response.status_code}")
                    
        except Exception as e:
            print(f"ChatGPT Fehler: {e}")
            return {"error": str(e), "provider": "chatgpt"}


async def main():
    """Hauptfunktion für Tests"""
    print("🎯 KI-gestützte Projekt- und Aufgabenplanung")
    print("=" * 50)
    
    # Benutzereingabe
    goal = input("Geben Sie Ihr Ziel/Projekt ein: ").strip()
    
    if not goal:
        print("❌ Kein Ziel eingegeben!")
        return
    
    # LLM Provider auswählen
    print("\nVerfügbare LLM Provider:")
    print("1. OLLAMA (lokal)")
    print("2. Claude API")
    print("3. ChatGPT API")
    
    choice = input("Wählen Sie einen Provider (1-3): ").strip()
    
    provider_map = {
        "1": LLMProvider.OLLAMA,
        "2": LLMProvider.CLAUDE,
        "3": LLMProvider.CHATGPT
    }
    
    if choice not in provider_map:
        print("❌ Ungültige Auswahl!")
        return
    
    provider = provider_map[choice]
    print(f"🤖 Verwende {provider.value}...")
    
    # Plan generieren
    client = LLMClient(provider)
    
    try:
        print("🔄 Generiere Plan...")
        plan = await client.generate_plan(goal)
        
        if "error" in plan:
            print(f"❌ Fehler: {plan['error']}")
            return
        
        # Plan ausgeben
        print("\n📋 Generierter Plan:")
        print("=" * 50)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        
        # Plan in Datei speichern
        filename = f"plan_{goal.replace(' ', '_')[:20]}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Plan gespeichert in: {filename}")
        
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    asyncio.run(main())