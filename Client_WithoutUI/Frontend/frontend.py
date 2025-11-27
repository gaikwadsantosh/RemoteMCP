import streamlit as st
import requests
import os
from fastapi import HTTPException

BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    raise HTTPException(status_code=500, detail="BACKEND_URL not set")
#BACKEND_URL = "http://127.0.0.1:9000/interpret"

st.set_page_config(page_title="AI Financial Assistant", layout="centered")
st.title("💰 AI Financial Assistant")

st.write("Ask a financial question — the system will choose and call the right tool automatically.")

user_message = st.text_input("Enter your request:")
if st.button("Submit"):
    if not user_message.strip():
        st.warning("Please enter a message.")
    else:
        with st.spinner("Interpreting your request..."):
            try:
                response = requests.post(BACKEND_URL, json={"message": user_message})
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"**Tool Selected:** {data.get('tool')}")
                    st.json(data)
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
