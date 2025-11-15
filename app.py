from flask import Flask, render_template, request, redirect, url_for,flash,send_from_directory,session
import os
import db 
import communication
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from googleapiclient.http import MediaFileUpload
import google.auth.transport.requests
from googleapiclient.discovery import build
from urllib.parse import urlencode
app = Flask(__name__)
app.secret_key = "super_secret_key"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/oauth"

BASE_UPLOAD_PATH = "data/uploads"
VIDEO_FOLDER = os.path.join(BASE_UPLOAD_PATH, "videos")
THUMBNAIL_FOLDER = os.path.join(BASE_UPLOAD_PATH, "thumbnails")

for folder in [VIDEO_FOLDER, THUMBNAIL_FOLDER]:
    os.makedirs(folder, exist_ok=True)

VIDEO_EXTENSIONS = {"mp4", "webm", "ogg","ogv"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
def get_flow():
    flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    return flow

def get_youtube_service(refresh_token):
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES
    )
    # Refresh automatically if expired
    service = build("youtube", "v3", credentials=creds)
    return service
def get_channel_info(youtube,credentials): #channel_name+owner_email
    request = youtube.channels().list(
        part="snippet",
        mine=True,
        maxResults=10
    )
    response = request.execute()
    channel_name = response["items"][0]["snippet"]["title"]
    request_session = google.auth.transport.requests.Request()
    id_info = id_token.verify_oauth2_token(
        credentials.id_token, request_session
    )

    owner_email = id_info.get("email")
    return channel_name,owner_email
def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set
def get_name_and_extension(orignal_name):
    name,ext=orignal_name.rsplit(".",1)
    return name,ext

@app.route("/")
def start():
    return render_template("start.html")


@app.route("/owner/signin", methods = ['GET'])
def register_as_owner():
    return render_template("signin_owner.html")

@app.route("/owner/signin", methods=['POST'])
def get_consent_screen():
    if session.get("owner_email") and session.get("channel_name"):
        params={"owner_email": session["owner_email"], "channel_name":session['channel_name']}
        return redirect(f"/owner/home?{urlencode(params)}")
    flow =get_flow()
    auth_url, state = flow.authorization_url(
    access_type="offline",           # request refresh token
    include_granted_scopes="true",
    prompt="consent"                 # force Google to always return refresh_token
    )
    session['oauth_state'] = state
    return redirect(auth_url)

@app.route("/oauth",methods = ['GET'])
def get_refresh_token():
    flow =get_flow()
    flow.state = session['oauth_state']
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    refresh_token= credentials.refresh_token
    youtube =get_youtube_service(refresh_token)
    channel,owner_email = get_channel_info(youtube,credentials)
    session["owner_email"]=owner_email
    session["channel_name"]=channel
    if db.check_channel(channel,owner_email) ==False:
        db.insert_channel(refresh_token,channel,owner_email)
    params={"owner_email": owner_email, "channel_name":channel}
    return redirect(f"/owner/home?{urlencode(params)}")
    

@app.route("/owner/home", methods =['GET'])
def home_owner():
    owner_email = request.args.get("owner_email")
    channel_name=request.args.get("channel_name")
    owner_id=db.get_owner_id(owner_email,channel_name)
    pending_video_info=db.get_pending_video_info_owner(owner_id)
    pending_video_user_emails=[db.get_user_email_from_id(vid["user_id"]) for vid in pending_video_info ]
    approved_video_info=db.get_approved_video_info_owner(owner_id)
    approved_video_user_emails=[db.get_user_email_from_id(vid["user_id"]) for vid in approved_video_info ]
    return render_template("home_owner.html",pending_videos=pending_video_info,approved_videos=approved_video_info,pending_video_user_emails = pending_video_user_emails,approved_video_user_emails = approved_video_user_emails,channel_name=channel_name,owner_email=owner_email)

@app.route("/user/signin", methods = ['GET'])
def register_as_user():
    return render_template("signin_user.html")

