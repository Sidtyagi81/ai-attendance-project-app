import streamlit as st
import segno
import io


@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    # ---------------------------------------------------------
    # YOUR ACTUAL DEPLOYED STREAMLIT APP
    # ---------------------------------------------------------
    app_domain = "ai-attendance-project-app-qbtawmk2tsonc5xhjnlbwd.streamlit.app"

    # Make sure there is no accidental whitespace
    subject_code = str(subject_code).strip()

    # Correct student join URL
    join_url = f"https://{app_domain}/?join-code={subject_code}"

    st.header("Scan to Join")

    # ---------------------------------------------------------
    # GENERATE QR CODE USING THE SAME JOIN URL
    # ---------------------------------------------------------
    qr = segno.make(join_url)

    out = io.BytesIO()

    qr.save(
        out,
        kind="png",
        scale=10,
        border=1
    )

    # ---------------------------------------------------------
    # DISPLAY LINK + QR
    # ---------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Copy Link")

        # Full clickable/shareable URL
        st.code(
            join_url,
            language="text"
        )

        # Class code
        st.code(
            subject_code,
            language="text"
        )

        st.info(
            "Copy this link to share on WhatsApp or Email"
        )

    with col2:
        st.markdown("### Scan to Join")

        st.image(
            out.getvalue(),
            caption="QR CODE for class joining"
        )
