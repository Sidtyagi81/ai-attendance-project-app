import streamlit as st

from src.ui.base_layout import (
    style_background_dashboard,
    style_base_layout,
)

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card

from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subjects,
    get_attendance_for_teacher,
)

from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog

from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_attendance_results import (
    attendance_result_dialog,
)

import numpy as np
from datetime import datetime
import pandas as pd

from src.database.config import supabase

from src.components.dialog_voice_attendance import (
    voice_attendance_dialog,
)


# ============================================================
# TEACHER SCREEN
# ============================================================

def teacher_screen():

    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()

    elif (
        "teacher_login_type" not in st.session_state
        or st.session_state.teacher_login_type == "login"
    ):
        teacher_screen_login()

    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


# ============================================================
# TEACHER DASHBOARD
# ============================================================

def teacher_dashboard():

    teacher_data = st.session_state.teacher_data

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge",
    )

    with c1:
        header_dashboard()

    with c2:

        st.subheader(
            f"Welcome, {teacher_data['name']}"
        )

        if st.button(
            "Logout",
            type="secondary",
            key="teacher_logout_btn",
            shortcut="control+backspace",
        ):

            st.session_state["is_logged_in"] = False

            if "teacher_data" in st.session_state:
                del st.session_state["teacher_data"]

            st.session_state["user_role"] = None
            st.session_state["login_type"] = None

            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"

    tab1, tab2, tab3 = st.columns(3)

    # ========================================================
    # TAKE ATTENDANCE TAB
    # ========================================================

    with tab1:

        type1 = (
            "primary"
            if st.session_state.current_teacher_tab
            == "take_attendance"
            else "tertiary"
        )

        if st.button(
            "Take Attendance",
            type=type1,
            width="stretch",
            icon=":material/ar_on_you:",
        ):

            st.session_state.current_teacher_tab = (
                "take_attendance"
            )

            st.rerun()

    # ========================================================
    # MANAGE SUBJECTS TAB
    # ========================================================

    with tab2:

        type2 = (
            "primary"
            if st.session_state.current_teacher_tab
            == "manage_subjects"
            else "tertiary"
        )

        if st.button(
            "Manage Subjects",
            type=type2,
            width="stretch",
            icon=":material/book_ribbon:",
        ):

            st.session_state.current_teacher_tab = (
                "manage_subjects"
            )

            st.rerun()

    # ========================================================
    # ATTENDANCE RECORDS TAB
    # ========================================================

    with tab3:

        type3 = (
            "primary"
            if st.session_state.current_teacher_tab
            == "attendance_records"
            else "tertiary"
        )

        if st.button(
            "Attendance Records",
            type=type3,
            width="stretch",
            icon=":material/cards_stack:",
        ):

            st.session_state.current_teacher_tab = (
                "attendance_records"
            )

            st.rerun()

    st.divider()

    # ========================================================
    # DISPLAY SELECTED TAB
    # ========================================================

    if (
        st.session_state.current_teacher_tab
        == "take_attendance"
    ):
        teacher_tab_take_attendance()

    elif (
        st.session_state.current_teacher_tab
        == "manage_subjects"
    ):
        teacher_tab_manage_subjects()

    elif (
        st.session_state.current_teacher_tab
        == "attendance_records"
    ):
        teacher_tab_attendance_records()

    footer_dashboard()


# ============================================================
# TAKE ATTENDANCE
# ============================================================

