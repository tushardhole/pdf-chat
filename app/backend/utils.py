import json
import os

import chromadb
from chromadb.config import Settings
from chromadb.api import ClientAPI

# ------------------------------
# Paths and basic setup
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
META_FILE = os.path.join(DATA_DIR, "metadata.json")
SETTING_JSON = os.path.join(DATA_DIR, "settings.json")

COLLECTION_NAME = "pdf_chunks"
CHROMA_CLIENT: ClientAPI | None = None

def load_metadata():
    with open(META_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_metadata(meta):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def get_chroma_client() -> chromadb.PersistentClient:
    global CHROMA_CLIENT

    if CHROMA_CLIENT is None:
        CHROMA_CLIENT = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(allow_reset=False),
        )

    return CHROMA_CLIENT

def get_chunk_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)

def _initialize():
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)

    if not os.path.exists(META_FILE):
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump({"pdfs": {}}, f)

    client = get_chroma_client()

    existing_collections = {c.name for c in client.list_collections()}
    if COLLECTION_NAME not in existing_collections:
        client.create_collection(name=COLLECTION_NAME)

_initialize()
