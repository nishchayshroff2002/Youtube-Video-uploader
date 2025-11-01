import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_otp(receiver_email):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    # Create a fresh message object each time
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Your OTP Code"

    # Generate OTP
    otp = str(random.randint(10000000, 99999999))

    # Email body
    body = f"Your one-time password (OTP) is: {otp}"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("OTP sent successfully!")
    except Exception as e:
        print("Error:", e)

    return otp
def send_approval_message(receiver_email,channel_name):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    # Create a fresh message object each time
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Request for uploading video to youtube channel: "+ channel_name
    verification_link = ""
    # Email body
    body = body = f"""
    <html>
      <body>
        <h2>Hi owner,</h2>
        <p>User {receiver_email} wants to upload a video to your channel {channel_name}. Please click on link below to check</p>
        <a href="{verification_link}">Verify Email</a>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("OTP sent successfully!")
    except Exception as e:
        print("Error:", e)

    return otp
