import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime, os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# ----------------- Firebase Init -----------------
if not firebase_admin._apps:  # ✅ Prevent duplicate initialization
    cred = credentials.Certificate("serviceAccountKey.json")  # <-- replace with your key
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ----------------- Streamlit UI -----------------
st.set_page_config(page_title="Student Attendance System", layout="wide")
st.title("🎓 Student Attendance Tracker")

menu = st.sidebar.radio("📌 Menu", ["Add Student", "Mark Attendance", "Generate Report"])

# ----------------- Add Student -----------------
if menu == "Add Student":
    st.subheader("➕ Register New Student")

    with st.form("student_form"):
        student_id = st.text_input("Student ID")
        name = st.text_input("Full Name")
        course = st.text_input("Course/Department")
        submit = st.form_submit_button("Add Student")

        if submit:
            if student_id and name:
                db.collection("students").document(student_id).set({
                    "name": name,
                    "course": course,
                })
                st.success(f"✅ Student {name} ({student_id}) added successfully!")
            else:
                st.error("⚠️ Please fill all required fields.")

# ----------------- Mark Attendance -----------------
elif menu == "Mark Attendance":
    st.subheader("📝 Mark Attendance")

    students = db.collection("students").stream()
    for student in students:
        data = student.to_dict()
        sid = student.id
        status = st.radio(
            f"{sid} - {data['name']} ({data.get('course','')})",
            ["Present", "Absent"],
            key=f"att_{sid}_{datetime.date.today()}"
        )
        # Save attendance
        db.collection("attendance").document(f"{sid}_{datetime.date.today()}").set({
            "student_id": sid,
            "name": data['name'],
            "course": data.get('course', ''),
            "date": str(datetime.date.today()),
            "status": status
        })

# ----------------- Generate Report -----------------
elif menu == "Generate Report":
    st.subheader("📄 Generate Attendance Report (PDF)")

    date = st.date_input("Select Date", datetime.date.today())
    generate = st.button("Generate Report")

    if generate:
        records = db.collection("attendance").where("date", "==", str(date)).stream()
        data = [["Student ID", "Name", "Course", "Date", "Status"]]

        for rec in records:
            r = rec.to_dict()
            data.append([r['student_id'], r['name'], r['course'], r['date'], r['status']])

        if len(data) == 1:
            st.warning("⚠️ No records found for this date.")
        else:
            # Generate PDF
            filename = f"Attendance_{date}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=letter)
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            doc.build([table])

            st.success(f"✅ Report generated: {filename}")
            with open(filename, "rb") as file:
                st.download_button("⬇️ Download PDF", file, file_name=filename)

            os.remove(filename)  # cleanup temp file
