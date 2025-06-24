import streamlit as st
from db import get_connection
import base64
import requests
from fpdf import FPDF
import pandas as pd
import tempfile
import os

# Hide only the default Streamlit navigation sidebar, not your custom sidebar
hide_nav_style = """
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        div[data-testid="collapsedControl"] {display: none !important;}
    </style>
"""
st.markdown(hide_nav_style, unsafe_allow_html=True)

st.set_page_config(page_title="Student Dashboard", layout="wide")

# Student info from session
student_id = st.session_state.get("student_id", "N/A")
student_name = st.session_state.get("student_name", "Student")

st.title(f"Welcome, {student_name}")
st.markdown(f"**Register No.:** {student_id}")

# Database connection
conn = get_connection()
cursor = conn.cursor()

# Sidebar navigation
sidebar_option = st.sidebar.selectbox(
    "Select Action",
    ("All Courses", "My Courses", "Completed Courses")
)


def get_youtube_details(video_id):
    api_key = "AIzaSyCARU1XWaIxx4XbFxqZ3lpLxYnZPhw-01E"
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
    resp = requests.get(url)
    data = resp.json()
    if data.get("items"):
        snippet = data["items"][0]["snippet"]
        return {
            "title": snippet["title"],
            "thumbnail": snippet["thumbnails"]["default"]["url"]
        }
    return {"title": "(Unknown Title)", "thumbnail": ""}

def generate_certificate(student_id, course_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Fetch student name from DB
        cursor.execute("SELECT student_name FROM students WHERE student_id = %s", (student_id,))
        student_row = cursor.fetchone()
        student_name = student_row[0] if student_row else student_id

        # Fetch course name, admin_code from courses
        cursor.execute("SELECT course_name, admin_code FROM courses WHERE course_id = %s", (course_id,))
        course_row = cursor.fetchone()
        if course_row:
            course_name, admin_code = course_row
        else:
            course_name, admin_code = course_id, "N/A"

        # Fetch admin name using admin_code
        cursor.execute("SELECT admin_id FROM admin WHERE admin_code = %s", (admin_code,))
        admin_row = cursor.fetchone()
        staff_name = admin_row[0] if admin_row else "N/A"

        # Fetch completion date and time
        cursor.execute("SELECT completion_date, completion_time FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
        comp_row = cursor.fetchone()
        if comp_row:
            # completion_date is DATE, completion_time is TIME (may be time or timedelta)
            if comp_row[0]:
                # MySQL DATE comes as date or datetime.date
                completion_date = comp_row[0].strftime('%Y-%m-%d') if hasattr(comp_row[0], 'strftime') else str(comp_row[0])
            else:
                completion_date = "N/A"
            if comp_row[1]:
                import datetime
                if isinstance(comp_row[1], datetime.time):
                    completion_time = comp_row[1].strftime('%H:%M:%S')
                elif isinstance(comp_row[1], datetime.timedelta):
                    total_seconds = int(comp_row[1].total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    completion_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    completion_time = str(comp_row[1])
            else:
                completion_time = "N/A"
        else:
            completion_date = "N/A"
            completion_time = "N/A"

        # Generate visually appealing landscape certificate
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto = False, margin = 0)
        pdf.set_fill_color(230, 230, 250)
        pdf.rect(0, 0, 297, 210, 'F')  # light lavender background
        pdf.set_font("Arial", 'B', 36)
        pdf.set_text_color(40, 40, 90)
        pdf.cell(0, 30, "Certificate of Completion", ln=1, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", '', 20)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 15, f"This is to certify that", ln=1, align='C')
        pdf.set_font("Arial", 'B', 28)
        pdf.set_text_color(34, 49, 63)
        pdf.cell(0, 18, student_name, ln=1, align='C')
        pdf.set_font("Arial", '', 18)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 12, f"has successfully completed the course", ln=1, align='C')
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 15, course_name, ln=1, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", '', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Staff Code: {admin_code}    Staff Name: {staff_name}", ln=1, align='C')
        pdf.cell(0, 10, f"Date of Completion: {completion_date}", ln=1, align='C')
        pdf.cell(0, 10, f"Time of Completion: {completion_time}", ln=1, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 13)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, "Congratulations on your achievement and best wishes for your future learning!", ln=1, align='C')
        pdf.ln(15)
        pdf.set_font("Arial", '', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "_____________________________", ln=1, align='R')
        pdf.cell(0, 7, "Staff Signature", ln=1, align='R')
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf.output(tmp.name)
            pdf_bytes = tmp.read()
            tmp.close()
            # Remove the temporary file
            os.remove(tmp.name)
        
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="certificate_{course_name}.pdf">Download Certificate</a>'
        return href
    finally:
        cursor.close()
        conn.close()

