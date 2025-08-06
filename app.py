
import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, firestore
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
from reportlab.lib.utils import ImageReader
from PIL import Image
import io
import os
import datetime

# 🔐 Load Firebase credentials from Streamlit secrets
if not firebase_admin._apps:
    cred_dict = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

# ✅ Firestore database instance
db = firestore.client()

# Title
st.title("Fiesta Hub - Ticket Generator 🎟️")

# Ticket type
ticket_type = st.selectbox("Select Ticket Type", ["Advance", "Gate"])

# Customer input form
st.subheader("Fill Your Details")
name = st.text_input("Full Name")
mpesa_code = st.text_input("M-Pesa Code")

# Submit button
if st.button("Generate Ticket"):
    if not name or not mpesa_code:
        st.warning("Please fill in all the fields.")
    else:
        # Check if MPesa code exists in database
        existing = db.collection("tickets").where("mpesa_code", "==", mpesa_code).stream()
        if any(existing):
            st.error("This M-Pesa code has already been used. Please use a unique one.")
        else:
            # Save to Firebase
            db.collection("tickets").add({
                "name": name,
                "mpesa_code": mpesa_code,
                "ticket_type": ticket_type,
                "scanned": False,
                "timestamp": datetime.datetime.now()
            })

            # Generate QR code
            qr_data = f"{name} | {mpesa_code}"
            qr_img = qrcode.make(qr_data)

            # Prepare ticket background and logo
            background_path = "ticket_background.jpg"  # must be in repo
            logo_path = "fiesta_logo.png"  # must be in repo

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A6)

            # Draw background
            if os.path.exists(background_path):
                bg = ImageReader(background_path)
                can.drawImage(bg, 0, 0, width=A6[0], height=A6[1])

            # Draw logo
            if os.path.exists(logo_path):
                logo = ImageReader(logo_path)
                can.drawImage(logo, 10, A6[1]-60, width=50, height=50)

            # Draw ticket info
            can.setFont("Helvetica-Bold", 10)
            can.drawString(10, A6[1]-70, f"Name: {name}")
            can.drawString(10, A6[1]-85, f"Ticket Type: {ticket_type}")
            can.drawString(10, A6[1]-100, f"M-Pesa: {mpesa_code}")

            # Draw QR code
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer)
            qr_buffer.seek(0)
            qr_reader = ImageReader(qr_buffer)
            can.drawImage(qr_reader, A6[0]-80, 10, width=70, height=70)

            can.save()
            packet.seek(0)

            # Output ticket
            st.success("Ticket Generated Successfully!")
            st.download_button(
                label="Download Your Ticket 🎫",
                data=packet,
                file_name=f"{name.replace(' ', '_')}_ticket.pdf",
                mime="application/pdf"
            )
