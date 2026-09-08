import streamlit as st


def subject_card(name, code, section, stats=None, footer_callback=None):

    html = f"""
    <div style="
        background: white;
        padding: 25px;
        border-radius: 20px;
        border: 1px solid #111827;
        margin-bottom: 20px;
        color: #1e293b;
    ">

        <h3 style="
            margin: 0;
            color: #1e293b;
            font-size: 1.5rem;
            font-weight: 700;
        ">
            {name}
        </h3>

        <p style="
            color: #475569;
            margin: 10px 0;
            font-size: 1rem;
        ">
            Code :
            <span style="
                background: #E0E3FF;
                color: #5865F2;
                padding: 3px 9px;
                border-radius: 6px;
                font-weight: 600;
            ">
                {code}
            </span>

            <span style="color:#64748b;">
                &nbsp;|&nbsp; Section : {section}
            </span>
        </p>
    """

    if stats:

        html += """
        <div style="
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 12px;
        ">
        """

        for icon, label, value in stats:

            html += f"""
            <div style="
                background: #FCE7F3;
                color: #1e293b;
                padding: 8px 14px;
                border-radius: 12px;
                font-size: 0.95rem;
                font-weight: 600;
                border: 1px solid #F9A8D4;
                display: inline-flex;
                align-items: center;
                gap: 5px;
            ">

                <span style="
                    font-size: 1rem;
                ">
                    {icon}
                </span>

                <span style="
                    color: #1e293b;
                    font-weight: 700;
                ">
                    {value}
                </span>

                <span style="
                    color: #334155;
                    font-weight: 600;
                ">
                    {label}
                </span>

            </div>
            """

        html += "</div>"

    html += "</div>"

    st.markdown(
        html,
        unsafe_allow_html=True
    )

    if footer_callback:
        footer_callback()