def teacher_tab_take_attendance():

    teacher_id = st.session_state.teacher_data["teacher_id"]

    st.header("Take AI Attendance")

    # --------------------------------------------------------
    # INITIALIZE PHOTO STORAGE
    # --------------------------------------------------------

    if "attendance_images" not in st.session_state:
        st.session_state.attendance_images = []

    # --------------------------------------------------------
    # GET TEACHER SUBJECTS
    # --------------------------------------------------------

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:

        st.warning(
            "You haven't created any subjects yet! "
            "Please create one to begin!"
        )

        return

    # --------------------------------------------------------
    # SUBJECT DROPDOWN
    # --------------------------------------------------------

    subject_options = {
        f"{s['name']} - {s['subject_code']}":
            s["subject_id"]
        for s in subjects
    }

    col1, col2 = st.columns(
        [3, 1],
        vertical_alignment="bottom",
    )

    with col1:

        selected_subject_label = st.selectbox(
            "Select Subject",
            options=list(subject_options.keys()),
        )

    with col2:

        if st.button(
            "Add Photos",
            type="primary",
            icon=":material/photo_prints:",
            width="stretch",
        ):

            add_photos_dialog()

    selected_subject_id = subject_options[
        selected_subject_label
    ]

    st.divider()

    # --------------------------------------------------------
    # DISPLAY ADDED PHOTOS
    # --------------------------------------------------------

    if st.session_state.attendance_images:

        st.header("Added Photos")

        gallery_cols = st.columns(4)

        for idx, img in enumerate(
            st.session_state.attendance_images
        ):

            with gallery_cols[idx % 4]:

                st.image(
                    img,
                    width="stretch",
                    caption=f"Photo {idx + 1}",
                )

    has_photos = bool(
        st.session_state.attendance_images
    )

    c1, c2, c3 = st.columns(3)

    # ========================================================
    # CLEAR PHOTOS
    # ========================================================

    with c1:

        if st.button(
            "Clear all photos",
            width="stretch",
            type="tertiary",
            icon=":material/delete:",
            disabled=not has_photos,
        ):

            st.session_state.attendance_images = []

            st.rerun()

    # ========================================================
    # RUN FACE ANALYSIS
    # ========================================================

    with c2:

        if st.button(
            "Run Face Analysis",
            width="stretch",
            type="secondary",
            icon=":material/analytics:",
            disabled=not has_photos,
        ):

            with st.spinner(
                "Deep scanning classroom photos..."
            ):

                # ------------------------------------------------
                # DETECT STUDENTS FROM PHOTOS
                # ------------------------------------------------

                all_detected_ids = {}

                for idx, img in enumerate(
                    st.session_state.attendance_images
                ):

                    img_np = np.array(
                        img.convert("RGB")
                    )

                    detected, _, _ = predict_attendance(
                        img_np
                    )

                    if detected:

                        for sid in detected.keys():

                            try:

                                student_id = int(sid)

                                all_detected_ids.setdefault(
                                    student_id,
                                    [],
                                ).append(
                                    f"Photo {idx + 1}"
                                )

                            except (
                                ValueError,
                                TypeError,
                            ):

                                continue

                # ------------------------------------------------
                # GET ENROLLED STUDENTS
                # ------------------------------------------------

                enrolled_res = (
                    supabase
                    .table("subject_students")
                    .select("*, students(*)")
                    .eq(
                        "subject_id",
                        selected_subject_id,
                    )
                    .execute()
                )

                enrolled_students = (
                    enrolled_res.data or []
                )

                # ------------------------------------------------
                # NO STUDENTS
                # ------------------------------------------------

                if not enrolled_students:

                    st.warning(
                        "No students enrolled in this course"
                    )

                    return

                # ------------------------------------------------
                # INITIALIZE RESULT LISTS
                # ------------------------------------------------

                results = []
                attendance_to_log = []

                current_timestamp = (
                    datetime.now().strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
                )

                # ------------------------------------------------
                # PROCESS EVERY ENROLLED STUDENT
                # ------------------------------------------------

                for node in enrolled_students:

                    student = node.get("students")

                    if not student:
                        continue

                    # Supabase can return a nested object
                    # depending on the relationship.
                    if isinstance(student, list):

                        if not student:
                            continue

                        student = student[0]

                    student_id = student.get(
                        "student_id"
                    )

                    if student_id is None:
                        continue

                    try:
                        student_id_int = int(student_id)

                    except (
                        ValueError,
                        TypeError,
                    ):
                        continue

                    sources = all_detected_ids.get(
                        student_id_int,
                        [],
                    )

                    is_present = bool(sources)

                    # ------------------------------------------------
                    # RESULT FOR UI
                    # ------------------------------------------------

                    results.append(
                        {
                            "Name": student.get(
                                "name",
                                "Unknown",
                            ),
                            "ID": student_id,
                            "Source": (
                                ", ".join(sources)
                                if is_present
                                else "-"
                            ),
                            "Status": (
                                "✅ Present"
                                if is_present
                                else "❌ Absent"
                            ),
                        }
                    )

                    # ------------------------------------------------
                    # ATTENDANCE LOG
                    # ------------------------------------------------

                    attendance_to_log.append(
                        {
                            "student_id": student_id,
                            "subject_id": selected_subject_id,
                            "timestamp": current_timestamp,
                            "is_present": is_present,
                        }
                    )

                # ------------------------------------------------
                # SAFETY CHECK
                # ------------------------------------------------

                if not results:

                    st.warning(
                        "No valid enrolled student records "
                        "were found."
                    )

                    return

                # ------------------------------------------------
                # SHOW RESULTS
                # ------------------------------------------------

                attendance_result_dialog(
                    pd.DataFrame(results),
                    attendance_to_log,
                )

    # ========================================================
    # VOICE ATTENDANCE
    # ========================================================

    with c3:

        if st.button(
            "Use Voice Attendance",
            type="primary",
            width="stretch",
            icon=":material/mic:",
        ):

            voice_attendance_dialog(
                selected_subject_id
            )