# 1. All Courses (with Enroll option)
if sidebar_option == "All Courses":
    st.header("All Courses")
    cursor.execute("SELECT course_id, course_name, yt_link FROM courses")
    all_courses = cursor.fetchall()
    # Get enrolled course_ids
    cursor.execute("SELECT course_id FROM enrollments WHERE student_id = %s", (student_id,))
    enrolled_ids = {row[0] for row in cursor.fetchall()}
    for cid, cname, yt_link in all_courses:
        yt_info = get_youtube_details(yt_link) if yt_link else {"title": "", "thumbnail": ""}
        st.write(f"**{cid} - {cname}**")
        if yt_info["title"]:
            st.write(f"YouTube: {yt_info['title']}")
            st.image(yt_info["thumbnail"])
        if cid in enrolled_ids:
            st.success("Enrolled")
        else:
            if st.button(f"Enroll in {cid}"):
                cursor.execute("INSERT INTO enrollments (student_id, course_id, completed) VALUES (%s, %s, 0)", (student_id, cid))
                conn.commit()
                st.success(f"Enrolled in {cname}!")
                st.rerun()
        st.markdown("---")

# 2. My Courses (show enrolled, allow mark complete)
elif sidebar_option == "My Courses":
    st.header("My Courses")
    cursor.execute("""
        SELECT c.course_id, c.course_name, c.yt_link, e.completed
        FROM courses c
        JOIN enrollments e ON c.course_id = e.course_id
        WHERE e.student_id = %s
    """, (student_id,))
    enrolled_courses = cursor.fetchall()
    if enrolled_courses:
        for cid, cname, yt_link, completed in enrolled_courses:
            yt_info = get_youtube_details(yt_link) if yt_link else {"title": "", "thumbnail": ""}
            st.write(f"### {cid} - {cname}")
            if yt_link:
                st.write(f"YouTube: {yt_info['title']}")
                st.image(yt_info["thumbnail"])
                st.video(f"https://www.youtube.com/watch?v={yt_link}")
            if completed:
                st.success("Completed!")
                if st.button(f"Download Certificate for {cid}", key=f"cert_{cid}"):
                    cert_link = generate_certificate(student_id, cid)
                    st.markdown(cert_link, unsafe_allow_html=True)
            else:
                if st.button(f"Mark {cid} as Completed", key=f"complete_{cid}"):
                    from datetime import datetime
                    now = datetime.now()
                    cursor.execute("UPDATE enrollments SET completed=1, completion_date=%s, completion_time=%s WHERE student_id=%s AND course_id=%s", (now, now.time(), student_id, cid))
                    conn.commit()
                    st.success(f"Course {cid} marked as completed!")
                    st.rerun()
            st.markdown("---")
        # Show DataFrame of enrolled courses as a table
        import pandas as pd
        course_data = []
        for cid, cname, yt_link, completed in enrolled_courses:
            yt_url = f"https://www.youtube.com/watch?v={yt_link}" if yt_link else ""
            course_data.append([cid, cname, yt_url])
        df = pd.DataFrame(course_data, columns=["Course ID", "Course Name", "YouTube Video"])
        def make_clickable(val):
            return f'<a href="{val}" target="_blank">{val}</a>' if val else ''
        df["YouTube Video"] = df["YouTube Video"].apply(make_clickable)
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("You are not enrolled in any courses.")

# 3. Completed Courses (show certificates)
elif sidebar_option == "Completed Courses":
    st.header("Completed Courses")
    cursor.execute("""
        SELECT c.course_id, c.course_name, c.yt_link, e.completion_date
        FROM courses c
        JOIN enrollments e ON c.course_id = e.course_id
        WHERE e.student_id = %s AND e.completed = 1
    """, (student_id,))
    completed_courses = cursor.fetchall()
    if completed_courses:
        for cid, cname, yt_link, comp_date in completed_courses:
            yt_info = get_youtube_details(yt_link) if yt_link else {"title": "", "thumbnail": ""}
            st.write(f"### {cid} - {cname}")
            st.write(f"YouTube: {yt_info['title']}")
            st.image(yt_info["thumbnail"])
            st.write(f"Completed on: {comp_date.strftime('%Y-%m-%d %H:%M') if comp_date else 'N/A'}")
            if st.button(f"Download Certificate for {cid}", key=f"completed_cert_{cid}"):
                cert_link = generate_certificate(student_name, cname)
                st.markdown(cert_link, unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("No completed courses yet.")

    import pandas as pd
    course_data = []
    for cid, cname, yt_link in enrolled_courses:
        # Create clickable YouTube link
        yt_url = f"https://www.youtube.com/watch?v={yt_link}" if yt_link else ""
        course_data.append([cid, cname, yt_url])
    df = pd.DataFrame(course_data, columns=["Course ID", "Course Name", "YouTube Video"])
    # Make YouTube links clickable in table
    def make_clickable(val):
        return f'<a href="{val}" target="_blank">{val}</a>' if val else ''
    df["YouTube Video"] = df["YouTube Video"].apply(make_clickable)
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("You are not enrolled in any courses.")

# Logout button (sidebar only)
def logout():
    for key in ["logged_in", "user_role", "student_id", "student_name"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("You have been logged out.")
    # Redirect to Dashboard page after logout
    try:
        st.switch_page("Dashboard.py")
    except Exception:
        st.rerun()

if st.sidebar.button("Logout", key="sidebar_logout"):
    logout()
