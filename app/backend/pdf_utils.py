import uuid

import fitz

from ollama import *
from utils import *

def extract_pdf_pages(file_path: str) -> List[str]:
    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        text = page.get_text("text")
        text = text.strip()
        if text:
            pages.append(text)
    return pages

def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    # Simple chunker: split by paragraphs, then pack
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 <= max_chars:
            current = current + "\n" + para if current else para
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks

def index_pdf(pdf_id: str, pages: List[str], ollama_url: str, embed_model: str):
    docs = []
    metadatas = []
    ids = []

    for page_idx, page_text in enumerate(pages):
        chunks = chunk_text(page_text)
        for chunk_idx, chunk in enumerate(chunks):
            emb = ollama_embed(ollama_url, embed_model, chunk)
            if emb is None:
                continue
            doc_id = f"{pdf_id}_p{page_idx}_c{chunk_idx}_{uuid.uuid4().hex}"
            docs.append(chunk)
            metadatas.append({
                "pdf_id": pdf_id,
                "page": page_idx,
                "chunk": chunk_idx,
            })
            ids.append(doc_id)
            get_chunk_collection().add(
                ids=[doc_id],
                documents=[chunk],
                metadatas=[metadatas[-1]],
                embeddings=[emb],
            )

def summarize_pdf(pages: List[str], ollama_url: str, model: str) -> str:
    # Use first few pages / limited text for initial summary
    joined = "\n\n".join(pages[:5])
    prompt = (
        "You are given the following PDF content. "
        "Write a concise, high-level summary (max 10 bullet points):\n\n"
        f"{joined}"
    )
    return ollama_chat(ollama_url, model, prompt)

def get_metadata_for_pdf(pdf_id: str):
    db = load_metadata()
    return db["pdfs"].get(pdf_id, {}).get("metadata", {})

