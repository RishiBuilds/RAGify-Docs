from __future__ import annotations
from collections import defaultdict
import requests
import streamlit as st

API_BASE = "http://localhost:8000"
MAX_FILE_SIZE_MB = 50

def _create_session() -> dict:
    resp = requests.post(f"{API_BASE}/session", timeout=30)
    resp.raise_for_status()
    return resp.json()

def _delete_session(session_id: str) -> None:
    try:
        requests.delete(f"{API_BASE}/session/{session_id}", timeout=15)
    except Exception:
        pass

def _check_health() -> dict:
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {"status": "unreachable", "qdrant_connected": False}

def _init_session() -> None:
    if "session_id" not in st.session_state:
        try:
            data = _create_session()
            st.session_state.session_id = data["session_id"]
            st.session_state.collection_name = data["collection_name"]
        except Exception as exc:
            st.session_state.backend_down = True
            st.session_state.backend_error = str(exc)
            return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "documents_uploaded" not in st.session_state:
        st.session_state.documents_uploaded = False

    if "uploaded_file_stats" not in st.session_state:
        st.session_state.uploaded_file_stats = []

def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    grouped = defaultdict(list)
    for src in sources:
        grouped[src["filename"]].append(src)
    for filename, file_sources in grouped.items():
        pages = sorted({s["page_number"] for s in file_sources})
        page_pills = " ".join(f'<span class="source-page">p.{p}</span>' for p in pages)
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-header">
                    <span class="source-icon">📄</span>
                    <span class="source-filename">{filename}</span>
                    <span class="source-pages-container">{page_pills}</span>
                </div>
            """,
            unsafe_allow_html=True
        )
        for src in file_sources:
            st.markdown(
                f'<div class="source-snippet">"{src["snippet"]}"</div>',
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

st.set_page_config(
    page_title="RAGify-Docs",
    page_icon=":material/description:",
    layout="wide",
    initial_sidebar_state="expanded",
)

_init_session()

if st.session_state.get("backend_down"):
    st.error(
        f"Backend unreachable. Make sure the FastAPI server is running at {API_BASE}. Error: {st.session_state.get('backend_error', 'unknown')}",
        icon=":material/error:",
    )
    st.stop()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }
    
    code, pre, .session-value, .doc-badge, .source-page {
        font-family: 'Fira Code', monospace !important;
    }
    
    .health-container {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .health-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    .health-ok {
        background-color: #10b981;
        animation: pulse 2s infinite;
    }
    
    .health-bad {
        background-color: #ef4444;
        box-shadow: 0 0 6px #ef4444aa;
    }
    
    .health-text {
        font-size: 0.85rem;
        font-weight: 600;
        color: #e8e6e1;
    }
    
    .session-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 16px;
    }
    
    .session-title {
        font-size: 0.72rem;
        font-weight: 700;
        color: #8a90a0;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }
    
    .session-value {
        font-size: 0.8rem;
        color: #e8a838;
        word-break: break-all;
    }
    
    .sidebar-section-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8a90a0;
        margin-top: 12px;
        margin-bottom: 8px;
    }
    
    .doc-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 6px;
        transition: all 0.2s ease;
    }
    
    .doc-card:hover {
        background: rgba(255, 255, 255, 0.03);
        border-color: rgba(232, 168, 56, 0.15);
    }
    
    .doc-card.status-ok {
        border-left: 3px solid #e8a838;
    }
    
    .doc-card.status-error {
        border-left: 3px solid #ef4444;
    }
    
    .doc-name {
        font-weight: 500;
        font-size: 0.82rem;
        color: #e8e6e1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 150px;
    }
    
    .doc-badge {
        font-size: 0.7rem;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(232, 168, 56, 0.1);
        color: #e8a838;
    }
    
    .doc-card.status-error .doc-badge {
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
    }
    
    button[data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        color: #8a90a0 !important;
        transition: all 0.2s ease !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #e8a838 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #e8a838 !important;
    }
    
    .hero-container {
        text-align: center;
        padding: 3rem 1.5rem;
        background: linear-gradient(135deg, rgba(26, 29, 36, 0.6) 0%, rgba(15, 17, 21, 0.6) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
    }
    
    .hero-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        animation: float 4s ease-in-out infinite;
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
        100% { transform: translateY(0px); }
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #e8a838 0%, #ff8c37 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #8a90a0;
        margin-bottom: 2rem;
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.25rem;
        max-width: 800px;
        margin: 0 auto;
    }
    
    .feature-card {
        background: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: left;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        background: rgba(255, 255, 255, 0.03);
        border-color: rgba(232, 168, 56, 0.20);
        transform: translateY(-2px);
    }
    
    .feature-card-icon {
        font-size: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    .feature-card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #e8e6e1;
        margin-bottom: 0.25rem;
    }
    
    .feature-card-desc {
        font-size: 0.8rem;
        color: #8a90a0;
        line-height: 1.4;
    }
    
    .source-card {
        background: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: all 0.2s ease;
    }
    
    .source-card:hover {
        background: rgba(255, 255, 255, 0.025);
        border-color: rgba(232, 168, 56, 0.2);
    }
    
    .source-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        padding-bottom: 6px;
    }
    
    .source-icon {
        font-size: 0.9rem;
    }
    
    .source-filename {
        font-weight: 600;
        font-size: 0.85rem;
        color: #e8e6e1;
        flex-grow: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .source-page {
        font-size: 0.72rem;
        color: #e8a838;
        background: rgba(232, 168, 56, 0.1);
        padding: 1px 6px;
        border-radius: 4px;
        margin-left: 4px;
    }
    
    .source-snippet {
        font-size: 0.82rem;
        color: #a0a5b5;
        font-style: italic;
        line-height: 1.4;
        border-left: 2px solid rgba(232, 168, 56, 0.4);
        padding-left: 10px;
        margin: 6px 0;
    }
    
    .confidence-container {
        display: flex;
        align-items: center;
        margin-top: 8px;
        font-size: 0.8rem;
    }
    
    .confidence-label {
        color: #8a90a0;
        margin-right: 8px;
    }
    
    .confidence-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .confidence-high {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .confidence-medium {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .confidence-low {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #e8a838, #ff8c37) !important;
        border: none !important;
        color: #0f1115 !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(232, 168, 56, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 16px rgba(232, 168, 56, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem;">⚡ RAGify<span style="color: #e8a838;">.Docs</span></div>', unsafe_allow_html=True)

    health = _check_health()
    if health["qdrant_connected"]:
        st.markdown(
            '<div class="health-container"><span class="health-dot health-ok"></span><span class="health-text">Connected</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="health-container"><span class="health-dot health-bad"></span><span class="health-text">{health["status"]}</span></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown(
        f"""
        <div class="session-card">
            <div class="session-title">Active Session</div>
            <div class="session-value">{st.session_state.session_id}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.uploaded_file_stats:
        st.divider()
        st.markdown('<div class="sidebar-section-title">Documents</div>', unsafe_allow_html=True)
        for fs in st.session_state.uploaded_file_stats:
            status_class = "status-ok" if fs["status"] == "ok" else "status-error"
            badge_text = f"{fs['chunks']} chunks" if fs["status"] == "ok" else "error"
            st.markdown(
                f"""
                <div class="doc-card {status_class}">
                    <span class="doc-name">{fs['name']}</span>
                    <span class="doc-badge">{badge_text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.subheader(":material/tune: Settings")
    top_k = st.slider(
        "Top-K retrieval",
        min_value=1,
        max_value=20,
        value=5,
        help="Number of document chunks to retrieve per question.",
    )

    st.divider()

    if "confirm_new_session" not in st.session_state:
        st.session_state.confirm_new_session = False

    if st.session_state.confirm_new_session:
        st.warning("Start a new session? This clears all uploaded documents and chat history.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm", use_container_width=True, type="primary"):
                _delete_session(st.session_state.session_id)
                try:
                    data = _create_session()
                    st.session_state.session_id = data["session_id"]
                    st.session_state.collection_name = data["collection_name"]
                    st.session_state.chat_history = []
                    st.session_state.documents_uploaded = False
                    st.session_state.uploaded_file_stats = []
                    st.session_state.confirm_new_session = False
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to create new session: {exc}")
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_new_session = False
                st.rerun()
    else:
        if st.button(
            "New Session",
            icon=":material/refresh:",
            use_container_width=True,
        ):
            st.session_state.confirm_new_session = True
            st.rerun()

tab_upload, tab_chat = st.tabs([
    ":material/upload_file:  Upload Documents",
    ":material/chat:  Ask Questions",
])

with tab_upload:
    st.subheader("Upload & Process PDFs")
    st.caption(
        "Upload one or more PDF files to ingest them into the knowledge base. "
        "Once processed, switch to the **Ask Questions** tab to start querying."
    )

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_uploader",
    )
    st.caption(f"Maximum file size: {MAX_FILE_SIZE_MB}MB per PDF")

    if uploaded_files and st.button(
        "Process Documents",
        icon=":material/rocket_launch:",
        use_container_width=True,
        type="primary",
    ):
        valid_files = []
        has_oversized = False
        for f in uploaded_files:
            size_mb = f.size / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                st.error(
                    f"**{f.name}** ({size_mb:.1f}MB) exceeds the "
                    f"{MAX_FILE_SIZE_MB}MB limit and will be skipped.",
                    icon=":material/block:",
                )
                has_oversized = True
            else:
                valid_files.append(f)

        if valid_files:
            with st.status(
                "Processing documents…", expanded=True
            ) as status_widget:
                st.write(":material/upload_file: Uploading files…")
                files_payload = [
                    ("files", (f.name, f.read(), "application/pdf"))
                    for f in valid_files
                ]

                st.write(":material/auto_awesome: Extracting text & generating embeddings…")
                try:
                    resp = requests.post(
                        f"{API_BASE}/upload",
                        data={"session_id": st.session_state.session_id},
                        files=files_payload,
                        timeout=120,
                    )

                    if resp.status_code == 404:
                        status_widget.update(
                            label="Session expired", state="error", expanded=True
                        )
                        st.error(
                            "Session not found - the backend may have restarted. "
                            "Please start a **New Session** from the sidebar.",
                            icon=":material/error:",
                        )
                    else:
                        resp.raise_for_status()
                        result = resp.json()

                        st.write(":material/database: Storing in vector database…")

                        file_stats = []
                        errors = result.get("errors", [])
                        processed_names = [f.name for f in valid_files]

                        error_map = {}
                        for err in errors:
                            for name in processed_names:
                                if name in err:
                                    error_map[name] = err
                                    break

                        if result["total_chunks"] > 0:
                            st.session_state.documents_uploaded = True

                        for f in valid_files:
                            if f.name in error_map:
                                file_stats.append(
                                    {"name": f.name, "chunks": 0, "status": "error"}
                                )
                                st.error(
                                    f"**{f.name}** - {error_map[f.name]}",
                                    icon=":material/error:",
                                )
                            else:
                                per_file_chunks = (
                                    result["total_chunks"] // result["files_processed"]
                                    if result["files_processed"] > 0
                                    else 0
                                )
                                file_stats.append(
                                    {"name": f.name, "chunks": per_file_chunks, "status": "ok"}
                                )
                                st.success(
                                    f"**{f.name}** - {per_file_chunks} chunks created",
                                    icon=":material/check_circle:",
                                )

                        st.session_state.uploaded_file_stats.extend(file_stats)

                        if result["status"] == "success" and result["total_chunks"] > 0:
                            status_widget.update(
                                label=f"Processed {result['files_processed']} file(s) - "
                                      f"{result['total_chunks']} chunks",
                                state="complete",
                                expanded=False,
                            )
                        else:
                            status_widget.update(
                                label="Processing completed with errors",
                                state="error",
                                expanded=True,
                            )

                except requests.exceptions.HTTPError as exc:
                    status_widget.update(
                        label="Upload failed", state="error", expanded=True
                    )
                    st.error(
                        f"Upload failed: {exc.response.text}",
                        icon=":material/error:",
                    )
                except Exception as exc:
                    status_widget.update(
                        label="Upload failed", state="error", expanded=True
                    )
                    st.error(
                        f"Upload failed: {exc}",
                        icon=":material/error:",
                    )
        elif has_oversized:
            st.warning(
                "No valid files to process - all selected files exceeded the size limit.",
                icon=":material/warning:",
            )

with tab_chat:
    if not st.session_state.documents_uploaded:
        st.markdown(
            """
            <div class="hero-container">
                <div class="hero-icon">⚡</div>
                <div class="hero-title">RAGify Your Documents</div>
                <div class="hero-subtitle">Upload PDFs in the first tab to begin asking questions with verified grounding sources.</div>
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-card-icon">📂</div>
                        <div class="feature-card-title">Document Parsing</div>
                        <div class="feature-card-desc">Extract text and metadata automatically from any PDF.</div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-card-icon">🔍</div>
                        <div class="feature-card-title">Semantic Search</div>
                        <div class="feature-card-desc">Retrieve exact matching chunks using dense vector embeddings in Qdrant.</div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-card-icon">⚖️</div>
                        <div class="feature-card-title">Strict Grounding</div>
                        <div class="feature-card-desc">Every answer is backed by explicit citations and page numbers.</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        if not st.session_state.chat_history:
            st.markdown(
                """
                <div class="hero-container">
                    <div class="hero-icon">💬</div>
                    <div class="hero-title">Knowledge Base Ready</div>
                    <div class="hero-subtitle">Ask questions below about your uploaded PDFs. The assistant will retrieve source citations to back its claims.</div>
                    <div class="features-grid">
                        <div class="feature-card">
                            <div class="feature-card-icon">💡</div>
                            <div class="feature-card-title">Ask Specific Claims</div>
                            <div class="feature-card-desc">"What is the definition of X in section 3?" or "Compare table A and table B."</div>
                        </div>
                        <div class="feature-card">
                            <div class="feature-card-icon">📝</div>
                            <div class="feature-card-title">Request Summaries</div>
                            <div class="feature-card-desc">"Summarize the main findings of the paper in 3 bullet points."</div>
                        </div>
                        <div class="feature-card">
                            <div class="feature-card-icon">🎯</div>
                            <div class="feature-card-title">Fact Checking</div>
                            <div class="feature-card-desc">"Does the document mention any security risks regarding Y?"</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                if msg["role"] == "assistant" and msg.get("sources"):
                    with st.expander(
                        f"🔍 Grounding Sources ({len(msg['sources'])})"
                    ):
                        _render_sources(msg["sources"])

                    if msg.get("confidence"):
                        level = msg["confidence"].lower()
                        st.markdown(
                            f"""
                            <div class="confidence-container">
                                <span class="confidence-label">Confidence:</span>
                                <span class="confidence-badge confidence-{level}">{msg['confidence']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

        if question := st.chat_input("Ask a question about your documents…"):
            st.session_state.chat_history.append(
                {"role": "user", "content": question}
            )
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/ask",
                            json={
                                "session_id": st.session_state.session_id,
                                "question": question,
                            },
                            timeout=60,
                        )

                        if resp.status_code == 404:
                            error_msg = (
                                "Session not found - the backend may have restarted. "
                                "Please start a New Session from the sidebar."
                            )
                            st.error(error_msg, icon=":material/error:")
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": error_msg}
                            )
                        else:
                            resp.raise_for_status()
                            result = resp.json()

                            answer = result["answer"]
                            sources = result.get("sources", [])
                            confidence = result.get("confidence")

                            st.markdown(answer)

                            if sources:
                                with st.expander(
                                    f"🔍 Grounding Sources ({len(sources)})"
                                ):
                                    _render_sources(sources)

                            if confidence:
                                level = confidence.lower()
                                st.markdown(
                                    f"""
                                    <div class="confidence-container">
                                        <span class="confidence-label">Confidence:</span>
                                        <span class="confidence-badge confidence-{level}">{confidence}</span>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            st.session_state.chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": answer,
                                    "sources": sources,
                                    "confidence": confidence,
                                }
                            )
                    except requests.exceptions.HTTPError as exc:
                        error_msg = f"Error: {exc.response.text}"
                        st.error(error_msg, icon=":material/error:")
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": error_msg}
                        )
                    except Exception as exc:
                        error_msg = f"Error: {exc}"
                        st.error(error_msg, icon=":material/error:")
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": error_msg}
                        )
