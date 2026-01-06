from pdf_utils import *


def build_rag_prompt(metadata: dict, context_chunks: list[str], question: str) -> str:
    metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)

    context_text = "\n\n---\n\n".join(context_chunks)

    prompt = f"""
You are answering questions about a PDF document.

You are given two sources of information:

1) Structured metadata extracted from the document (trust this for factual details like title, authors, publication year, publisher, document type, and abstract).
2) Text chunks retrieved from the document content (trust this for detailed explanations, methods, results, and narrative content).

Metadata (JSON):
{metadata_json}

Context (text chunks):
{context_text}

Instructions:
- Use the metadata for factual questions about the document itself (e.g., title, authors, publication year, publisher, document type).
- Use the context chunks for questions about the content, methods, results, and discussion.
- If metadata and context disagree, prefer metadata.
- Do NOT repeat the context verbatim.
- Do NOT anything unrelated to the question or context.
- Answer concisely and directly.
- If the answer is not clearly present in either the metadata or the context, say: "I don't know based on this document."

Question:
{question}

Answer:
"""
    return prompt

def rag_answer(req: ChatRequest) -> str:
    # Embed question
    q_emb = ollama_embed(req.ollama_url, req.embedding_model, req.question)
    if q_emb is None:
        return "Could not generate embeddings for question."

    # Query Chroma
    results = get_chunk_collection().query(
        query_embeddings=[q_emb],
        n_results=5,
        where={"pdf_id": req.pdf_id},
    )

    contexts = results.get("documents", [[]])[0]

    prompt = build_rag_prompt(get_metadata_for_pdf(req.pdf_id), contexts, req.question)
    return ollama_chat(req.ollama_url, req.model, prompt)

def extract_content_metadata_with_llm(text: str, model: str):
    prompt = (
        "You are an expert at extracting metadata from documents.\n"
        "Given the text below (from the first pages of a PDF), extract structured metadata.\n"
        "Return ONLY valid JSON with these fields:\n\n"
        """{{
          "title": "",
          "authors": [],
          "emails": [],
          "affiliations": [],
          "publication_year": "",
          "publisher": "",
          "document_type": "",
          "abstract": "",
          "keywords": []
        }}"""

        "Rules:\n"
        "- If a field is missing, return an empty string or empty list.\n"
        "- Do NOT invent information.\n"
        "- Do NOT include commentary.\n"
        "- Do NOT include extra fields.\n"
        "- Return ONLY JSON.\n\n"

        "Text:\n"
        "<<<\n"
        f"{text}\n"
        ">>>\n"
    )

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=600
    )

    raw = response.json().get("response", "").strip()

    # Ensure valid JSON
    try:
        metadata = json.loads(raw)
    except:
        metadata = {}

    return metadata
