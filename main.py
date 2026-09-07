import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from streamlit_mic_recorder import speech_to_text
import pypdf, json

st.set_page_config(page_title="AI Asistan", page_icon="🤖")

api_key = st.sidebar.text_input("API Key:", type="password")
client = genai.Client(api_key=api_key) if api_key else None
model = st.sidebar.selectbox("Model:", ["gemini-3.6-flash"])
if st.sidebar.button("Sohbeti Temizle"): st.session_state.messages = []; st.rerun()

st.title("🤖 AI Asistan")
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("image"): st.image(m["image"], width=300)

audio = speech_to_text(start_prompt="Konuş", stop_prompt="Dur", use_container_width=True, key='stt')
file = st.file_uploader("Görsel/Belge", type=["jpg", "png", "pdf", "txt"])
img = Image.open(file) if file and file.type in ["image/jpeg", "image/png"] else None
doc_text = "".join([p.extract_text() for p in pypdf.PdfReader(file).pages if p.extract_text()]) if file and file.type == "application/pdf" else (file.read().decode("utf-8") if file and file.type == "text/plain" else "")

if img: st.image(img, width=300)
if file and doc_text: st.success("Belge okundu!")

user_input = audio or st.chat_input("Bir şeyler yaz...")

if user_input and client:
    final_input = f"Belge:\n{doc_text}\n\nSoru: {user_input}" if doc_text else user_input
    st.session_state.messages.append({"role": "user", "content": user_input, "image": img})
    
    with st.chat_message("user"):
        st.markdown(user_input)
        if img: st.image(img, width=300)
    
    with st.chat_message("assistant"):
        history = [types.Content(role="user" if m["role"]=="user" else "model", parts=[types.Part.from_text(text=m["content"])]) for m in st.session_state.messages[:-1]]
        chat = client.chats.create(model=model, history=history)
        resp = chat.send_message([final_input, img] if img else final_input)
        st.markdown(resp.text)
        
        st.components.v1.html(f"""<script>
            var u = new SpeechSynthesisUtterance({json.dumps(resp.text)});
            u.lang = 'tr-TR'; u.rate = 0.9;
            window.speechSynthesis.speak(u);
        </script>""", height=0)
        
        st.session_state.messages.append({"role": "assistant", "content": resp.text})
elif user_input and not client:
    st.error("Önce sol panelden API anahtarını gir!")