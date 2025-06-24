import streamlit as st
from db import get_connection

# Hide only the default Streamlit navigation sidebar, not your custom sidebar
hide_nav_style = """
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        div[data-testid="collapsedControl"] {display: none !important;}
    </style>
"""
st.markdown(hide_nav_style, unsafe_allow_html=True)

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Sidebar navigation
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #f0f4fa;
    }
    </style>
    """,
    unsafe_allow_html=True
)

sidebar_option = st.sidebar.selectbox(
    "Select Action",
    ("Add New Course", "Show Courses")
)

# Logout button in sidebar
if st.sidebar.button("Logout"):
    for key in ["logged_in", "user_role", "admin_id", "admin_code"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("You have been logged out.")
    st.rerun()

# Redirect to login if not logged in
if not st.session_state.get("logged_in", False):
    st.info("Please log in to continue.")
    st.switch_page("Dashboard.py")

# Database connection
conn = get_connection()
cursor = conn.cursor()

if sidebar_option == "Add New Course":
    st.header("Add New Course")
    # Fetch the admin_code for the current admin_id from session
    admin_id = st.session_state.get("admin_id", "N/A")
    cursor.execute("SELECT admin_code FROM admin WHERE admin_id = %s", (admin_id,))
    row = cursor.fetchone()
    admin_code = row[0] if row else "N/A"

    with st.form("add_course_form"):
        st.text_input("Admin Code", value=admin_code, disabled=True)
        course_id = st.text_input("Course ID")
        course_name = st.text_input("Course Name")
        st.info("Enter the YouTube Video ID (e.g., dQw4w9WgXcQ)")
        yt_link = st.text_input("YouTube Video ID")
        submit = st.form_submit_button("Add Course")
    if submit:
        cursor.execute(
            "INSERT INTO courses (course_id, course_name, admin_code, yt_link) VALUES (%s, %s, %s, %s)",
            (course_id, course_name, admin_code, yt_link)
        )
        conn.commit()
        st.success(f"Course '{course_name}' added successfully!")

elif sidebar_option == "Show Courses":
    st.header("All Courses")
    cursor.execute("SELECT course_id, course_name, admin_code, yt_link FROM courses")
    courses = cursor.fetchall()
    if courses:
        import pandas as pd
        table_data = []
        for idx, row in enumerate(courses, start=1):
            table_data.append([idx] + list(row))
        headers = ["S.No.", "Course ID", "Course Name", "Admin Code", "YouTube Video ID"]
        df = pd.DataFrame(table_data, columns=headers)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No courses found.")