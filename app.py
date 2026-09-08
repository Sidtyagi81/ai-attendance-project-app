import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen
from src.components.dialog_auto_enroll import auto_enroll_dialog


def main():
    st.set_page_config(
        page_title="SnapClass - Making Attendance faster using AI",
        page_icon="https://i.ibb.co/YTYGn5qV/logo.png",
        layout="wide"
    )

    if "login_type" not in st.session_state:
        st.session_state["login_type"] = None

    if "is_logged_in" not in st.session_state:
        st.session_state["is_logged_in"] = False

    if "user_role" not in st.session_state:
        st.session_state["user_role"] = None

    join_code = st.query_params.get("join-code")

    if join_code:
        join_code = str(join_code).strip()

        if not join_code:
            join_code = None

    if join_code:
        if st.session_state["login_type"] != "student":
            st.session_state["login_type"] = "student"
            st.rerun()

        student_screen()
        
        if (
            st.session_state.get("is_logged_in") is True
            and st.session_state.get("user_role") == "student"
        ):
            auto_enroll_dialog(join_code)

        return

    login_type = st.session_state.get("login_type")

    if login_type == "teacher":
        teacher_screen()

    elif login_type == "student":
        student_screen()

    else:
        home_screen()

if __name__ == "__main__":
    main()
