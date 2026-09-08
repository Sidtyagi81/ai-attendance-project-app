from src.database.config import supabase
import bcrypt


# =========================================================
# PASSWORD HELPERS
# =========================================================

def hash_pass(pwd):
    return bcrypt.hashpw(
        pwd.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def check_pass(pwd, hashed):
    return bcrypt.checkpw(
        pwd.encode("utf-8"),
        hashed.encode("utf-8")
    )


# =========================================================
# TEACHER
# =========================================================

def check_teacher_exists(username):

    response = (
        supabase
        .table("teachers")
        .select("username")
        .eq("username", username)
        .execute()
    )

    return bool(response.data)


def create_teacher(username, password, name):

    data = {
        "username": username,
        "password": hash_pass(password),
        "name": name,
    }

    response = (
        supabase
        .table("teachers")
        .insert(data)
        .execute()
    )

    return response.data or []


def teacher_login(username, password):

    response = (
        supabase
        .table("teachers")
        .select("*")
        .eq("username", username)
        .execute()
    )

    if not response.data:
        return None

    teacher = response.data[0]

    try:
        if check_pass(
            password,
            teacher["password"]
        ):
            return teacher
    except Exception:
        return None

    return None


# =========================================================
# STUDENTS
# =========================================================

def get_all_students():

    response = (
        supabase
        .table("students")
        .select("*")
        .execute()
    )

    return response.data or []


def create_student(
    new_name,
    face_embedding=None,
    voice_embedding=None
):

    data = {
        "name": new_name,
        "face_embedding": face_embedding,
        "voice_embedding": voice_embedding,
    }

    response = (
        supabase
        .table("students")
        .insert(data)
        .execute()
    )

    return response.data or []


# =========================================================
# SUBJECTS
# =========================================================

def create_subject(
    subject_code,
    name,
    section,
    teacher_id
):

    data = {
        "subject_code": str(subject_code).strip(),
        "name": str(name).strip(),
        "section": str(section).strip(),
        "teacher_id": teacher_id,
    }

    response = (
        supabase
        .table("subjects")
        .insert(data)
        .execute()
    )

    return response.data or []


def get_teacher_subjects(teacher_id):

    response = (
        supabase
        .table("subjects")
        .select(
            "*, "
            "subject_students(count), "
            "attendance_logs(timestamp)"
        )
        .eq(
            "teacher_id",
            teacher_id
        )
        .execute()
    )

    subjects = response.data or []

    for sub in subjects:

        # -------------------------------------------------
        # STUDENT COUNT
        # -------------------------------------------------

        subject_students = (
            sub.get("subject_students") or []
        )

        if subject_students:

            sub["total_students"] = int(
                subject_students[0].get(
                    "count",
                    0
                ) or 0
            )

        else:

            sub["total_students"] = 0

        # -------------------------------------------------
        # CLASS COUNT
        # -------------------------------------------------

        attendance = (
            sub.get("attendance_logs") or []
        )

        timestamps = set()

        for log in attendance:

            timestamp = log.get(
                "timestamp"
            )

            if timestamp:
                timestamps.add(
                    timestamp
                )

        sub["total_classes"] = len(
            timestamps
        )

        # -------------------------------------------------
        # REMOVE NESTED DATA
        # -------------------------------------------------

        sub.pop(
            "subject_students",
            None
        )

        sub.pop(
            "attendance_logs",
            None
        )

    return subjects


# =========================================================
# ENROLLMENT
# =========================================================

def enroll_student_to_subject(
    student_id,
    subject_id
):
    """
    Enroll a student into a subject.

    This function:
      1. Validates IDs.
      2. Checks whether enrollment already exists.
      3. Inserts the enrollment.
      4. Verifies that Supabase actually created the row.
      5. Raises an error instead of silently failing.
    """

    # -----------------------------------------------------
    # VALIDATE
    # -----------------------------------------------------

    if student_id is None:
        raise ValueError(
            "Enrollment failed: student_id is missing."
        )

    if subject_id is None:
        raise ValueError(
            "Enrollment failed: subject_id is missing."
        )

    # -----------------------------------------------------
    # NORMALIZE INTEGER IDs
    # -----------------------------------------------------

    try:
        student_id = int(student_id)
        subject_id = int(subject_id)

    except (ValueError, TypeError):

        raise ValueError(
            "Enrollment failed: student_id and "
            "subject_id must be valid IDs."
        )

    # -----------------------------------------------------
    # VERIFY STUDENT EXISTS
    # -----------------------------------------------------

    student_check = (
        supabase
        .table("students")
        .select("student_id")
        .eq(
            "student_id",
            student_id
        )
        .execute()
    )

    if not student_check.data:

        raise ValueError(
            f"Enrollment failed: student "
            f"{student_id} does not exist."
        )

    # -----------------------------------------------------
    # VERIFY SUBJECT EXISTS
    # -----------------------------------------------------

    subject_check = (
        supabase
        .table("subjects")
        .select("subject_id, name, subject_code")
        .eq(
            "subject_id",
            subject_id
        )
        .execute()
    )

    if not subject_check.data:

        raise ValueError(
            f"Enrollment failed: subject "
            f"{subject_id} does not exist."
        )

    # -----------------------------------------------------
    # CHECK EXISTING ENROLLMENT
    # -----------------------------------------------------

    existing = (
        supabase
        .table("subject_students")
        .select(
            "student_id, subject_id"
        )
        .eq(
            "student_id",
            student_id
        )
        .eq(
            "subject_id",
            subject_id
        )
        .execute()
    )

    if existing.data:

        # Already enrolled.
        return existing.data

    # -----------------------------------------------------
    # INSERT
    # -----------------------------------------------------

    enrollment_data = {
        "student_id": student_id,
        "subject_id": subject_id,
    }

    try:

        response = (
            supabase
            .table("subject_students")
            .insert(enrollment_data)
            .execute()
        )

    except Exception as e:

        raise RuntimeError(
            "Supabase rejected the enrollment: "
            f"{e}"
        ) from e

    # -----------------------------------------------------
    # CHECK INSERT RESPONSE
    # -----------------------------------------------------

    if not response.data:

        raise RuntimeError(
            "Enrollment insert returned no data."
        )

    # -----------------------------------------------------
    # VERIFY DATABASE
    # -----------------------------------------------------

    verify = (
        supabase
        .table("subject_students")
        .select(
            "student_id, subject_id"
        )
        .eq(
            "student_id",
            student_id
        )
        .eq(
            "subject_id",
            subject_id
        )
        .execute()
    )

    if not verify.data:

        raise RuntimeError(
            "Enrollment insert appeared successful, "
            "but the enrollment could not be found "
            "in subject_students."
        )

    return verify.data


def unenroll_student_to_subject(
    student_id,
    subject_id
):

    response = (
        supabase
        .table("subject_students")
        .delete()
        .eq(
            "student_id",
            student_id
        )
        .eq(
            "subject_id",
            subject_id
        )
        .execute()
    )

    return response.data or []


def get_student_subjects(student_id):

    response = (
        supabase
        .table("subject_students")
        .select(
            "*, subjects(*)"
        )
        .eq(
            "student_id",
            student_id
        )
        .execute()
    )

    return response.data or []


# =========================================================
# ATTENDANCE
# =========================================================

def get_student_attendance(student_id):

    response = (
        supabase
        .table("attendance_logs")
        .select(
            "*, subjects(*)"
        )
        .eq(
            "student_id",
            student_id
        )
        .execute()
    )

    return response.data or []


def create_attendance(logs):

    if not logs:
        return []

    response = (
        supabase
        .table("attendance_logs")
        .insert(logs)
        .execute()
    )

    return response.data or []


def get_attendance_for_teacher(
    teacher_id
):

    response = (
        supabase
        .table("attendance_logs")
        .select(
            "*, subjects!inner(*)"
        )
        .eq(
            "subjects.teacher_id",
            teacher_id
        )
        .execute()
    )

    return response.data or []
