import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sender_email = "shroffnishchay@gmail.com"
sender_password = "S1Q3T3#PE"
msg = MIMEMultipart()
msg["From"] = sender_email
def send_otp(receiver_email):
    msg["To"] = receiver_email
    
    # Generate OTP
    otp = str(random.randint(10000000,99999999 ))
    # Email content
    subject = "Your OTP Code"
    body = f"Your one-time password (OTP) is: {otp}"
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    # Send the email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("OTP sent successfully!")
    except Exception as e:
        print("Error:", e)
    return otp
