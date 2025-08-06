
import streamlit as st # type: ignore
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import os

# Initialize Firebase (replace 'your-firebase-adminsdk.json' with your actual key file)
if not firebase_admin._apps:
    import json
from streamlit.runtime.secrets import secrets
cred = credentials.Certificate(json.loads(secrets["FIREBASE_KEY"]))

    firebase_admin.initialize_app(cred)
db = firestore.client()

# Set page config
st.set_page_config(page_title="Fiesta Hub Ticketing", layout="centered")

# Load logo
logo_path = "fiesta_logo.png"

# Function to check for duplicate M-Pesa code
def is_duplicate(mpesa_code):
    tickets_ref = db.collection("tickets")
    query = tickets_ref.where("mpesa_code", "==", mpesa_code).stream()
    return any(query)

# Generate ticket PDF
def generate_ticket_pdf(name, mpesa_code, ticket_type):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A6)
    width, height = A6

    # Background color splash style
    p.setFillColorRGB(0.95, 0.8, 1)
    p.rect(0, 0, width, height, fill=True)

    # Logo
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        p.drawImage(logo, 10, height - 60, width=80, preserveAspectRatio=True)

    # Ticket details
    p.setFont("Helvetica-Bold", 10)
    p.drawString(10, height - 80, f"Colour Splash 3.0")
    p.setFont("Helvetica", 8)
    p.drawString(10, height - 95, f"Name: {name}")
    p.drawString(10, height - 110, f"M-Pesa Code: {mpesa_code}")
    p.drawString(10, height - 125, f"Type: {ticket_type}")
    p.drawString(10, height - 140, "24th Aug 2025 | 11AM till late")
    p.drawString(10, height - 155, "Canaville Resort, JujaFarm")

    # Generate QR code
    qr = qrcode.make(f"{name}_{mpesa_code}")
    qr_buffer = BytesIO()
    qr.save(qr_buffer)
    qr_buffer.seek(0)
    qr_img = ImageReader(qr_buffer)
    p.drawImage(qr_img, width - 90, 10, width=80, height=80)

    p.save()
    buffer.seek(0)
    return buffer

# Main form
st.markdown("<h2 style='text-align:center;'>🎉 Fiesta Hub Ticket Generator</h2>", unsafe_allow_html=True)

with st.form("ticket_form"):
    name = st.text_input("Your Full Name")
    mpesa_code = st.text_input("M-Pesa Code")
    ticket_type = st.selectbox("Ticket Type", ["Advance - KES 300", "Gate - KES 500"])
    submit = st.form_submit_button("Generate Ticket")

    if submit:
        if not name or not mpesa_code:
            st.error("Please fill in all details.")
        elif is_duplicate(mpesa_code):
            st.error("This M-Pesa code has already been used.")
        else:
            short_type = "Advance" if "Advance" in ticket_type else "Gate"
            ticket_pdf = generate_ticket_pdf(name, mpesa_code, short_type)

            # Save to Firebase
            db.collection("tickets").add({
                "name": name,
                "mpesa_code": mpesa_code,
                "ticket_type": short_type,
                "scanned": False,
                "timestamp": datetime.utcnow()
            })

            st.success("✅ Ticket generated successfully!")

            # PDF download
            b64 = base64.b64encode(ticket_pdf.read()).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="FiestaHub_Ticket.pdf">📥 Download Your Ticket</a>'
            st.markdown(href, unsafe_allow_html=True)
