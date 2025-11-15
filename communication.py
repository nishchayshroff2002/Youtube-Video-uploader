import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for
import os

sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")

def send_otp(receiver_email):

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

def send_approval_message(receiver_email,channel_name,user_email):

    # Create a fresh message object each time
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Request for uploading video to youtube channel: "+ channel_name
    verification_link = url_for('check_approvals', _external=True)
    # Email body
    body = f"""
    <html>
      <body>
        <h2>Hi owner,</h2>
        <p>User {user_email} wants to upload a video to your channel {channel_name}. Please click on link below to check</p>
        <a href="{verification_link}">Verify Email</a>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("Approval mail sent successfully!")
    except Exception as e:
        print("Error:", e)

def send_disapproved_message(receiver_email,channel_name,owner_email,title,description,tags,category_id,privacy_status,video_file_name,video_extension,thumbnail_file_name,thumbnail_extension):

    # Create a fresh message object each time
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Disapproved request for uploading to channel: "+ channel_name
    body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Hi owner,</h2>
    <p>Owner <b>{owner_email}</b> has <b>disapproved</b> the upload of your video to the channel <b>{channel_name}</b>.</p>

    <p>The details of the video are as follows:</p>
     <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
      <tr style="background-color: #f2f2f2;">
        <th align="left">Field</th>
        <th align="left">Value</th>
      </tr>
      <tr>
        <td><b>Title</b></td>
        <td>{title}</td>
      </tr>
      <tr>
        <td><b>Description</b></td>
        <td>{description}</td>
      </tr>
      <tr>
        <td><b>Tags</b></td>
        <td>{", ".join(tags) if isinstance(tags, list) else tags}</td>
      </tr>
      <tr>
        <td><b>Category ID</b></td>
        <td>{category_id}</td>
      </tr>
      <tr>
        <td><b>Privacy Status</b></td>
        <td>{privacy_status}</td>
      </tr>
      <tr>
        <td><b>Video File</b></td>
        <td>{video_file_name}.{video_extension}</td>
      </tr>
      <tr>
        <td><b>Thumbnail File</b></td>
        <td>{thumbnail_file_name}.{thumbnail_extension}</td>
      </tr>
    </table>

    <p style="margin-top: 20px;">Please review the video details and take any necessary actions.</p>
  </body>
</html>
"""
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("Dispproved mail sent successfully!")
    except Exception as e:
        print("Error:", e)

def send_approved_message(receiver_email,channel_name,owner_email,title,description,tags,category_id,privacy_status,video_file_name,video_extension,thumbnail_file_name,thumbnail_extension,yt_video_url,yt_thumb_url):

    # Create a fresh message object each time
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Approved request for uploading to channel: "+ channel_name
    body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Hi owner,</h2>
    <p>Owner <b>{owner_email}</b> has <b>approved</b> the upload of your video to the channel <b>{channel_name}</b>.</p>

    <p>The details of the video are as follows:</p>

    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
      <tr style="background-color: #f2f2f2;">
        <th align="left">Field</th>
        <th align="left">Value</th>
      </tr>
      <tr>
        <td><b>Title</b></td>
        <td>{title}</td>
      </tr>
      <tr>
        <td><b>Description</b></td>
        <td>{description}</td>
      </tr>
      <tr>
        <td><b>Tags</b></td>
        <td>{", ".join(tags) if isinstance(tags, list) else tags}</td>
      </tr>
      <tr>
        <td><b>Category ID</b></td>
        <td>{category_id}</td>
      </tr>
      <tr>
        <td><b>Privacy Status</b></td>
        <td>{privacy_status}</td>
      </tr>
      <tr>
        <td><b>Video File</b></td>
        <td>{video_file_name}.{video_extension}</td>
      </tr>
      <tr>
        <td><b>Thumbnail File</b></td>
        <td>{thumbnail_file_name}.{thumbnail_extension}</td>
      </tr>

      <!-- New Row: Video Link -->
      <tr>
        <td><b>Video Link</b></td>
        <td><a href="{yt_video_url}" target="_blank" style="color: #1a73e8;">{yt_video_url}</a></td>
      </tr>

      <!-- New Row: Thumbnail Link -->
      <tr>
        <td><b>Thumbnail Link</b></td>
        <td><a href="{yt_thumb_url}" target="_blank" style="color: #1a73e8;">{yt_thumb_url}</a></td>
      </tr>

    </table>

    <p style="margin-top: 20px;">Please check in the approved section of the home page to view the details.</p>
  </body>
</html>
"""

    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("Approved mail sent successfully!")
    except Exception as e:
        print("Error:", e)
