import streamlit as st

# ---------------------------------------------------------
# Initialize dynamic uploader key (MUST be before widgets)
# ---------------------------------------------------------
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ---------------------------------------------------------
# Now safe to import modules that may create widgets
# ---------------------------------------------------------
from settings import configure_setting, BACKEND_URL
from pdf_utils import fetch_pdfs, fetch_summary, fetch_chat_history, send_chat, upload_pdf

# ---------------------------------------------------------
# Page config + settings sidebar
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="Local PDF RAG")
configure_setting()

# ---------------------------------------------------------
# Initialize session state
# ---------------------------------------------------------
st.session_state.setdefault("selected_pdf_id", None)
st.session_state.setdefault("chat_history", [])

# ---------------------------------------------------------
# Main layout
# ---------------------------------------------------------
left, right = st.columns([1, 3])

with left:
    st.subheader("📚 Uploaded PDFs")

    pdfs = fetch_pdfs()

    if pdfs:
        ids = [p["id"] for p in pdfs]
        names = {p["id"]: f"{p['name']} ({p['id'][:8]})" for p in pdfs}

        # If a new PDF was uploaded, set it BEFORE widget creation
        if "uploaded_pdf_id" in st.session_state:
            st.session_state.selected_pdf_id = st.session_state.uploaded_pdf_id
            del st.session_state.uploaded_pdf_id

        st.selectbox(
            "Select a PDF",
            ids,
            format_func=lambda pdf_id: names[pdf_id],
            key="selected_pdf_id",
        )
    else:
        st.info("No PDFs yet. Upload one to get started.")

    # ---------------------------------------------------------
    # File uploader (fires exactly once using dynamic key)
    # ---------------------------------------------------------
    uploaded_file = st.file_uploader(
        "Upload new PDF",
        type=["pdf"],
        key=f"pdf_uploader_{st.session_state.uploader_key}"
    )

    if uploaded_file:
        pdf_info = upload_pdf(uploaded_file)

        if pdf_info:
            st.session_state.uploaded_pdf_id = pdf_info["id"]
            st.session_state.chat_history = []

        # Force uploader reset by changing its key
        st.session_state.uploader_key += 1
        st.rerun()


with right:
    st.subheader("📝 PDF Summary")

    if st.session_state.selected_pdf_id:
        summary = fetch_summary(st.session_state.selected_pdf_id)
        st.session_state.chat_history = []
        if summary:
            st.markdown(summary)
        else:
            st.info("No summary available for this PDF yet.")
    else:
        st.info("Select a PDF to see its summary.")

    st.markdown("---")
    st.subheader("💬 Chat with PDF")

    if not st.session_state.selected_pdf_id:
        st.info("Select or upload a PDF to start chatting.")
    else:
        question = st.text_input("Ask a question about this PDF")

        if st.button("Send"):
            if question.strip():
                send_chat(st.session_state.selected_pdf_id, question)
            else:
                st.warning("Please enter a question.")

        # Load chat history if empty
        if not st.session_state.chat_history:
            st.session_state.chat_history = fetch_chat_history(st.session_state.selected_pdf_id)

        for msg in st.session_state.chat_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                st.markdown(f"**You:** {content}")
            else:
                st.markdown(f"**Assistant:** {content}")
