import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

def set_default_session():
    if "ollama_url" not in st.session_state:
        st.session_state.ollama_url = DEFAULT_OLLAMA_URL

    if "model" not in st.session_state:
        st.session_state.model = None

    if "embedding_model" not in st.session_state:
        st.session_state.embedding_model = None

    if "settings_ok" not in st.session_state:
        st.session_state.settings_ok = False

    if "models" not in st.session_state:
        st.session_state.models = []

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def configure_setting():
    set_default_session()
    saved_settings = load_saved_setting()
    if saved_settings and saved_settings.get("ollama_url"):
        st.session_state.ollama_url = saved_settings["ollama_url"]
        st.session_state.model = saved_settings.get("model")
        st.session_state.embedding_model = saved_settings.get("embedding_model")
        st.session_state.settings_ok = True

    if not st.session_state.ollama_url or not st.session_state.model or not st.session_state.embedding_model:
        st.session_state.settings_ok = False

    # ------------------------------
    # Settings sidebar
    # ------------------------------
    with st.sidebar:
        st.header("⚙️ Settings")

        st.session_state.ollama_url = st.text_input(
            "Ollama URL",
            value=st.session_state.ollama_url,
        )

        if st.button("Fetch Models"):
            try:
                r = requests.get(f"{DEFAULT_OLLAMA_URL}/api/tags", timeout=10)
                data = r.json()
                if data.get("models"):
                    st.session_state.models = [m["name"] for m in data["models"]]
                else:
                    st.session_state.models = []
                    st.error("No models found or cannot reach Ollama.")
            except Exception as e:
                st.session_state.models = []
                st.error(f"Error fetching models: {e}")

        if st.session_state.models:
            st.session_state.embedding_model = st.selectbox(
                "Embedding Model",
                st.session_state.models,
                index=(
                    st.session_state.models.index(st.session_state.embedding_model)
                    if st.session_state.embedding_model in st.session_state.models
                    else 0
                ),
            )

        if st.session_state.models:
            st.session_state.model = st.selectbox(
                "Model",
                st.session_state.models,
                index=(
                    st.session_state.models.index(st.session_state.model)
                    if st.session_state.model in st.session_state.models
                    else 0
                ),
            )
        elif not st.session_state.settings_ok:
            st.info("Verify settings to load models from Ollama.")

        if st.button("Verify settings"):
            try:
                r = requests.post(
                    f"{BACKEND_URL}/settings",
                    json={
                        "ollama_url": st.session_state.ollama_url,
                        "model": st.session_state.model,
                        "embedding_model": st.session_state.embedding_model
                    },
                    timeout=10,
                )
                data = r.json()
                if data.get("ok"):
                    st.session_state.settings_ok = True
                    st.success("Settings are valid, models loaded.")
                else:
                    st.session_state.settings_ok = False
                    st.error(data.get("error", "Settings invalid."))
            except Exception as e:
                st.session_state.settings_ok = False
                st.error(f"Error verifying settings: {e}")
        status_placeholder = st.empty()
        update_status(status_placeholder)

def update_status(status_placeholder):
    status_icon = "🟢" if st.session_state.settings_ok else "🔴"
    status_placeholder.write(f"Status: {status_icon}")

def load_saved_setting():
    try:
        r = requests.get(f"{BACKEND_URL}/settings", timeout=10)
        data = r.json()
        return data
    except Exception as e:
        st.error(f"Error fetching settings: {e}")
        return None