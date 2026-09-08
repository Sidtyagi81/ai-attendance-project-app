import streamlit as st

from src.database.db import enroll_student_to_subject
from src.database.config import supabase


@st.dialog("Quick Enrollment")
def auto_enroll_dialog(subject_code):

    # =========================================================
    # GET LOGGED-IN STUDENT
    # =========================================================

    student_data = st.session_state.get("student_data")

    if not student_data:
        st.warning(
            "Please log in as a student to join this class."
        )

        if st.button(
            "Close",
            type="primary",
            width="stretch"
        ):
            st.query_params.clear()
            st.rerun()

        return

    student_id = student_data.get("student_id")

    if not student_id:
        st.error(
            "Student information could not be found."
        )

        if st.button(
            "Close",
            type="primary",
            width="stretch"
        ):
            st.query_params.clear()
            st.rerun()

        return

    # =========================================================
    # CLEAN SUBJECT CODE
    # =========================================================

    subject_code = str(subject_code).strip()

    if not subject_code:
        st.error("Invalid subject code.")
        return

    # =========================================================
    # FIND SUBJECT
    # =========================================================

    try:
        response = (
            supabase
            .table("subjects")
            .select(
                "subject_id, name, subject_code"
            )
            .ilike(
                "subject_code",
                subject_code
            )
            .execute()
        )

    except Exception as e:
        st.error(
            "Unable to find the class."
        )
        st.caption(str(e))
        return

    if not response.data:
        st.error(
            f"Subject code '{subject_code}' was not found."
        )

        if st.button(
            "Close",
            type="primary",
            width="stretch"
        ):
            st.query_params.clear()
            st.rerun()

        return

    subject = response.data[0]

    subject_id = subject.get("subject_id")
    subject_name = subject.get(
        "name",
        "this class"
    )

    # =========================================================
    # CHECK IF ALREADY ENROLLED
    # =========================================================

    try:
        check = (
            supabase
            .table("subject_students")
            .select("*")
            .eq(
                "subject_id",
                subject_id
            )
            .eq(
                "student_id",
                student_id
            )
            .execute()
        )

    except Exception as e:
        st.error(
            "Unable to check your enrollment."
        )
        st.caption(str(e))
        return

    if check.data:

        st.info(
            f"You're already enrolled in {subject_name}!"
        )

        if st.button(
            "Got it!",
            type="primary",
            width="stretch"
        ):
            st.query_params.clear()
            st.rerun()

        return

    # =========================================================
    # ASK STUDENT TO JOIN
    # =========================================================

    st.markdown(
        f"Would you like to enroll in **{subject_name}**?"
    )

    col1, col2 = st.columns(2)

    # =========================================================
    # NO
    # =========================================================

    with col1:

        if st.button(
            "No thanks",
            width="stretch"
        ):
            st.query_params.clear()
            st.rerun()

    # =========================================================
    # YES
    # =========================================================

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

                if result:

                    st.success(
                        "Joined successfully!"
                    )

                    # Remove the join code from URL
                    st.query_params.clear()

                    st.rerun()

                else:
                    st.error(
                        "Enrollment could not be completed."
                    )

            except Exception as e:

                st.error(
                    "Could not join the class."
                )

                st.caption(str(e))
