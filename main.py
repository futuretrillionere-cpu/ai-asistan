import streamlit as st
import os

st.set_page_config(page_title="AI Asistan", page_icon="🚀", layout="wide")

# Güvenli Kütüphane Kontrolleri
try:
    import google.generativeai as genai
    from supabase import create_client, Client
    from PIL import Image
    from pypdf import PdfReader
    LIBS_OK = True
except ImportError:
    LIBS_OK = False

# Bilgileri güvenli şekilde Streamlit Secrets'tan alıyoruz (GitHub engeline takılmamak için)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY = "", "", ""

if LIBS_OK and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        pass

@st.cache_resource
def get_supabase():
    if not LIBS_OK or not SUPABASE_URL or not SUPABASE_KEY: return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = get_supabase()

if "user" not in st.session_state:
    st.session_state["user"] = None

st.sidebar.title("🔐 Kullanıcı Paneli")

if st.session_state["user"] is None:
    islem = st.sidebar.radio("İşlem", ["Giriş Yap", "Kayıt Ol"])
    email = st.sidebar.text_input("E-posta")
    sifre = st.sidebar.text_input("Şifre", type="password")
    
    if st.sidebar.button(islem):
        if not supabase:
            st.sidebar.error("Veritabanı bağlantısı yok veya anahtarlar eksik!")
        elif email and sifre:
            try:
                if islem == "Kayıt Ol":
                    supabase.auth.sign_up({"email": email, "password": sifre})
                    st.sidebar.success("Kayıt başarılı! Giriş yapın.")
                else:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": sifre})
                    st.session_state["user"] = res.user
                    st.sidebar.success("Giriş başarılı!")
                    st.rerun()
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")
        else:
            st.sidebar.warning("Alanları doldurun.")
else:
    st.sidebar.success(f"Giriş yapıldı:\n{getattr(st.session_state['user'], 'email', 'Kullanıcı')}")
    if st.sidebar.button("Çıkış Yap"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state["user"] = None
        st.rerun()

st.title("🚀 AI Asistan - SaaS Sürümü")

if st.session_state["user"] is None:
    st.info("👋 Devam etmek için lütfen sol menüden giriş yapın.")
else:
    st.markdown("---")
    uploaded_file = st.file_uploader("Görsel veya PDF yükle", type=["png", "jpg", "jpeg", "pdf"])
    
    file_content, file_type = None, None
    if uploaded_file and LIBS_OK:
        ext = uploaded_file.name.split(".")[-1].lower()
        if ext in ["png", "jpg", "jpeg"]:
            file_type, file_content = "image", Image.open(uploaded_file)
            st.image(file_content, caption="Yüklenen Görsel", width=300)
        elif ext == "pdf":
            file_type = "pdf"
            reader = PdfReader(uploaded_file)
            file_content = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
            st.success(f"📄 PDF okundu ({len(reader.pages)} sayfa)")

    prompt = st.text_area("Yapay zekaya ne sormak istersin?", placeholder="Sorunuz...")
    
    if st.button("Gönder ve Analiz Et") and prompt:
        if not LIBS_OK or not GEMINI_API_KEY:
            st.error("Kütüphaneler veya Gemini API anahtarı eksik!")
        else:
            try:
                model = genai.GenerativeModel("gemini-2.5-flash")
                with st.spinner("Yapay zeka düşünüyor..."):
                    if file_type == "image":
                        res = model.generate_content([file_content, prompt])
                    elif file_type == "pdf":
                        res = model.generate_content(f"Metin:\n{file_content}\n\nSoru: {prompt}")
                    else:
                        res = model.generate_content(prompt)
                    
                    st.markdown("### 💡 Cevap:")
                    st.write(res.text)
            except Exception as e:
                st.error(f"Hata oluştu: {e}")