import streamlit as st


def subject_card(name, code, section, stats=None, footer_callback=None):

    stats_html = ""

    if stats:
        for icon, label, value in stats:
            stats_html += f"""
            <div style="
                background-color: #fce7f3;
                border: 1px solid #f9a8d4;
                border-radius: 12px;
                padding: 8px 14px;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                margin-right: 8px;
                margin-top: 8px;
                font-size: 15px;
                font-weight: 600;
                color: #1e293b;
            ">
                <span>{icon}</span>
                <span style="color: #1e293b; font-weight: 700;">
                    {value}
                </span>
                <span style="color: #334155; font-weight: 600;">
                    {label}
                </span>
            </div>
            """

    html = f"""
    <div style="
        background-color: white;
        border: 1px solid #111827;
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 15px;
        width: 100%;
        box-sizing: border-box;
    ">

        <div style="
            color: #1e293b;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 12px;
        ">
            {name}
        </div>

        <div style="
            color: #475569;
            font-size: 17px;
            margin-bottom: 10px;
        ">
            Code :

            <span style="
                background-color: #e0e3ff;
                color: #5865f2;
                padding: 4px 9px;
                border-radius: 6px;
                font-weight: 600;
            ">
                {code}
            </span>

            <span style="color: #64748b;">
                &nbsp; | &nbsp; Section : {section}
            </span>
        </div>

        <div style="
            display: flex;
            flex-wrap: wrap;
            align-items: center;
        ">
            {stats_html}
        </div>

    </div>
    """

    # IMPORTANT:
    # Use st.html(), NOT st.markdown().
    st.html(html)

    if footer_callback:
        footer_callback()