# ============================================================
# MANAGE SUBJECTS
# ============================================================

def teacher_tab_manage_subjects():

    teacher_id = st.session_state.teacher_data[
        "teacher_id"
    ]

    col1, col2 = st.columns(2)

    with col1:

        st.header(
            "Manage Subjects",
            width="stretch",
        )

    with col2:

        if st.button(
            "Create New Subject",
            width="stretch",
            type="primary",
        ):

            create_subject_dialog(
                teacher_id
            )

    # --------------------------------------------------------
    # GET SUBJECTS
    # --------------------------------------------------------

    subjects = get_teacher_subjects(
        teacher_id
    )

    # --------------------------------------------------------
    # SHOW SUBJECTS
    # --------------------------------------------------------

    if subjects:

        for sub in subjects:

            stats = [
                (
                    "🫂",
                    "Students",
                    sub.get(
                        "total_students",
                        0,
                    ),
                ),
                (
                    "🕰️",
                    "Classes",
                    sub.get(
                        "total_classes",
                        0,
                    ),
                ),
            ]

            # ------------------------------------------------
            # SHARE BUTTON
            # ------------------------------------------------

            def share_btn(
                subject_name=sub["name"],
                subject_code=sub["subject_code"],
            ):

                if st.button(
                    f"Share Code: {subject_name}",
                    key=f"share_{subject_code}",
                    icon=":material/share:",
                    width="stretch",
                ):

                    share_subject_dialog(
                        subject_name,
                        subject_code,
                    )

                st.space()

            # ------------------------------------------------
            # SUBJECT CARD
            # ------------------------------------------------

            subject_card(
                name=sub["name"],
                code=sub["subject_code"],
                section=sub.get(
                    "section",
                    "",
                ),
                stats=stats,
                footer_callback=share_btn,
            )

    else:

        st.info(
            "NO SUBJECTS FOUND. CREATE ONE ABOVE"
        )


# ============================================================
# ATTENDANCE RECORDS
# ============================================================

