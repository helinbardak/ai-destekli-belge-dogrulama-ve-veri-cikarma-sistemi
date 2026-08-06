import streamlit as st
import base64
import time
from dotenv import load_dotenv

from rules.settings import COMPANY_THRESHOLD
from services.ai_service import analyze_document_with_ai

load_dotenv()

st.set_page_config(page_title="Konut Hasar Evrak PortalÄ±", layout="wide")

st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)

st.markdown("""
    <style>
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color:
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .info-card {
        background:
        border-radius: 10px;
        padding: 25px;
        border: 1px solid
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }
    
    .red-bordered-card {
        border-left: 4px solid
    }
    
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploadDropzone"] {
        background-color:
        border: 2px dashed
        border-radius: 12px !important;
        padding: 48px 20px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover,
    [data-testid="stFileUploadDropzone"]:hover {
        background-color:
        border-color:
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] svg,
    [data-testid="stFileUploaderDropzoneInstructions"] [data-testid*="Icon"] {
        width: 26px !important;
        height: 26px !important;
        font-size: 26px !important;
        line-height: 26px !important;
        color:
        background-color:
        padding: 19px !important;
        border-radius: 50% !important;
        margin-bottom: 14px !important;
        box-sizing: content-box !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] span:not([data-testid*="Icon"]),
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        font-size: 0px !important; 
        color: transparent !important;
        line-height: 0 !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] span:not([data-testid*="Icon"])::after {
        content: "Belgelerinizi buraya sÃ¼rÃ¼kleyip bÄ±rakÄ±n";
        font-size: 16px !important;
        color:
        font-weight: 600 !important;
        line-height: 1.4 !important;
        display: block !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] small::after {
        content: "veya dosya seÃ§mek iÃ§in tÄ±klayÄ±nÄ±z (PDF, JPG, PNG)";
        font-size: 13px !important;
        color:
        font-weight: 400 !important;
        line-height: 1.4 !important;
        display: block !important;
        margin-top: 6px !important;
    }
    
    [data-testid="stFileUploaderDropzone"] button,
    [data-testid="stFileUploadDropzone"] button {
        display: none !important;
    }
    
    [data-testid="stFileUploader"] [data-testid="stWidgetLabel"] {
        display: none !important;
    }
    
    [data-testid="stFileUploaderFile"] {
        background-color:
        border-radius: 8px !important;
        border: 1px solid
    }
    
    [data-testid="stFileUploaderFile"] button,
    [data-testid*="FileUploaderDeleteBtn"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        color:
        background-color: transparent !important;
        border-radius: 50% !important;
        opacity: 1 !important;
    }
    [data-testid="stFileUploaderFile"] button:hover,
    [data-testid*="FileUploaderDeleteBtn"]:hover {
        color:
        background-color:
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color:
        border-radius: 10px !important;
        border: 1px solid
        box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
    }
    
    .stButton > button {
        border-radius: 8px !important;
        padding: 16px 24px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button[data-testid="baseButton-primary"] {
        background-color:
        color:
        border: none !important;
    }
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background-color:
    }
    .stButton > button:disabled {
        background-color:
        color:
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

beklenen_belgeler = [
    "Tapu Belgesi",
    "Kimlik Belgesi",
    "Ä°mzalÄ± Beyan DilekÃ§esi",
    "IBAN / Banka Hesap Bilgisi"
]
BEKLENEN_BELGE_SAYISI = len(beklenen_belgeler)

if 'analiz_edilenler' not in st.session_state:
    st.session_state.analiz_edilenler = {}

st.markdown("""
<div style="display: flex; align-items: center; padding: 10px 0 30px 0;">
    <div style="background-color:
        <i class="fas fa-shield-alt"></i>
    </div>
    <div>
        <h1 style="color:
        <p style="color:
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2])

bulunan_tipler = list(st.session_state.analiz_edilenler.values())
belge_durumlari = []
for belge in beklenen_belgeler:
    eslesti = any(belge.lower() in t.lower() or t.lower() in belge.lower() for t in bulunan_tipler)
    belge_durumlari.append((belge, eslesti))
eksik_belge_sayisi = sum(1 for _, eslesti in belge_durumlari if not eslesti)

with col1:
    html_bilgi = (
        "<div class='info-card red-bordered-card'>"
        "<h3 style='color:
        "<p style='color:
        "<h4 style='color:
        "<p style='color:
        "<a href='https://www.anadolusigorta.com.tr/hasar-merkezi/hasar-evraklari/oto-disi-hasar' target='_blank' style='color:
        "</div>"
    )
    st.markdown(html_bilgi, unsafe_allow_html=True)
    
    html_liste = """
    <div class="info-card">
        <h3 style="color:
    """
    
    for belge, eslesti in belge_durumlari:
        if eslesti:
            html_liste += f"<div style='color:
        else:
            html_liste += f"<div style='color:
            
    html_liste += """
        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid
            Toplam 4 belgeyi eksiksiz yÃ¼klemeniz gerekmektedir.
        </div>
    </div>
    """
    st.markdown(html_liste, unsafe_allow_html=True)

