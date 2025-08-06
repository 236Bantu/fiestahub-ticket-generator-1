import streamlit as st
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
import pyrebase
import json
import base64

# Firebase credentials from Streamlit secrets
cred_dict = json.loads(st.secrets["FIREBASE_CREDENTIALS"])

firebase_config = {
    "apiKey": cred_dict["private_key_id"],
    "authDomain": f"{cred_dict['project_id']}.firebaseapp.com",
    "databaseURL": "",
    "projectId": cred_dict["project_id"],
    "storageBucket": f"{cred_dict['project_id']}.appspot.com",
    "messagingSenderId": cred_dict["client_id"],
    "appId": "your-app-id",
    "serviceAccount": cred_dict
}

firebase = pyrebase.initialize_app(firebase_config)
storage = firebase.storage()

st.title("🎟️ Fiesta Hub Ticket Generator")

name = st.text_input("Enter your full name")
mpesa_code = st.text_input("Enter your M-Pesa payment code")
submit = st.button("Generate Ticket")

def generate_qr_code(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)
    return buffer

def generate_pdf(name, mpesa_code):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A6)

    p.drawString(30, 150, "🎉 Colour Splash 3.0")
    p.drawString(30, 135, f"Name: {name}")
    p.drawString(30, 120, f"Code: {mpesa_code}")
    p.drawString(30, 105, "Date: 24 August 2025")
    p.drawString(30, 90, "Venue: Canaville Resort")

    qr_buf = generate_qr_code(f"{name}-{mpesa_code}")
    p.drawImage(qr_buf, 30, 20, width=60*mm, height=60*mm)

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

if submit:
    if name and mpesa_code:
        st.success("Ticket generated!")
        pdf_file = generate_pdf(name, mpesa_code)
        b64 = base64.b64encode(pdf_file.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="ticket.pdf">📥 Download Your Ticket</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.error("Please fill in all the fields.")