def teacher_tab_attendance_records():

    st.header("Attendance Records")

    teacher_id = st.session_state.teacher_data[
        "teacher_id"
    ]

    records = get_attendance_for_teacher(
        teacher_id
    )

    if not records:
        st.info("No attendance records yet.")
        return

    data = []

    for r in records:

        ts = r.get("timestamp")

        # ----------------------------------------------------
        # FORMAT TIMESTAMP
        # ----------------------------------------------------

        if ts:

            try:

                formatted_time = (
                    datetime.fromisoformat(
                        ts.replace(
                            "Z",
                            "+00:00",
                        )
                    ).strftime(
                        "%Y-%m-%d %I:%M %p"
                    )
                )

            except Exception:

                formatted_time = ts

            ts_group = ts.split(".")[0]

        else:

            formatted_time = "N/A"
            ts_group = None

        # ----------------------------------------------------
        # SUBJECT SAFETY
        # ----------------------------------------------------

        subject = r.get("subjects") or {}

        data.append(
            {
                "ts_group": ts_group,
                "Time": formatted_time,
                "Subject": subject.get(
                    "name",
                    "Unknown",
                ),
                "Subject Code": subject.get(
                    "subject_code",
                    "N/A",
                ),
                "is_present": bool(
                    r.get(
                        "is_present",
                        False,
                    )
                ),
            }
        )

    if not data:
        st.info("No attendance records yet.")
        return

    df = pd.DataFrame(data)

    # --------------------------------------------------------
    # GROUP ATTENDANCE
    # --------------------------------------------------------

    summary = (
        df.groupby(
            [
                "ts_group",
                "Time",
                "Subject",
                "Subject Code",
            ],
            dropna=False,
        )
        .agg(
            Present_Count=(
                "is_present",
                "sum",
            ),
            Total_Count=(
                "is_present",
                "count",
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # ATTENDANCE STATISTICS
    # --------------------------------------------------------

    summary["Attendance Stats"] = (
        "✅ "
        + summary[
            "Present_Count"
        ].astype(str)
        + " / "
        + summary[
            "Total_Count"
        ].astype(str)
        + " Students"
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    display_df = (
        summary
        .sort_values(
            by="ts_group",
            ascending=False,
            na_position="last",
        )
        [
            [
                "Time",
                "Subject",
                "Subject Code",
                "Attendance Stats",
            ]
        ]
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# TEACHER LOGIN
# ============================================================

def login_teacher(
    username,
    password,
):

    if not username or not password:
        return False

    teacher = teacher_login(
        username,
        password,
    )

    if teacher:

        st.session_state.user_role = (
            "teacher"
        )

        st.session_state.teacher_data = (
            teacher
        )

        st.session_state.is_logged_in = True
        st.session_state.login_type = "teacher"

        return True

    return False


# ============================================================
# TEACHER LOGIN SCREEN
# ============================================================

def teacher_screen_login():

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge",
    )

    with c1:

        header_dashboard()

    with c2:

        if st.button(
            "Go back to Home",
            type="secondary",
            key="teacher_login_back_btn",
            shortcut="control+backspace",
        ):

            st.session_state[
                "login_type"
            ] = None

            st.rerun()

    st.header(
        "Login using password",
        text_alignment="center",
    )

    st.space()
    st.space()

    teacher_username = st.text_input(
        "Enter username",
        placeholder="ananyaroy",
    )

    teacher_pass = st.text_input(
        "Enter password",
        type="password",
        placeholder="Enter password",
    )

    st.divider()

    btnc1, btnc2 = st.columns(2)

    # ========================================================
    # LOGIN
    # ========================================================

    with btnc1:

        if st.button(
            "Login",
            icon=":material/passkey:",
            shortcut="control+enter",
            width="stretch",
        ):

            if login_teacher(
                teacher_username,
                teacher_pass,
            ):

                st.toast(
                    "Welcome back!",
                    icon="👋",
                )

                import time

                time.sleep(1)

                st.rerun()

            else:

                st.error(
                    "Invalid username and password combo"
                )

    # ========================================================
    # REGISTER
    # ========================================================

    with btnc2:

        if st.button(
            "Register Instead",
            type="primary",
            icon=":material/passkey:",
            width="stretch",
        ):

            st.session_state.teacher_login_type = (
                "register"
            )

            st.rerun()

    footer_dashboard()


# ============================================================
# REGISTER TEACHER
# ============================================================

def register_teacher(
    teacher_username,
    teacher_name,
    teacher_pass,
    teacher_pass_confirm,
):

    if (
        not teacher_username
        or not teacher_name
        or not teacher_pass
    ):

        return (
            False,
            "All fields are required!",
        )

    if check_teacher_exists(
        teacher_username
    ):

        return (
            False,
            "Username already taken",
        )

    if teacher_pass != teacher_pass_confirm:

        return (
            False,
            "Password doesn't match",
        )

    try:

        created = create_teacher(
            teacher_username,
            teacher_pass,
            teacher_name,
        )

        if not created:

            return (
                False,
                "Teacher account could not be created.",
            )

        return (
            True,
            "Successfully Created! Login Now",
        )

    except Exception:

        return (
            False,
            "Unexpected Error!",
        )


# ============================================================
# TEACHER REGISTER SCREEN
# ============================================================

def teacher_screen_register():

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge",
    )

    with c1:

        header_dashboard()

    with c2:

        if st.button(
            "Go back to Home",
            type="secondary",
            key="teacher_register_back_btn",
            shortcut="control+backspace",
        ):

            st.session_state[
                "login_type"
            ] = None

            st.rerun()

    st.header(
        "Register your teacher profile"
    )

    st.space()
    st.space()

    teacher_username = st.text_input(
        "Enter username",
        placeholder="ananyaroy",
    )

    teacher_name = st.text_input(
        "Enter name",
        placeholder="Ananya Roy",
    )

    teacher_pass = st.text_input(
        "Enter password",
        type="password",
        placeholder="Enter password",
    )

    teacher_pass_confirm = st.text_input(
        "Confirm your password",
        type="password",
        placeholder="Enter password",
    )

    st.divider()

    btnc1, btnc2 = st.columns(2)

    # ========================================================
    # REGISTER
    # ========================================================

    with btnc1:

        if st.button(
            "Register now",
            icon=":material/passkey:",
            shortcut="control+enter",
            width="stretch",
        ):

            success, message = register_teacher(
                teacher_username,
                teacher_name,
                teacher_pass,
                teacher_pass_confirm,
            )

            if success:

                st.success(message)

                import time

                time.sleep(2)

                st.session_state.teacher_login_type = (
                    "login"
                )

                st.rerun()

            else:

                st.error(message)

    # ========================================================
    # LOGIN INSTEAD
    # ========================================================

    with btnc2:

        if st.button(
            "Login Instead",
            type="primary",
            icon=":material/passkey:",
            width="stretch",
        ):

            st.session_state.teacher_login_type = (
                "login"
            )

            st.rerun()

    footer_dashboard()
