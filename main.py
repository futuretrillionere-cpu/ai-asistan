import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pypdf import PdfReader

load_dotenv()

# --------------------------------------------------------------------------
# SAYFA YAPILANDIRMASI
# --------------------------------------------------------------------------
st.set_page_config(page_title="AI Asistan - SaaS", page_icon="🚀", layout="wide")

# --------------------------------------------------------------------------
# BAĞLANTI BİLGİLERİ (Environment veya Streamlit Secrets)
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# OTURUM DURUMU (session_state) BAŞLANGIÇ DEĞERLERİ
# --------------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_metni" not in st.session_state:
    st.session_state.pdf_metni = ""
if "pdf_adi" not in st.session_state:
    st.session_state.pdf_adi = ""


# --------------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR - AUTH
# --------------------------------------------------------------------------
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
    st.session_state.pdf_metni = ""
    st.session_state.pdf_adi = ""


# --------------------------------------------------------------------------
# YARDIMCI FONKSİYON - PDF OKUMA
# --------------------------------------------------------------------------
def pdf_metnini_cikar(yuklenen_dosya) -> str:
    try:
        okuyucu = PdfReader(yuklenen_dosya)
        metin_parcalari = []
        for sayfa in okuyucu.pages:
            sayfa_metni = sayfa.extract_text()
            if sayfa_metni:
                metin_parcalari.append(sayfa_metni)
        return "\n".join(metin_parcalari)
    except Exception as e:
        st.error(f"PDF okunurken hata oluştu: {e}")
        return ""
    # --------------------------------------------------------------------------
# YAN MENÜ - GİRİŞ / KAYIT PANELİ
# --------------------------------------------------------------------------
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

        st.divider()

        # --- PDF YÜKLEME ALANI ---
        st.subheader("📄 PDF Yükle")
        yuklenen_pdf = st.file_uploader("Bir PDF dosyası seç", type=["pdf"])

        if yuklenen_pdf is not None:
            if yuklenen_pdf.name != st.session_state.pdf_adi:
                with st.spinner("PDF okunuyor..."):
                    metin = pdf_metnini_cikar(yuklenen_pdf)
                    st.session_state.pdf_metni = metin
                    st.session_state.pdf_adi = yuklenen_pdf.name
                if metin:
                    st.success(f"'{yuklenen_pdf.name}' yüklendi ({len(metin)} karakter okundu).")
                else:
                    st.warning("PDF'den metin çıkarılamadı (taranmış görsel olabilir).")

        if st.session_state.pdf_metni:
            st.caption(f"Aktif belge: {st.session_state.pdf_adi}")
            if st.button("PDF'i kaldır"):
                st.session_state.pdf_metni = ""
                st.session_state.pdf_adi = ""
                st.rerun()


# --------------------------------------------------------------------------
# ANA EKRAN
# --------------------------------------------------------------------------
st.title("🚀 AI Asistan - SaaS Sürümü")

if st.session_state.user is None:
    st.info("👋 Devam etmek için lütfen sol menüden giriş yapın.")
    st.stop()

if st.session_state.pdf_metni:
    st.info(f"📄 Şu an '{st.session_state.pdf_adi}' belgesi hakkında konuşuyorsun. Bu belgeyle ilgili soru sorabilirsin.")

# Sohbet geçmişini göster
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Kullanıcıdan yeni mesaj al
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

                if st.session_state.pdf_metni:
                    pdf_baglam = st.session_state.pdf_metni[:15000]
                    tam_prompt = (
                        f"Aşağıda bir PDF belgesinin içeriği var. Kullanıcının sorularını "
                        f"bu belgeye dayanarak cevapla.\n\n"
                        f"--- BELGE İÇERİĞİ ---\n{pdf_baglam}\n--- BELGE SONU ---\n\n"
                        f"--- KONUŞMA GEÇMİŞİ ---\n{gecmis_metin}"
                    )
                else:
                    tam_prompt = gecmis_metin

                yanit = model.generate_content(tam_prompt)
                cevap = yanit.text
            except Exception as e:
                cevap = f"Bir hata oluştu: {e}"

            st.markdown(cevap)

    st.session_state.messages.append({"role": "assistant", "content": cevap})