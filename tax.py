import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date
import qrcode
from PIL import Image
from qreader import QReader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import os

# ---------------- Firebase Init ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")  # put your Firebase service key
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("🎓 Student Attendance System with QR")

# ---------------- Register Student & Generate Pass ----------------
with st.expander("➕ Register Student & Generate Pass"):
    name = st.text_input("Student Name")
    pass_id = st.text_input("Assign Pass ID")

    if st.button("Generate Pass"):
        if name and pass_id:
            # Save student in Firestore
            db.collection("students").document(pass_id).set({
                "name": name,
                "pass_id": pass_id
            })

            # Generate QR Code
            qr = qrcode.make(pass_id)
            qr_file = f"{pass_id}_qr.png"
            qr.save(qr_file)

            st.image(qr_file, caption=f"QR Code for {name}")
            with open(qr_file, "rb") as f:
                st.download_button("⬇ Download Pass (QR)", f, file_name=qr_file)

        else:
            st.error("Please enter name and pass ID!")

# ---------------- Attendance Marking ----------------
with st.expander("📝 Mark Attendance via QR"):
    uploaded_file = st.file_uploader("Upload QR Image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded QR")

        qreader = QReader()
        decoded = qreader.detect_and_decode(img)

        if decoded:
            pass_id = decoded[0]
            st.success(f"✅ QR Code Detected: {pass_id}")

            today = str(date.today())
            student_ref = db.collection("students").document(pass_id).get()

            if student_ref.exists:
                student = student_ref.to_dict()
                name = student["name"]

                # Save attendance
                db.collection("attendance").document(today).set({
                    pass_id: {"name": name, "status": "Present"}
                }, merge=True)

                st.success(f"Attendance marked for {name}")
            else:
                st.error("❌ Student not found in database!")
        else:
            st.error("⚠ Could not read QR code")

# ---------------- Generate PDF Report ----------------
if st.button("📄 Generate Attendance Report"):
    today = str(date.today())
    attendance_doc = db.collection("attendance").document(today).get()

    if attendance_doc.exists:
        attendance_data = attendance_doc.to_dict()

        pdf_file = f"attendance_{today}.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        data = [["Pass ID", "Name", "Status"]]

        for pid, details in attendance_data.items():
            data.append([pid, details["name"], details["status"]])

        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 1, colors.black)
        ]))

        doc.build([table])

        st.success(f"📄 PDF Generated for {today}")
        with open(pdf_file, "rb") as f:
            st.download_button("⬇ Download Report", f, file_name=pdf_file, mime="application/pdf")
    else:
        st.warning("⚠ No attendance found for today!")

