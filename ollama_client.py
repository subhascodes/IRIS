"""
Ollama API client for querying Qwen 7B locally.
No external API calls - runs on your machine.
"""

import requests
import json
from typing import Optional

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2:7b"


def query_qwen(
    prompt: str,
    system_context: Optional[str] = None,
    temperature: float = 0.7,
    timeout: int = 60
) -> str:
    """
    Query Qwen 7B via Ollama.
    
    Args:
        prompt: User question
        system_context: System message (role/context)
        temperature: 0.0-1.0 (lower=deterministic, higher=creative)
        timeout: Request timeout in seconds
    
    Returns:
        Model response text
    
    Raises:
        ConnectionError: If Ollama not running
        requests.Timeout: If response slow
    """
    
    messages = []
    
    if system_context:
        messages.append({"role": "system", "content": system_context})
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "temperature": temperature,
                "stream": False
            },
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise ConnectionError(
                f"Ollama error {response.status_code}: {response.text}"
            )
        
        result = response.json()
        return result["message"]["content"]
    
    except requests.ConnectionError:
        raise ConnectionError(
            "❌ Ollama not running. Start with: ollama serve"
        )
    except requests.Timeout:
        raise requests.Timeout(
            f"⏱️ Qwen took too long ({timeout}s timeout)"
        )


def check_ollama_running() -> bool:
    """
    Check if Ollama service is available.
    
    Returns:
        True if running, False otherwise
    """
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=2
        )
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def get_available_models() -> list:
    """
    Get list of available models in Ollama.
    
    Returns:
        List of model names
    """
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except:
        pass
    return []
