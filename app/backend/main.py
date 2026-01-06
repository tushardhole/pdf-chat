import logging
import shutil

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from rag_utils import *
from models import Settings

# ------------------------------
# FastAPI app
# ------------------------------
app = FastAPI(title="PDF RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Routes
# ------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/settings", response_model=SaveSettingsResponse)
def save_settings(req: Settings):
    try:
        with open(SETTING_JSON, "w") as f:
            json.dump(req.model_dump(), f, indent=2)
    except Exception as e:
        return SaveSettingsResponse(ok=False, error=str(e))
    return SaveSettingsResponse(ok=True)


@app.get("/settings", response_model=Settings)
def get_settings():
    try:
        with open(SETTING_JSON, "r") as f:
            data = json.load(f)
            # Let Pydantic validate/normalize
            return Settings(**data)
    except Exception:
        # Fall back to defaults if file missing or invalid
        return Settings(
            ollama_url="http://localhost:11434",
            model="",
            embedding_model="",
        )


@app.post("/pdf/upload", response_model=PDFInfo)
def upload_pdf(
    file: UploadFile = File(...),
    ollama_url: str = Form(...),
    embedding_model: str = Form(...),
    file_id: str = Form(...),
    model: str = Form(...),
):
    logging.debug(f"Uploading PDF: {file.filename}")
    meta = load_metadata()

    if file_id in meta.get("pdfs", {}):
        pdf = meta["pdfs"][file_id]
        return PDFInfo(id=pdf["id"], name=pdf["name"], summary=pdf["summary"])

    pdf_id = file_id
    filename = f"{pdf_id}_{file.filename}"
    file_path = os.path.join(PDF_DIR, filename)

    # Save uploaded file synchronously
    os.makedirs(PDF_DIR, exist_ok=True)
    with open(file_path, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out)

    # Extract pages
    pages = extract_pdf_pages(file_path)

    # Combine first 3–4 pages (or fewer if shorter) for metadata extraction
    first_pages_text = "\n\n".join(pages[:4])
    content_metadata = extract_content_metadata_with_llm(first_pages_text, model)

    # Index and summarize (both synchronous)
    index_pdf(pdf_id, pages, ollama_url, embedding_model)
    summary = summarize_pdf(pages, ollama_url, model)

    # Update metadata store
    if "pdfs" not in meta:
        meta["pdfs"] = {}

    meta["pdfs"][pdf_id] = {
        "id": pdf_id,
        "name": file.filename,
        "file_path": file_path,
        "summary": summary,
        "content_metadata": content_metadata,
        "chat_history": [],
    }
    save_metadata(meta)

    logging.debug(f"Uploaded PDF: {file.filename}")

    return PDFInfo(id=pdf_id, name=file.filename, summary=summary)

@app.get("/pdf/list", response_model=PDFListResponse)
def list_pdfs():
    meta = load_metadata()
    pdfs: list[PDFInfo] = []

    for pdf_id, info in meta.get("pdfs", {}).items():
        pdfs.append(
            PDFInfo(
                id=pdf_id,
                name=info.get("name", ""),
                summary=info.get("summary"),
            )
        )

    return PDFListResponse(pdfs=pdfs)


@app.get("/pdf/{pdf_id}/summary", response_model=SummaryResponse)
def get_pdf_summary(pdf_id: str):
    meta = load_metadata()
    pdf = meta.get("pdfs", {}).get(pdf_id)
    if not pdf:
        return SummaryResponse(pdf_id=pdf_id, summary=None)
    return SummaryResponse(pdf_id=pdf_id, summary=pdf.get("summary"))


@app.get("/pdf/{pdf_id}/chat_history", response_model=ChatHistory)
def get_pdf_chat_history(pdf_id: str):
    meta = load_metadata()
    pdf = meta.get("pdfs", {}).get(pdf_id)
    if not pdf:
        return ChatHistory(history=[])
    return ChatHistory(history=pdf.get("chat_history", []))


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    meta = load_metadata()
    pdf = meta.get("pdfs", {}).get(req.pdf_id)
    if not pdf:
        return ChatResponse(answer="PDF not found.", history=[])

    try:
        answer = rag_answer(req)

        # Append to history
        history = pdf.get("chat_history", [])
        history.append({"role": "user", "content": req.question})
        history.append({"role": "assistant", "content": answer})
        pdf["chat_history"] = history

        meta["pdfs"][req.pdf_id] = pdf
        save_metadata(meta)

        return ChatResponse(answer=answer, history=history)
    except Exception as e:
        # Still return existing history if something breaks mid-answer
        return ChatResponse(
            answer=f"Please try again later. Error: {str(e)}",
            history=pdf.get("chat_history", []),
        )


def main():
    import uvicorn

    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")


if __name__ == "__main__":
    main()
