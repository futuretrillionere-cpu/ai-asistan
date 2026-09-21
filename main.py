import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

st.set_page_config(page_title="AI Asistan - SaaS", page_icon="🚀", layout="wide")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

if not GEMINI_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "⚠️ Gerekli anahtarlar bulunamadı. Lütfen .env dosyanı (yerelde) "
        "veya Streamlit Cloud > Settings > Secrets kısmını (canlıda) doldur:\n\n"
        "GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY"
    )
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

MODEL_NAME = "gemini-3.5-flash"

if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []


def kayit_ol(email: str, password: str):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return True, "Kayıt başarılı! Şimdi giriş yapabilirsin. (E-posta onayı gerekebilir.)"
    except Exception as e:
        return False, f"Kayıt hatası: {e}"


def giris_yap(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        return True, "Giriş başarılı!"
    except Exception as e:
        return False, f"Giriş hatası: {e}"


def cikis_yap():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.session_state.messages = []


with st.sidebar:
    st.title("🔐 Kullanıcı Paneli")

    if st.session_state.user is None:
        islem = st.radio("İşlem", ["Giriş Yap", "Kayıt Ol"])
        email = st.text_input("E-posta")
        password = st.text_input("Şifre", type="password")

        if islem == "Giriş Yap":
            if st.button("Giriş Yap"):
                basarili, mesaj = giris_yap(email, password)
                if basarili:
                    st.success(mesaj)
                    st.rerun()
                else:
                    st.error(mesaj)
        else:
            if st.button("Kayıt Ol"):
                basarili, mesaj = kayit_ol(email, password)
                if basarili:
                    st.success(mesaj)
                else:
                    st.error(mesaj)
    else:
        st.success(f"Giriş yapıldı: {st.session_state.user.email}")
        if st.button("Çıkış Yap"):
            cikis_yap()
            st.rerun()


st.title("🚀 AI Asistan - SaaS Sürümü")

if st.session_state.user is None:
    st.info("👋 Devam etmek için lütfen sol menüden giriş yapın.")
    st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

kullanici_mesaji = st.chat_input("Bir şeyler yaz...")

if kullanici_mesaji:
    st.session_state.messages.append({"role": "user", "content": kullanici_mesaji})
    with st.chat_message("user"):
        st.markdown(kullanici_mesaji)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyorum..."):
            try:
                model = genai.GenerativeModel(MODEL_NAME)
                gecmis_metin = "\n".join(
                    f"{m['role']}: {m['content']}" for m in st.session_state.messages[-10:]
                )
                yanit = model.generate_content(gecmis_metin)
                cevap = yanit.text
            except Exception as e:
                cevap = f"Bir hata oluştu: {e}"

            st.markdown(cevap)

    st.session_state.messages.append({"role": "assistant", "content": cevap})