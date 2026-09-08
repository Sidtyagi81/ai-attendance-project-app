import time
import streamlit as st

from src.database.db import enroll_student_to_subject
from src.database.config import supabase


@st.dialog("Quick Enrollment")
def auto_enroll_dialog(subject_code):
    # ---------------------------------------------------------
    # SAFELY GET STUDENT DATA
    # ---------------------------------------------------------
    student_data = st.session_state.get("student_data")

    if not student_data:
        st.warning("Please log in as a student to join this class.")

        if st.button("Close", type="primary", width="stretch"):
            st.query_params.clear()
            st.rerun()

        return

    # ---------------------------------------------------------
    # SAFELY GET STUDENT ID
    # ---------------------------------------------------------
    student_id = student_data.get("student_id")

    if not student_id:
        st.error("Student information could not be found.")

        if st.button("Close", type="primary", width="stretch"):
            st.query_params.clear()
            st.rerun()

        return

    # ---------------------------------------------------------
    # CLEAN SUBJECT CODE
    # ---------------------------------------------------------
    subject_code = str(subject_code).strip()

    if not subject_code:
        st.error("Invalid class code.")

        if st.button("Close", type="primary", width="stretch"):
            st.query_params.clear()
            st.rerun()

        return

    # ---------------------------------------------------------
    # FIND SUBJECT
    # ---------------------------------------------------------
    try:
        response = (
            supabase
            .table("subjects")
            .select("subject_id, name")
            .eq("subject_code", subject_code)
            .execute()
        )

        subject_data = response.data

    except Exception as e:
        st.error("Unable to find the class right now.")
        st.caption(f"Error: {e}")

        if st.button("Close", type="primary", width="stretch"):
            st.query_params.clear()
            st.rerun()

        return

    # ---------------------------------------------------------
    # SUBJECT DOES NOT EXIST
    # ---------------------------------------------------------
    if not subject_data:
        st.error("Subject Code not found!")

        if st.button("Close", type="primary", width="stretch"):
            st.query_params.clear()
            st.rerun()

        return

    subject = subject_data[0]

    subject_id = subject.get("subject_id")
    subject_name = subject.get("name", "this class")

    # ---------------------------------------------------------
    # CHECK WHETHER STUDENT IS ALREADY ENROLLED
    # ---------------------------------------------------------
    try:
        check_response = (
            supabase
            .table("subject_students")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("student_id", student_id)
            .execute()
        )

        already_enrolled = bool(check_response.data)

    except Exception as e:
        st.error("Unable to check your enrollment.")
        st.caption(f"Error: {e}")

        if st.button("Close", type="primary", width="stretch"):
            st.query_params.clear()
            st.rerun()

        return

    # ---------------------------------------------------------
    # ALREADY ENROLLED
    # ---------------------------------------------------------
    if already_enrolled:
        st.info("You're already enrolled in this class!")

        if st.button("Got it!", type="primary", width="stretch"):
            st.query_params.clear()
            st.rerun()

        return

    # ---------------------------------------------------------
    # ENROLLMENT CONFIRMATION
    # ---------------------------------------------------------
    st.markdown(
        f"Would you like to enroll in **{subject_name}**?"
    )

    col1, col2 = st.columns(2)

    # ---------------------------------------------------------
    # NO
    # ---------------------------------------------------------
    with col1:
        if st.button(
            "No thanks",
            width="stretch"
        ):
            st.query_params.clear()
            st.rerun()

    # ---------------------------------------------------------
    # YES
    # ---------------------------------------------------------
    with col2:
        if st.button(
            "Yes, enroll now!",
            type="primary",
            width="stretch"
        ):
            try:
                result = enroll_student_to_subject(
                    student_id,
                    subject_id
                )

                st.success("Joined successfully!")

                # Give the success message a moment to display.
                time.sleep(1)

                # Remove join-code from URL.
                st.query_params.clear()

                st.rerun()

            except Exception as e:
                st.error("Could not join the class.")
                st.caption(f"Error: {e}")
