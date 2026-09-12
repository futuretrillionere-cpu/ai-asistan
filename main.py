import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

st.set_page_config(page_title="AI Asistan - SaaS", page_icon="🤖", layout="wide")

try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except Exception:
    supabase = None

st.title("🤖 AI Asistan - SaaS Sürümü")

st.sidebar.header("🔐 Kullanıcı Paneli")

if "user" not in st.session_state:
    st.session_state.user = None

if "credits" not in st.session_state:
    st.session_state.credits = 5

if not st.session_state.user:
    auth_mode = st.sidebar.radio("İşlem Seçin", ["Giriş Yap", "Kayıt Ol"])
    email = st.sidebar.text_input("E-posta")
    password = st.sidebar.text_input("Şifre", type="password")
    
    if st.sidebar.button("Onayla"):
        if supabase:
            try:
                if auth_mode == "Kayıt Ol":
                    response = supabase.auth.sign_up({"email": email, "password": password})
                    st.sidebar.success("Kayıt başarılı! Lütfen giriş yapın.")
                else:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = response.user
                    st.sidebar.success("Giriş başarılı!")
                    st.rerun()
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")
        else:
            if email and password:
                st.session_state.user = {"email": email}
                st.sidebar.success("Test modunda giriş yapıldı!")
                st.rerun()
            else:
                st.sidebar.warning("Lütfen alanları doldurun.")
else:
    user_email = st.session_state.user.get('email', 'Kullanıcı') if isinstance(st.session_state.user, dict) else st.session_state.user.email
    st.sidebar.write(f"Hoş geldin, **{user_email}**")
    
    st.sidebar.metric(label="Kalan Kredi", value=st.session_state.credits)
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.user = None
        st.rerun()

    st.sidebar.divider()
    api_key_input = st.sidebar.text_input("Gemini API Key", type="password")
    selected_model = st.sidebar.selectbox("Model Seç", ["gemini-1.5-flash", "gemini-1.5-pro"])

if st.session_state.user:
    if st.session_state.credits > 0:
        user_prompt = st.text_area("Yapay zekaya bir şeyler sorun...")
        
        if st.button("Gönder") and user_prompt:
            if not api_key_input:
                st.warning("Lütfen sol menüden Gemini API Key girin.")
            else:
                try:
                    genai.configure(api_key=api_key_input)
                    model = genai.GenerativeModel(selected_model)
                    with st.spinner("Yapay zeka düşünüyor..."):
                        response = model.generate_content(user_prompt)
                        st.markdown("### Cevap:")
                        st.write(response.text)
                        
                        # Kredi düşürme
                        st.session_state.credits -= 1
                        st.rerun()
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")
    else:
        st.error("Krediniz bitti!")
else:
    st.info("Sol menüden giriş yapın.")