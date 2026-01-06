from settings import BACKEND_URL
import requests
import streamlit as st

def fetch_pdfs():
    try:
        r = requests.get(f"{BACKEND_URL}/pdf/list", timeout=10)
        return r.json().get("pdfs", [])
    except Exception as e:
        st.error(f"Error fetching PDFs: {e}")
        return []

def fetch_summary(pdf_id: str):
    try:
        r = requests.get(f"{BACKEND_URL}/pdf/{pdf_id}/summary", timeout=10)
        return r.json().get("summary")
    except Exception as e:
        st.error(f"Error fetching summary: {e}")
        return None

def fetch_chat_history(pdf_id: str):
    try:
        r = requests.get(f"{BACKEND_URL}/pdf/{pdf_id}/chat_history", timeout=10)
        return r.json().get("history", [])
    except Exception as e:
        st.error(f"Error fetching chat history: {e}")
        return []

def upload_pdf(file):
    if not st.session_state.settings_ok or not st.session_state.model:
        st.error("Configure settings and select a model first.")
        return None

    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {
        "ollama_url": st.session_state.ollama_url,
        "model": st.session_state.model,
        "embedding_model": st.session_state.embedding_model,
        "file_id": file.name,
    }

    try:
        with st.spinner("Uploading and indexing PDF..."):
            r = requests.post(
                f"{BACKEND_URL}/pdf/upload",
                files=files,
                data=data,
                timeout=605,
            )
        if r.status_code == 200:
            pdf_info = r.json()
            st.success(f"PDF uploaded and indexed: {pdf_info.get('name')}")
            return pdf_info
        else:
            st.error(f"Upload failed: {r.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading PDF: {e}")
        return None


def send_chat(pdf_id: str, question: str):
    payload = {
        "pdf_id": pdf_id,
        "question": question,
        "ollama_url": st.session_state.ollama_url,
        "model": st.session_state.model,
        "embedding_model": st.session_state.embedding_model,
    }

    try:
        with st.spinner("Thinking..."):
            r = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=245)
        if r.status_code == 200:
            data = r.json()
            st.session_state.chat_history = data.get("history", [])
        else:
            st.error(f"Chat failed: {r.text}")
    except Exception as e:
        st.error(f"Error sending chat: {e}")