@app.route("/user/signin", methods = ['POST'])
def user_signin():
    session["email"] = request.form.get('email')
    session["password"] = request.form.get('password')
    password_from_db = db.get_password(session["email"])

    if password_from_db == "":
        session["otp"]  = communication.send_otp(session["email"])
        return redirect("/user/otp")
    elif password_from_db == session["password"]:
        return redirect("/user/home")
    else:
        flash("incorrect password")
        return render_template("signin_user.html")


@app.route("/user/otp", methods = ['GET'])
def send_otp():
    return render_template("otp.html")

@app.route("/user/otp", methods = ['POST'])
def verify_otp():
    received_otp = request.form.get('otp')
    if received_otp == session["otp"]:
        db.insert_user(session["email"],session["password"])
        return redirect("/user/home")
    else :
        flash("incorrect otp")

@app.route("/user/home", methods =['GET'])
def home_user():
    channels_info = db.get_all_channel_names_and_owner_emails()
    user_id=db.get_user_id(session["email"],session["password"])
    pending_video_info=db.get_pending_video_info_user(user_id)
    pending_video_owner_info=[db.get_owner_email_and_channel_name_from_id(vid["owner_id"]) for vid in pending_video_info] #has channel_name and owner_info
    approved_video_info=db.get_approved_video_info_user(user_id)
    approved_video_owner_info=[db.get_owner_email_and_channel_name_from_id(vid["owner_id"]) for vid in approved_video_info] #has channel_name and owner_info  
    return render_template("home_user.html",channels_info=channels_info,pending_videos=pending_video_info,pending_video_owner_info=pending_video_owner_info,approved_videos=approved_video_info,approved_video_owner_info=approved_video_owner_info)

          
@app.route("/videos/<filename>")
def get_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

@app.route("/thumbnails/<filename>")
def get_thumbnail(filename):
    return send_from_directory(THUMBNAIL_FOLDER, filename)

@app.route("/upload-request", methods=['GET'])
def video_upload():
    channel_name = request.args.get('channel_name')
    owner_email = request.args.get('owner_email')
    return render_template("video_upload.html", channel_name=channel_name, owner_email=owner_email)

@app.route("/upload-request",methods = ['POST'])
def upload_video():
    title = request.form.get("title")
    description = request.form.get("description")
    tags = request.form.get("tags")
    category_id = request.form.get("categoryId")
    privacy_status = request.form.get("privacyStatus")
    channel_name = request.form.get('channel_name')
    owner_email = request.form.get('owner_email')
    video_file = request.files.get("video_file")
    thumb_file = request.files.get("thumbnail_file")
    video_name,video_extension = get_name_and_extension(video_file.filename)
    thumbnail_name,thumbnail_extension = get_name_and_extension(thumb_file.filename)
    user_id=db.get_user_id(session["email"],session["password"])
    owner_id=db.get_owner_id(owner_email,channel_name)
    video_id=str(db.insert_video(title,description,tags,category_id,privacy_status,video_name,video_extension,thumbnail_name,thumbnail_extension,user_id,owner_id))
    if video_file and allowed_file(video_file.filename, VIDEO_EXTENSIONS):
        video_path = os.path.join(VIDEO_FOLDER, video_id+"."+video_extension)
        video_file.save(video_path)
    if thumb_file and allowed_file(thumb_file.filename, IMAGE_EXTENSIONS):
        thumb_path = os.path.join(THUMBNAIL_FOLDER, video_id+"."+thumbnail_extension)
        thumb_file.save(thumb_path)
    communication.send_approval_message(owner_email,channel_name,session["email"])
    flash(f"upload request sent successfully!", "success")
    return redirect("/user/home")

@app.route("/pending-approvals",methods=['GET'])
def check_approvals():
    if session.get("owner_email") and session.get("channel_name"):
        return redirect("/owner/home")
    else :
        return redirect("/owner/signin")