with col2:
    with st.container(border=True):
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3 style="color:
            <span style="background-color:
        </div>
        """, unsafe_allow_html=True)
        
        yuklenen_dosyalar = st.file_uploader(
            "Belgelerinizi buraya sÃ¼rÃ¼kleyip bÄ±rakÄ±n (veya dosya seÃ§mek iÃ§in tÄ±klayÄ±nÄ±z)", 
            type=["pdf", "png", "jpg", "jpeg"], 
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if yuklenen_dosyalar is not None and len(yuklenen_dosyalar) >= BEKLENEN_BELGE_SAYISI:
            st.markdown("""
        <style>
            [data-testid*="FileUploader"][data-testid*="Dropzone"] { pointer-events: none !important; opacity: 0.6 !important; }
        </style>
        """, unsafe_allow_html=True)
        
        if yuklenen_dosyalar is not None and len(yuklenen_dosyalar) > BEKLENEN_BELGE_SAYISI:
            yuklenen_dosyalar = yuklenen_dosyalar[:BEKLENEN_BELGE_SAYISI]
            st.error("En fazla 4 adet belge yÃ¼kleyebilirsiniz.")

        html_slotlar = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin: 20px 0;">'
        for belge, eslesti in belge_durumlari:
            if eslesti:
                html_slotlar += f"""
                <div style="border: 1.5px solid
                    <div style="color:
                    <div style="color:
                </div>
                """
            else:
                html_slotlar += f"""
                <div style="border: 1.5px dashed
                    <div style="color:
                    <div style="color:
                </div>
                """
        html_slotlar += '</div>'
        st.markdown(html_slotlar, unsafe_allow_html=True)

        uploaded_count = len(yuklenen_dosyalar) if yuklenen_dosyalar else 0
        progress_percentage = (min(uploaded_count, BEKLENEN_BELGE_SAYISI) / BEKLENEN_BELGE_SAYISI) * 100
        
        st.markdown(f"""
        <div style="margin: 20px 0; background-color:
            <div style="display: flex; justify-content: space-between; font-size: 13px; color:
                <span>YÃ¼klenen Belgeler</span>
                <span>{min(uploaded_count, BEKLENEN_BELGE_SAYISI)} / {BEKLENEN_BELGE_SAYISI}</span>
            </div>
            <div style="width: 100%; background-color:
                <div style="width: {progress_percentage}%; background-color:
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        buton_alani = st.empty()
    
    st.markdown("""
    <p style="color:
        Belgeleriniz gizlilik esaslarÄ±na uygun olarak ÅŸifreli bir kanal Ã¼zerinden iÅŸlenmektedir. YalnÄ±zca hasar dosyanÄ±zÄ±n deÄŸerlendirilmesi amacÄ±yla kullanÄ±lacaktÄ±r.
    </p>
    """, unsafe_allow_html=True)

islem_bekleyen_dosyalar = [f for f in yuklenen_dosyalar if f.name not in st.session_state.analiz_edilenler] if yuklenen_dosyalar else []

if islem_bekleyen_dosyalar:
    buton_alani.button(f"Belgeleriniz analiz ediliyor... ({uploaded_count}/{BEKLENEN_BELGE_SAYISI})", disabled=True, key="btn_analyzing")
    for dosya in islem_bekleyen_dosyalar:
        with st.spinner(f"'{dosya.name}' inceleniyor..."):
            try:
                dosya.seek(0)
                base64_image = base64.b64encode(dosya.read()).decode('utf-8')
                ai_sonucu = analyze_document_with_ai(base64_image)
                tahmin = ai_sonucu.get('document_type', 'Bilinmeyen Belge')
                guven = ai_sonucu.get('confidence', 0)
                
                if guven >= COMPANY_THRESHOLD:
                    st.session_state.analiz_edilenler[dosya.name] = tahmin
                else:
                    st.session_state.analiz_edilenler[dosya.name] = "GeÃ§ersiz/OkunaksÄ±z Belge"
            except Exception as e:
                st.session_state.analiz_edilenler[dosya.name] = "Hata"
    st.rerun()
else:
    if len(yuklenen_dosyalar) > 0:
        if eksik_belge_sayisi == 0:
            if buton_alani.button("Belgeleri GÃ¶nder", type="primary", key="btn_submit"):
                st.success("Tebrikler! TÃ¼m belgeleriniz baÅŸarÄ±yla doÄŸrulandÄ± ve ÅŸirketimize iletildi.")
                st.balloons()
        else:
            buton_alani.button(f"Belgeleri GÃ¶nder ({uploaded_count}/{BEKLENEN_BELGE_SAYISI})", disabled=True, key="btn_missing")
    else:
        buton_alani.button(f"Belgeleri GÃ¶nder (0/{BEKLENEN_BELGE_SAYISI})", disabled=True, key="btn_empty")
