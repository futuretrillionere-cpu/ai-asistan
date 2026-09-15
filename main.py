import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# Sayfa Yapılandırması
st.set_page_config(page_title="AI Asistan - SaaS", page_icon="🚀", layout="wide")

# Güvenli Import Kontrolü
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# API ve Supabase Bağlantı Bilgilerini Güvenli Al
GEMINI_API_KEY = ""
SUPABASE_URL = ""
SUPABASE_KEY = ""

try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    pass

try:
    SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
except Exception:
    pass

try:
    SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")
except Exception:
    pass

# Gemini Yapılandırması
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Supabase İstemcisi Oluşturma (Detaylı Hata Gösterimi ile)
@st.cache_resource
def init_supabase(url, key):
    if SUPABASE_AVAILABLE and url and key:
        try:
            return create_client(url, key)
        except Exception as e:
            return str(e)
    return "Eksik URL veya Key"

supabase_result = init_supabase(SUPABASE_URL, SUPABASE_KEY)
supabase = supabase_result if isinstance(supabase_result, Client) else None
supabase_error_detail = supabase_result if not isinstance(supabase_result, Client) else None

# Oturum Durumu Yönetimi
if "user" not in st.session_state:
    st.session_state["user"] = None

# Yan Menü (Giriş / Kayıt Paneli)
st.sidebar.title("🔐 Kullanıcı Paneli")

# Bağlantı Durumu Kontrolü (Hata ayıklamak için)
if not SUPABASE_URL or not SUPABASE_KEY:
    st.sidebar.error("⚠️ Supabase URL veya Key secrets içinde boş okunuyor!")
elif supabase is None:
    st.sidebar.error(f"⚠️ Bağlantı Hatası: {supabase_error_detail}")

if st.session_state["user"] is None:
    islem = st.sidebar.radio("İşlem Seçin", ["Giriş Yap", "Kayıt Ol"])
    
    email = st.sidebar.text_input("E-posta")
    sifre = st.sidebar.text_input("Şifre", type="password")
    
    if islem == "Kayıt Ol":
        if st.sidebar.button("Kayıt Ol"):
            if not supabase:
                st.sidebar.error("Supabase bağlantısı kurulamadı!")
            elif email and sifre:
                try:
                    response = supabase.auth.sign_up({"email": email, "password": sifre})
                    st.sidebar.success("Kayıt başarılı! Lütfen giriş yapın.")
                except Exception as e:
                    st.sidebar.error(f"Kayıt hatası: {e}")
            else:
                st.sidebar.warning("Lütfen alanları doldurun.")
                
    elif islem == "Giriş Yap":
        if st.sidebar.button("Giriş Yap"):
            if not supabase:
                st.sidebar.error("Supabase bağlantısı kurulamadı!")
            elif email and sifre:
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": sifre})
                    st.session_state["user"] = response.user
                    st.sidebar.success("Giriş başarılı!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Giriş hatası: {e}")
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
    st.warning("⚠️ Lütfen GEMINI_API_KEY anahtarınızı ekleyin.")
elif not GEMINI_AVAILABLE:
    st.error("⚠️ google-generativeai kütüphanesi ortamda bulunamadı.")
elif st.session_state["user"] is None:
    st.info("👋 Devam etmek için lütfen sol menüden giriş yapın veya kayıt olun.")
else:
    st.markdown("---")
  
    uploaded_file = st.file_uploader("Bir görsel veya PDF belgesi yükleyin (İsteğe bağlı)", type=["png", "jpg", "jpeg", "pdf"])
    
    file_content = None
    file_type = None
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        if file_extension in ["png", "jpg", "jpeg"] and PIL_AVAILABLE:
            file_type = "image"
            file_content = Image.open(uploaded_file)
            st.image(file_content, caption="Yüklenen Görsel", width=300)
        elif file_extension == "pdf" and PDF_AVAILABLE:
            file_type = "pdf"
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            file_content = text
            st.success(f"📄 PDF başarıyla okundu! ({len(reader.pages)} sayfa)")

    prompt = st.text_area("Yapay zekaya ne sormak istersin?", placeholder="Sorunuzu buraya yazın...") 
    if st.button("Gönder ve Analiz Et") and prompt:
            model = genai.GenerativeModel("gemini-2.5-flash")
            with st.spinner("Yapay zeka düşünüyor..."):
                
                if file_type == "image" and file_content:
                    response = model.generate_content([file_content, prompt])
                elif file_type == "pdf" and file_content:
                    combined_prompt = f"Aşağıdaki PDF metnini inceleyerek soruyu yanıtla:\n\nMetin:\n{file_content}\n\nSoru: {prompt}"
                