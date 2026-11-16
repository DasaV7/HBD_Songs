import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st


def send_email_notification(
        recipient_email,
        recipient_name,
        youtube_url
):

    try:

        sender_email = st.secrets["EMAIL_ADDRESS"]
        sender_password = st.secrets["EMAIL_PASSWORD"]

        message = MIMEMultipart()

        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = (
            "🎂 Your Birthday Video is Ready!"
        )

        body = f"""
Hello {recipient_name},

Your birthday video has been successfully created and uploaded.

Watch it here:

{youtube_url}

Thank you for using our Birthday Video Generator.

Best wishes,
Birthday Video Generator Team
"""

        message.attach(
            MIMEText(body, "plain")
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            sender_email,
            sender_password
        )

        server.send_message(message)

        server.quit()

        return True

    except Exception as e:

        print("Email Error:", e)

        return False
