import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from PIL import Image
from pypdf import PdfReader

load_dotenv()

# Sayfa Yapılandırması
st.set_page_config(page_title="AI Asistan - SaaS", page_icon="🚀", layout="wide")

# API ve Supabase Bağlantı Bilgilerini Al (Environment veya Streamlit Secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

# Gemini Yapılandırması
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Supabase İstemcisi Oluşturma
@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return None

supabase = init_supabase()

# Oturum Durumu Yönetimi (Session State)
if "user" not in st.session_state:
    st.session_state["user"] = None

# Yan Menü (Giriş / Kayıt Paneli)
st.sidebar.title("🔐 Kullanıcı Paneli")

if st.session_state["user"] is None:
    islem = st.sidebar.radio("İşlem Seçin", ["Giriş Yap", "Kayıt Ol"])
    
    email = st.sidebar.text_input("E-posta")
    sifre = st.sidebar.text_input("Şifre", type="password")
    
    if islem == "Kayıt Ol":
        if st.sidebar.button("Kayıt Ol"):
            if not supabase:
                st.sidebar.error("Supabase bağlantısı eksik veya hatalı!")
            elif email and sifre:
                try:
                    response = supabase.auth.sign_up({"email": email, "password": sifre})
                    st.sidebar.success("Kayıt başarılı! Lütfen giriş yapın.")
                except Exception as e:
                    st.sidebar.error(f"Kayıt hatası: {e}")
            else:
                st.sidebar.warning("Lütfen alanları doldurun.")
        else:
         st.sidebar.success(f"Giriş yapıldı:\n{getattr(st.session_state['user'], 'email', 'Kullanıcı')}")
    if st.sidebar.button("Çıkış Yap"):
        if supabase:
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
        st.session_state["user"] = None
        st.rerun()

# Ana Ekran
st.title("🚀 AI Asistan - SaaS Sürümü")

if not GEMINI_API_KEY:
    st.warning("⚠️ Lütfen GEMINI_API_KEY anahtarınızı ekleyin (.env veya Secrets).")
elif st.session_state["user"] is None:
    st.info("👋 Devam etmek için lütfen sol menüden giriş yapın veya kayıt olun.")
else:
    st.markdown("---")
    
    # Dosya Yükleme Alanı (PDF ve Görsel)
    uploaded_file = st.file_uploader("Bir görsel veya PDF belgesi yükleyin (İsteğe bağlı)", type=["png", "jpg", "jpeg", "pdf"])
    
    file_content = None
    file_type = None
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        if file_extension in ["png", "jpg", "jpeg"]:
            file_type = "image"
            file_content = Image.open(uploaded_file)
            st.image(file_content, caption="Yüklenen Görsel", width=300)
        elif file_extension == "pdf":
            file_type = "pdf"
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            file_content = text
            st.success(f"📄 PDF başarıyla okundu! ({len(reader.pages)} sayfa)")

    # Kullanıcı Girdi Alanı
    prompt = st.text_area("Yapay zekaya ne sormak istersin?", placeholder="Sorunuzu buraya yazın...")
    
    if st.button("Gönder ve Analiz Et") and prompt:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            with st.spinner("Yapay zeka düşünüyor..."):
                
                # İçerik türüne göre model çağrısı
              if file_type == "image" and file_content:
                    response = model.generate_content([file_content, prompt])
              elif file_type == "pdf" and file_content:
                    combined_prompt = f"Aşağıdaki PDF metnini inceleyerek soruyu yanıtla:\n\nMetin:\n{file_content}\n\nSoru: {prompt}"
                    response = model.generate_content(combined_prompt)
              else:
                    response = model.generate_content(prompt)
                
              st.markdown("### 💡 Cevap:")
              st.write(response.text)
                
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")