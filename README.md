Local PDF RAG Application
=========================

Overview
--------
This project is a fully local, privacy‑friendly PDF Question‑Answering (RAG) application.  
It uses a Streamlit frontend, a FastAPI backend, and a local Ollama LLM for both embeddings and chat responses.

The app allows you to:
- Upload PDFs
- Generate summaries
- Ask questions using Retrieval‑Augmented Generation
- Persist chat history per PDF
- Select LLM and embedding models
- Run everything offline on your own machine

Prerequisites
-------------
1. Install Ollama locally  
   Download from: https://ollama.com

2. Pull at least one LLM model  
   Example:
       ollama pull qwen2.5:7b

3. Pull a specialized embedding model  
   Recommended:
       ollama pull nomic-embed-text

Python Virtual Environment Setup
================================

Create a virtual environment
----------------------------
cd to project root directory
python3 -m venv .venv

Activate the virtual environment
--------------------------------
macOS / Linux:
    source .venv/bin/activate

Windows (PowerShell):
    .venv\Scripts\Activate.ps1

Windows (CMD):
    .venv\Scripts\activate.bat

Install dependencies
--------------------
pip install --upgrade pip
pip install -r ./app/backend/requirements.txt
pip install -r ./app/web/requirements.txt

Deactivate the environment
--------------------------
deactivate

Using the App
-------------
Open the left sidebar and select “Settings”.

You must configure:
- Ollama URL (default: http://localhost:11434)
- LLM Model (example: qwen2.5:7b)
- Embedding Model (recommended: nomic-embed-text)

The app verifies the models and shows a green/red status indicator.

Architecture
============

High‑Level System Diagram
-------------------------

                ┌────────────────────┐
                │   Frontend (FE)    │
                │    Streamlit UI    │
                └─────────┬──────────┘
                          │
                          │ HTTP (REST)
                          ▼
                ┌────────────────────┐
                │   Backend (BE)     │
                │     FastAPI        │
                └─────────┬──────────┘
                          │
                          │ Local API Calls
                          ▼
                ┌────────────────────┐
                │  Local LLM Engine  │
                │      Ollama        │
                └────────────────────┘


Data Flow
---------

1. PDF Upload (Frontend)
       │
       ▼
2. Backend receives file
       │
       ├── Saves raw PDF locally
       │
       ├── Extracts text from PDF
       │
       ├── Generates embeddings using embedding model
       │
       └── Stores:
             - PDF file
             - extracted text
             - embeddings
             - metadata (summary, title, etc.)

3. User asks a question (Frontend)
       │
       ▼
4. Backend performs RAG:
       ├── Retrieves relevant chunks via vector search
       ├── Builds prompt with metadata + context
       └── Sends prompt to Ollama LLM

5. LLM generates answer
       │
       ▼
6. Backend stores chat history per PDF
       │
       ▼
7. Frontend displays answer + history

Local Storage Layout
====================

All application data is stored locally inside the backend `data/` directory.  
This ensures full privacy and makes the system completely offline‑capable.

```
data/
│
├── chroma/          → Persistent vector database (embeddings, chunk metadata)
│
├── metadata.json    → Master index of PDFs:
│                       - PDF ID
│                       - filename
│                       - summary
│                       - chat history
│                       - file path
│
├── pdfs/            → Raw uploaded PDF files
│                       Example:
│                       data/pdfs/<pdf_id>_<original_name>.pdf
│
└── settings.json    → Saved user settings:
                        - ollama_url
                        - model
                        - embedding_model
```

Explanation of Each Component
-----------------------------

1. chroma/
   Stores all vector embeddings generated from your PDFs.
   This includes:
   - chunked text
   - embedding vectors
   - metadata per chunk (pdf_id, page number, etc.)

2. metadata.json
   Acts as your lightweight “database”.
   Contains:
   - list of uploaded PDFs
   - summaries
   - chat history per PDF
   - file paths
   - extracted metadata

3. pdfs/
   Stores the original uploaded PDF files.
   These are referenced by metadata.json and used for re‑processing if needed.

4. settings.json
   Stores the user’s selected:
   - LLM model
   - embedding model
   - Ollama URL
   This allows the app to restore settings on restart.

Nothing leaves your machine.

Running the App Locally
-----------------------
Backend:
    cd app/backend
    ./run.sh

Frontend:
    cd app/web
    ./run.sh

Debugging
---------
Backend debugging:
    Open app/backend/main.py in PyCharm and run in debug mode.

Frontend debugging:
    Open app/web/app.py in PyCharm and run in debug mode.

Project Structure
-----------------
app/
    backend/
        main.py
        run.sh
        storage/
    web/
        app.py
        run.sh

Summary
-------
This application provides a fully local, private, extensible RAG workflow with:
- Modular architecture
- Persistent storage
- Zero cloud dependencies

Perfect for developers to start learning RAG AI app development.
