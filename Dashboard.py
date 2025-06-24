import mysql.connector.connection
import streamlit as st
import streamlit.components.v1 as components
import mysql.connector

# Hide Streamlit sidebar completely
hide_sidebar_style = """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="stSidebar"] {display: none;}
        section[data-testid="stSidebar"] {display: none !important;}
        div[data-testid="collapsedControl"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

st.set_page_config(
    page_title="LMS Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📚"
)

# --- TOP SECTION ---
st.markdown("""
<div style='text-align:center; margin-top:1.5em;'>
    <h2>Welcome to the Learning Management System (LMS)</h2>
    <p style='font-size:1.1em; max-width:700px; margin:auto;'>
        The LMS is your one-stop platform to manage courses, assignments, grades, and communication for both staff and students. Stay organized, track progress, and access resources efficiently.
    </p>
</div>
""", unsafe_allow_html=True)

# --- MAIN CONTENT: TWO COLUMNS ---
col1, col2 = st.columns([1.2, 1], gap="large")

with col1:
    st.markdown('<h2 style="margin-bottom: 1.2em;">Features</h2>', unsafe_allow_html=True)
    feature_role = st.radio("View Features for:", ["Staff / Admin", "Student"], horizontal=True)
    st.write("")  # Small gap

    if feature_role == "Staff / Admin":
        features = [
            ("📚", "Manage Courses & Content", "Create, update, and organize course materials and resources."),
            ("📈", "Track Student Progress", "Monitor student attendance, submissions, and performance."),
            ("📝", "Grade Assignments", "Evaluate and provide feedback on student assignments."),
            ("📢", "Send Announcements", "Communicate important updates to students and staff."),
            ("📊", "View Analytics & Reports", "Analyze class performance and download reports."),
        ]
    else:
        features = [
            ("📚", "View & Enroll in Courses", "Browse available courses and enroll easily."),
            ("✍️", "Submit Assignments", "Upload and manage your assignment submissions."),
            ("📊", "Check Grades", "View your grades and instructor feedback."),
            ("💬", "Participate in Discussions", "Engage in course forums and group chats."),
            ("📚", "Access Learning Resources", "Download notes, references, and study materials."),
        ]

    # Display features as Streamlit cards in a grid
    for i in range(0, len(features), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(features):
                icon, title, desc = features[i + j]
                with cols[j]:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style='
                                background: #f8fafc;
                                border-radius: 12px;
                                padding: 0.8em 1.2em;
                                margin-bottom: 0.7em;
                                box-shadow: 0 2px 8px rgba(44,62,80,0.07);
                                border: 1.2px solid #e0eafc;
                                min-height: 70px;
                            '>
                                <span style='font-size:1.3em; margin-right:0.7em;'>{icon}</span>
                                <span style='font-weight:600; font-size:1.08em;'>{title}</span>
                                <br>
                                <span style='font-size:0.97em; color:#555;'>{desc}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

with col2:
    st.markdown('<h2 style="margin-bottom: 1.5em;">Login</h2>', unsafe_allow_html=True)
    role = st.radio("Role", ["Admin", "Student"], horizontal=True)
    if role == "Admin":
        with st.form("admin_login_form"):
            admin_id = st.text_input("Admin ID")
            admin_password = st.text_input("Password", type="password")
            admin_button = st.form_submit_button("Login as Admin")
        if admin_button:
            from db import get_connection
            connect = get_connection()
            cursor = connect.cursor()
            query = "SELECT * FROM admin WHERE admin_id = %s AND pass = %s"
            cursor.execute(query, (admin_id, admin_password))
            result = cursor.fetchone()
            if result:
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.admin_id = admin_id
                st.success("Login Successful!")
                try:
                    st.switch_page("E:\VS Projects\Intern\LMS-System\pages\AdminDashboard.py")
                except AttributeError:
                    st.info("Redirecting to Admin Dashboard... (If not redirected, please select AdminDashboard from the sidebar)")
            else:
                st.error("Invalid Credentials")
    else:
        with st.form("student_login_form"):
            student_id = st.text_input("Register No.")
            student_password = st.text_input("Password", type="password")
            student_button = st.form_submit_button("Login as Student")
        if student_button:
            from db import get_connection
            connect = get_connection()
            cursor = connect.cursor()
            query = "SELECT * FROM students WHERE student_id = %s AND password = %s"
            cursor.execute(query, (student_id, student_password))
            result = cursor.fetchone()
            if result:
                st.session_state.logged_in = True
                st.session_state.user_role = "student"
                st.session_state.student_id = student_id
                st.success("Login Successful!")
                try:
                    st.switch_page("E:\VS Projects\Intern\LMS-System\pages\StudentDashboard.py")
                except AttributeError:
                    st.info("Redirecting to Student Dashboard... (If not redirected, please select StudentDashboard from the sidebar)")
            else:
                st.error("Invalid Credentials")