@app.route("/disapprove",methods=['POST'])
def disapprove():
    video_id = request.form.get("video_id")
    channel_name = request.form.get("channel_name")
    owner_email = request.form.get("owner_email")
    title = request.form.get("title")
    description = request.form.get("description")
    category_id = request.form.get("category_id")
    privacy_status = request.form.get("privacy_status")
    tags = request.form.get("tags")  # comma-separated string if sent as hidden input
    video_file_name = request.form.get("video_file_name")
    video_extension = request.form.get("video_extension")
    thumbnail_file_name = request.form.get("thumbnail_file_name")
    thumbnail_extension = request.form.get("thumbnail_extension")
    user_email = request.form.get("user_email")
    # optional: convert tags string back to a list
    if tags:
        tags = [t.strip() for t in tags.split(",")]
    communication.send_disapproved_message(user_email,channel_name,owner_email,title,description,tags,category_id,privacy_status,video_file_name,video_extension,thumbnail_file_name,thumbnail_extension)
    db.delete_pending_video(video_id)
    params={"owner_email": owner_email, "channel_name":channel_name}
    flash("Video disapproved successfully")
    return redirect(f"/owner/home?{urlencode(params)}")

@app.route("/approve",methods=['POST'])
def approve():
    video_id = request.form.get("video_id")
    channel_name = request.form.get("channel_name")
    owner_email = request.form.get("owner_email")
    title = request.form.get("title")
    description = request.form.get("description")
    category_id = request.form.get("category_id")
    privacy_status = request.form.get("privacy_status")
    tags = request.form.get("tags")  # comma-separated string if sent as hidden input
    video_file_name = request.form.get("video_file_name")
    video_extension = request.form.get("video_extension")
    thumbnail_file_name = request.form.get("thumbnail_file_name")
    thumbnail_extension = request.form.get("thumbnail_extension")
    user_email = request.form.get("user_email")
    # optional: convert tags string back to a list
    if tags:
        tags = [t.strip() for t in tags.split(",")]
    else:
        tags=[]
    refresh_token = db.get_refresh_token(owner_email,channel_name)
    youtube = get_youtube_service(refresh_token)
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": str(category_id),
        },
        "status": {
            "privacyStatus": privacy_status,  # "public", "private", or "unlisted"
        },
    }
    vid_file_name = f"{video_id}.{video_extension}"
    video_file =os.path.join(VIDEO_FOLDER,vid_file_name)

    if video_file and os.path.exists(video_file):
        media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
        vid_request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = vid_request.next_chunk()
            if status:
                print(f"Uploading... {int(status.progress() * 100)}%")
    yt_video_id = response["id"]
    print(f"yt video id:{yt_video_id}")
    thumb_file_name = f"{video_id}.{thumbnail_extension}"
    thumbnail_file = os.path.join(THUMBNAIL_FOLDER,thumb_file_name)
    if thumbnail_file and os.path.exists(thumbnail_file):
        youtube.thumbnails().set(
            videoId=response["id"],
            media_body=MediaFileUpload(thumbnail_file)
        ).execute()
        print("✅ Thumbnail uploaded successfully!")
    
    yt_embed_video_link = f"https://www.youtube.com/embed/{yt_video_id}"
    yt_watch_video_link = f"https://www.youtube.com/watch?v={yt_video_id}"
    yt_thumb_url = f"https://i.ytimg.com/vi/{yt_video_id}/mqdefault.jpg"


    communication.send_approved_message(user_email,channel_name,owner_email,title,description,tags,category_id,privacy_status,video_file_name,video_extension,thumbnail_file_name,thumbnail_extension,yt_watch_video_link,yt_thumb_url)
    db.approve_video(video_id,yt_embed_video_link,yt_thumb_url)
    params={"owner_email": owner_email, "channel_name":channel_name}

    flash("Video approved successfully")
    return redirect(f"/owner/home?{urlencode(params)}")

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
    # 