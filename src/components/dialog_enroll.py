import streamlit as st

from src.database.db import enroll_student_to_subject
from src.database.config import supabase


@st.dialog("Enroll in Subject")
def enroll_dialog():

    st.write(
        "Enter the subject code provided by your teacher to enroll."
    )

    join_code = st.text_input(
        "Subject Code",
        placeholder="Eg. CS101"
    )

    if st.button(
        "Enroll now",
        type="primary",
        width="stretch"
    ):

        # ---------------------------------------------------------
        # VALIDATE CODE
        # ---------------------------------------------------------

        if not join_code or not join_code.strip():
            st.warning("Please enter a subject code.")
            return

        join_code = join_code.strip()

        # ---------------------------------------------------------
        # CHECK STUDENT LOGIN
        # ---------------------------------------------------------

        student_data = st.session_state.get("student_data")

        if not student_data:
            st.error("Please log in as a student first.")
            return

        student_id = student_data.get("student_id")

        if not student_id:
            st.error("Student information could not be found.")
            return

        # ---------------------------------------------------------
        # FIND SUBJECT
        # ---------------------------------------------------------

        try:
            response = (
                supabase
                .table("subjects")
                .select(
                    "subject_id, name, subject_code"
                )
                .ilike(
                    "subject_code",
                    join_code
                )
                .execute()
            )

        except Exception as e:
            st.error("Unable to find the subject.")
            st.caption(str(e))
            return

        if not response.data:
            st.error(
                f"Subject code '{join_code}' was not found."
            )
            return

        subject = response.data[0]

        subject_id = subject.get("subject_id")
        subject_name = subject.get(
            "name",
            "this subject"
        )

        # ---------------------------------------------------------
        # CHECK EXISTING ENROLLMENT
        # ---------------------------------------------------------

        try:
            check = (
                supabase
                .table("subject_students")
                .select("*")
                .eq("subject_id", subject_id)
                .eq("student_id", student_id)
                .execute()
            )

        except Exception as e:
            st.error(
                "Could not check your enrollment."
            )
            st.caption(str(e))
            return

        if check.data:
            st.warning(
                f"You are already enrolled in {subject_name}."
            )
            return

        # ---------------------------------------------------------
        # ENROLL STUDENT
        # ---------------------------------------------------------

        try:
            result = enroll_student_to_subject(
                student_id,
                subject_id
            )

            if result:
                st.success(
                    f"Successfully enrolled in {subject_name}!"
                )

                st.rerun()

            else:
                st.error(
                    "Enrollment could not be completed."
                )

        except Exception as e:
            st.error(
                "Could not enroll you in this subject."
            )
            st.caption(str(e))
