from flask import Flask, render_template, request, redirect, url_for,flash,send_from_directory,session
import os
import db 
import sendotp
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
app = Flask(__name__)
app.secret_key = "super_secret_key"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/oauth"
BASE_UPLOAD_PATH = "/data/uploads"
VIDEO_FOLDER = os.path.join(BASE_UPLOAD_PATH, "videos") 
THUMBNAIL_FOLDER = os.path.join(BASE_UPLOAD_PATH, "thumbnails")
VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload"
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
        scopes=["https://www.googleapis.com/auth/youtube.readonly"]
    )
    # Refresh automatically if expired
    service = build("youtube", "v3", credentials=creds)
    return service
def get_channel_name(youtube):
    request = youtube.channels().list(
        part="snippet",
        mine=True,
        maxResults=10
    )
    response = request.execute()
    return response["items"][0]["snippet"]["title"]
def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set

@app.route("/")
def start():
    return render_template("start.html")


@app.route("/owner/signin", methods = ['GET'])
def register_as_owner():
    return render_template("signin_owner.html")

@app.route("/owner/signin", methods=['POST'])
def get_consent_screen():
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
    channel = get_channel_name(youtube)
    if db.check_channel(refresh_token,channel) ==False:
        db.insert_channel(refresh_token,channel,session["email"])
    return redirect("/owner/home")

@app.route("/owner/home", methods =['GET'])
def home_owner():
    channel_names = db.get_all_channels()
    return render_template("home_owner.html",channel_names=channel_names)

@app.route("/user/signin", methods = ['GET'])
def register_as_user():
    return render_template("signin_user.html")

@app.route("/user/signin", methods = ['POST'])
def user_signin():
    session["email"] = request.form.get('email')
    session["password"] = request.form.get('password')
    if db.check_user(session["email"],session["password"]) == False:
        session["otp"]  = sendotp.send_otp(session["email"])
        return redirect("/user/otp")
    return redirect("/user/home")

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

@app.route("/user/home", methods = ['GET'])
def home_user():
    return render_template("home_user.html")
          
@app.route("/videos/<filename>")
def get_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

@app.route("/thumbnails/<filename>")
def get_thumbnail(filename):
    return send_from_directory(THUMBNAIL_FOLDER, filename)

@app.route("/upload/<channel_name>",methods = ['GET'])
def video_upload(channel_name):
    return render_template("video_upload.html",channel_name=channel_name)

@app.route("/upload/<channel_name>",methods = ['POST'])
def upload_video():
    title = request.form.get("title")
    description = request.form.get("description")
    tags = request.form.get("tags")
    category_id = request.form.get("categoryId")
    privacy_status = request.form.get("privacyStatus")
    video_file = request.files.get("video_file")
    thumb_file = request.files.get("thumbnail_file")
    if video_file and allowed_file(video_file.filename, VIDEO_EXTENSIONS):
        video_path = os.path.join(VIDEO_FOLDER, video_file.filename)
        video_file.save(video_path)
    if thumb_file and allowed_file(thumb_file.filename, IMAGE_EXTENSIONS):
        thumb_path = os.path.join(THUMBNAIL_FOLDER, thumb_file.filename)
        thumb_file.save(thumb_path)

    flash(f"File '{video.filename}' upload request sent successfully!", "success")
    return redirect()


if __name__ == "__main__":
    app.run(debug=True)
    # 