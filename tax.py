import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# 🔹 Firebase Setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

st.title("🎓 Student Attendance System")

# Input student Pass ID
pass_id = st.text_input("Enter Pass ID")

if st.button("Mark Attendance"):
    today = str(date.today())

    # Check if student exists
    students_ref = db.collection("students").where("pass_id", "==", pass_id).get()
    if students_ref:
        student = students_ref[0].to_dict()
        name = student["name"]

        # Save attendance
        db.collection("attendance").document(today).set({
            pass_id: {"name": name, "status": "Present"}
        }, merge=True)

        st.success(f"✅ Attendance marked for {name}")
    else:
        st.error("❌ Student not found!")

# 🔹 Generate Attendance PDF
if st.button("Generate PDF Report"):
    today = str(date.today())
    attendance_doc = db.collection("attendance").document(today).get()

    if attendance_doc.exists:
        attendance_data = attendance_doc.to_dict()

        # Prepare PDF
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
        st.success(f"📄 PDF Generated: {pdf_file}")
        with open(pdf_file, "rb") as f:
            st.download_button("⬇ Download Report", f, file_name=pdf_file, mime="application/pdf")
    else:
        st.warning("⚠ No attendance found for today!")

