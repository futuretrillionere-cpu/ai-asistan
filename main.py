import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="AI Asistan", page_icon="🤖", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "credits" not in st.session_state:
    st.session_state.credits = 5

st.sidebar.header("🔐 Kullanıcı Paneli")

if not st.session_state.user:
    email = st.sidebar.text_input("E-posta")
    password = st.sidebar.text_input("Şifre", type="password")
    if st.sidebar.button("Giriş Yap / Kayıt Ol"):
        if email and password:
            st.session_state.user = email
            st.success("Giriş başarılı!")
            st.rerun()
        else:
            st.warning("Bilgileri doldurun.")
else:
    st.sidebar.write(f"**{st.session_state.user}**")
    st.sidebar.metric("Kredi", st.session_state.credits)
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.user = None
        st.rerun()
    
    st.sidebar.divider()
    api_key = st.sidebar.text_input("Gemini API Key", type="password")
    model_choice = st.sidebar.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro"])

st.title("🤖 AI Asistan")

if st.session_state.user:
    if st.session_state.credits > 0:
        prompt = st.text_area("Yapay zekaya bir şeyler sorun...")
        if st.button("Gönder") and prompt:
            if not api_key:
                st.warning("Sol menüden API Key girin.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_choice)
                    with st.spinner("Düşünüyor..."):
                        res = model.generate_content(prompt)
                        st.markdown("### Cevap:")
                        st.write(res.text)
                        st.session_state.credits -= 1
                except Exception as e:
                    st.error(f"Hata: {e}")
    else:
        st.error("Krediniz bitti!")
else:
    st.info("Sol menüden giriş yapın.")