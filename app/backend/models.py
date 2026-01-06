from typing import List, Optional

from pydantic import BaseModel

class Settings(BaseModel):
    ollama_url: str
    model: str
    embedding_model: str

class SaveSettingsResponse(BaseModel):
    ok: bool
    error: Optional[str] = None

class ChatRequest(BaseModel):
    pdf_id: str
    question: str
    ollama_url: str
    model: str
    embedding_model: str

class ChatResponse(BaseModel):
    answer: str
    history: List[dict]

class PDFInfo(BaseModel):
    id: str
    name: str
    summary: Optional[str] = None

class PDFListResponse(BaseModel):
    pdfs: List[PDFInfo]

class SummaryResponse(BaseModel):
    pdf_id: str
    summary: Optional[str] = None

class ChatHistory(BaseModel):
    history: List[dict]

