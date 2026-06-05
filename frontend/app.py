import streamlit as st
import requests
import json
import time

# Set page config
st.set_page_config(
    page_title="HR Copilot AI - İK Asistanı",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    /* Dark glassmorphic styling */
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #0f1626 50%, #030712 100%);
        color: #f8fafc;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Hide default Streamlit decoration */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Brand header */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    .brand-icon {
        background: linear-gradient(135deg, #06b6d4, #8b5cf6);
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.45);
        color: white;
        font-size: 15px;
        font-weight: 700;
    }
    .brand-name {
        font-size: 22px;
        font-weight: 700;
        background: linear-gradient(to right, #ffffff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .brand-tag {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: #06b6d4;
        border: 1px solid rgba(6, 182, 212, 0.3);
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(17, 24, 39, 0.8) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    /* Status section */
    .status-card {
        background: rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }
    .status-title {
        font-size: 12px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
    }
    .status-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 13px;
        margin-bottom: 8px;
    }
    .status-label {
        color: #94a3b8;
    }
    .status-value {
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-dot.active {
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }
    .status-dot.inactive {
        background-color: #ec4899;
        box-shadow: 0 0 8px #ec4899;
    }
    
    /* Custom message bubbles */
    .user-bubble {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(139, 92, 246, 0.08) 100%);
        border: 1px solid rgba(6, 182, 212, 0.25);
        padding: 16px 20px;
        border-radius: 16px;
        border-top-right-radius: 4px;
        margin: 10px 0 20px 40px;
        color: #f8fafc;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    .assistant-bubble {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 16px 20px;
        border-radius: 16px;
        border-top-left-radius: 4px;
        margin: 10px 40px 20px 0;
        color: #e2e8f0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        line-height: 1.6;
    }
    .bubble-sender {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
    .user-sender {
        color: #06b6d4;
        text-align: right;
    }
    .assistant-sender {
        color: #8b5cf6;
    }
    
    /* Source citations cards */
    .source-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 12px;
        margin-top: 10px;
    }
    .source-meta {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-bottom: 8px;
    }
    .badge-category {
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(139, 92, 246, 0.15);
        color: #c084fc;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    .badge-page {
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(6, 182, 212, 0.15);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }
    .source-score {
        font-size: 11px;
        font-weight: 600;
        color: #10b981;
        margin-left: auto;
    }
    .source-title {
        font-size: 13px;
        font-weight: 600;
        color: #ffffff;
    }
    .source-text {
        font-size: 12px;
        color: #cbd5e1;
        line-height: 1.5;
        background: rgba(0, 0, 0, 0.15);
        padding: 8px;
        border-radius: 6px;
        margin-top: 6px;
        border-left: 2px solid #8b5cf6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize Session State for Preset Trigger
if "preset_question" not in st.session_state:
    st.session_state.preset_question = None

# Backend API Base URL
BACKEND_URL = "http://127.0.0.1:8000/api"

# Status Checker
def check_status():
    try:
        res = requests.get(f"{BACKEND_URL}/status", timeout=2)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {
        "status": "offline",
        "openai_configured": False,
        "qdrant_configured": False,
        "collection_exists": False,
        "total_points": 0,
        "collection_name": ""
    }

backend_status = check_status()

# Sidebar Layout
with st.sidebar:
    st.markdown("""
    <div class="brand-container">
        <div class="brand-icon">HR</div>
        <div>
            <h1 class="brand-name" style="margin:0;">HR Copilot</h1>
            <span class="brand-tag">RAG V1</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Connections Info
    is_online = backend_status.get("status") == "healthy"
    dot_class = "active" if is_online else "inactive"
    openai_dot = "active" if backend_status.get("openai_configured") else "inactive"
    qdrant_dot = "active" if backend_status.get("qdrant_configured") else "inactive"
    
    st.markdown(f"""
    <div class="status-card">
        <div class="status-title">Bağlantı Durumu</div>
        <div class="status-item">
            <span class="status-label">FastAPI Backend</span>
            <span class="status-value"><span class="status-dot {dot_class}"></span>{"Çalışıyor" if is_online else "Bağlantı Yok"}</span>
        </div>
        <div class="status-item">
            <span class="status-label">OpenAI API</span>
            <span class="status-value"><span class="status-dot {openai_dot}"></span>{"Hazır" if backend_status.get("openai_configured") else "Eksik"}</span>
        </div>
        <div class="status-item">
            <span class="status-label">Qdrant DB (Yerel)</span>
            <span class="status-value"><span class="status-dot {qdrant_dot}"></span>{"Hazır" if backend_status.get("qdrant_configured") else "Bağlantı Yok"}</span>
        </div>
        <div class="status-item">
            <span class="status-label">Yüklenen Veriler</span>
            <span class="status-value" style="color:#06b6d4; font-weight:600;">{backend_status.get("total_points", 0)} Parça</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Preset Scenarios
    st.markdown("<div class='status-title'>Demo Senaryoları</div>", unsafe_allow_html=True)
    
    scenarios = [
        {"label": "Yıllık İzin Hakkı", "q": "3 yıldır çalışıyorum. Kaç gün yıllık izin hakkım var?", "role": "Çalışan"},
        {"label": "Evlilik İzni", "q": "Evlilik izni kaç gün?", "role": "Çalışan"},
        {"label": "Veri Analisti İlanı", "q": "Veri Analisti iş ilanı oluştur.", "role": "İK Uzmanı"},
        {"label": "İK Uzmanı Görevleri", "q": "İnsan Kaynakları Uzmanının görevleri nelerdir?", "role": "Yönetici / İK"}
    ]
    
    for idx, sc in enumerate(scenarios):
        if st.button(f"{sc['role']} | {sc['label']}", key=f"sc_{idx}", use_container_width=True):
            st.session_state.preset_question = sc['q']
            st.rerun()

    st.markdown("""
    <div style="margin-top: 40px; font-size: 11px; color: #64748b; text-align: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 16px;">
        <p>© 2026 HR Copilot AI PoC</p>
        <p>Python Streamlit & FastAPI</p>
    </div>
    """, unsafe_allow_html=True)

# Main Workspace Layout
st.title("HR Copilot AI")
st.caption("Kurum içi politika, prosedür, mevzuat ve İK süreçleriyle ilgili sorularınızı yanıtlar.")

# If collection is not loaded, show warning
if is_online and not backend_status.get("collection_exists"):
    st.warning("Qdrant veritabanında veri bulunmamaktadır. Lütfen OpenAI API anahtarınızı `.env` dosyasına girdikten sonra `python scripts/upload_vectors.py` betiğini çalıştırarak verileri yükleyin.")

# Render Chat History
for msg in st.session_state.messages:
    if msg["sender"] == "user":
        st.markdown(f"""
        <div class="user-bubble">
            <div class="bubble-sender user-sender">Siz</div>
            {msg["text"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-bubble">
            <div class="bubble-sender assistant-sender">HR Copilot</div>
            {msg["text"]}
        </div>
        """, unsafe_allow_html=True)
        
        # If there are sources, render expander for sources
        if msg.get("chunks"):
            with st.expander("Kullanılan Kaynakları Göster (" + str(len(msg["chunks"])) + " döküman)"):
                for chunk in msg["chunks"]:
                    score_pct = chunk.get("score", 0) * 100
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-meta">
                            <span class="badge-category">{chunk.get('category', 'Döküman')}</span>
                            <span class="badge-page">Sayfa {chunk.get('page', 1)}</span>
                            <span class="source-score">Benzerlik: {score_pct:.1f}%</span>
                        </div>
                        <div class="source-title">{chunk.get('title')}</div>
                        <div style="font-size:11px; color:#94a3b8; font-style:italic; margin-top:2px;">Bölüm: {chunk.get('section', 'Genel')} | Dosya: {chunk.get('source_file')}</div>
                        <div class="source-text">{chunk.get('content')}</div>
                    </div>
                    """, unsafe_allow_html=True)

# Handle Question Ingestion
question = None
if st.session_state.preset_question:
    question = st.session_state.preset_question
    st.session_state.preset_question = None  # Reset trigger
else:
    question = st.chat_input("Yıllık izin hesaplama, iş tanımları veya İK süreçleri hakkında soru sorun...")

if question:
    # Render user message bubble instantly
    st.markdown(f"""
    <div class="user-bubble">
        <div class="bubble-sender user-sender">Siz</div>
        {question}
    </div>
    """, unsafe_allow_html=True)
    
    # Store in history
    st.session_state.messages.append({"sender": "user", "text": question})
    
    # Trigger assistant response
    with st.spinner("HR Copilot yanıt oluşturuyor..."):
        try:
            # Make API Call to FastAPI backend
            res = requests.post(
                f"{BACKEND_URL}/chat",
                headers={"Content-Type": "application/json"},
                json={"message": question, "top_k": 10},
                timeout=30
            )
            
            if res.status_code == 200:
                data = res.json()
                answer = data["answer"]
                chunks = data["chunks"]
                
                # Store and rerun to render updated interface
                st.session_state.messages.append({
                    "sender": "assistant",
                    "text": answer,
                    "chunks": chunks
                })
                st.rerun()
            else:
                try:
                    err_detail = res.json().get("detail", "Bilinmeyen sunucu hatası")
                except Exception:
                    err_detail = res.text
                st.error(f"Sunucu Hatası: {err_detail}")
        except Exception as e:
            st.error(f"Bağlantı Hatası: Backend sunucusu çalışıyor mu? (Detay: {str(e)})")
