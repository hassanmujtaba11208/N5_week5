"""Streamlit UI. It communicates with FastAPI over HTTP only."""
import os
import requests
import streamlit as st

st.set_page_config(page_title="Full-Stack GenAI App", page_icon="🧠", layout="wide")
st.title("🧠 Full-Stack GenAI App")
st.caption("RAG + bounded agent · FastAPI · API-key authentication · JSON logging · rate limiting")

with st.sidebar:
    st.header("Backend connection")
    api_url = st.text_input("FastAPI base URL", value=os.getenv("API_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
    api_key = st.text_input("API key", value=os.getenv("GENAI_API_KEY", "dev-local-key-change-me"), type="password")
    st.caption("The frontend sends requests to the backend over HTTP. Keep your API key private.")

tab_ask, tab_health, tab_help = st.tabs(["Ask", "Backend health", "API help"])

with tab_ask:
    query = st.text_area("Your question", placeholder="Ask about anomaly detection, calculate 24 * 8, or ask for today's date.")
    col1, col2 = st.columns(2)
    with col1:
        mode = st.selectbox("Mode", ["rag", "agent"], help="RAG searches the knowledge base. Agent chooses a tool.")
    with col2:
        top_k = st.slider("Top K", min_value=1, max_value=10, value=3)
    if st.button("Submit question", type="primary", disabled=not query.strip()):
        headers = {"X-API-Key": api_key}
        payload = {"query": query, "mode": mode, "top_k": top_k}
        try:
            response = requests.post(f"{api_url}/ask", json=payload, headers=headers, timeout=45)
            if response.status_code == 200:
                data = response.json()
                st.success(f"Request completed · mode: {data['mode']} · tool: {data.get('tool_used') or 'none'}")
                st.markdown(data["answer"])
                if data.get("results"):
                    st.subheader("Retrieved passages")
                    for item in data["results"]:
                        with st.expander(f"{item.get('rank', '')}. {item.get('section', 'Result')} · similarity {item.get('similarity', 'n/a')}"):
                            st.write(item.get("text", ""))
                st.caption(f"Request ID: {data.get('request_id')} · Iterations: {data.get('iterations')}")
            else:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text
                st.error(f"Backend returned HTTP {response.status_code}: {detail}")
                if response.status_code == 429:
                    st.info("This API key has reached its request limit. Wait before trying again.")
        except requests.RequestException as exc:
            st.error(f"Could not reach the backend: {exc}")
            st.info("Start FastAPI in a separate terminal: uvicorn backend.app.main:app --reload")

with tab_health:
    st.write("Check whether the FastAPI service is reachable.")
    if st.button("Check backend health"):
        try:
            response = requests.get(f"{api_url}/health", timeout=10)
            st.json(response.json())
        except requests.RequestException as exc:
            st.error(f"Backend unavailable: {exc}")

with tab_help:
    st.markdown("""
    **RAG mode** retrieves matching passages from the local knowledge base.

    **Agent mode** routes a request to one tool:
    - Safe calculator for arithmetic
    - RAG search for knowledge-base questions
    - Date/time utility for current date or time

    The `/ask` endpoint requires an `X-API-Key` header. The `/health` endpoint is public.
    """)
    st.code("POST /ask\nGET /health\nHeader: X-API-Key: <your-key>")
