import requests

from models import *


def ollama_list_models(ollama_url: str) -> List[str]:
    try:
        r = requests.get(f"{ollama_url}/api/tags", timeout=5)
        r.raise_for_status()
        data = r.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []

def ollama_embed(ollama_url: str, model: str, text: str) -> Optional[List[float]]:
    try:
        r = requests.post(
            f"{ollama_url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("embedding")
    except Exception as e:
        print("Embedding error:", e)
        return None

def ollama_chat(ollama_url: str, model: str, prompt: str) -> str:
    r = requests.post(
        f"{ollama_url}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        },
        timeout=240,
    )
    r.raise_for_status()
    data = r.json()
    # Support both streaming-like and single-message schemas
    if "message" in data and isinstance(data["message"], dict):
        return data["message"].get("content", "")
    if "messages" in data and isinstance(data["messages"], list):
        return data["messages"][-1].get("content", "")
    return ""

