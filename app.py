from flask import Flask, render_template, request, redirect, url_for,flash,send_from_directory
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
app = Flask(__name__)

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

@app.route("/user/signin", methods = ['GET'])
def register_as_user():
    return render_template("signin_user.html")


@app.route("/owner/signin", methods=['POST'])
def get_consent_screen():
    auth_url, state = flow.authorization_url(
    access_type="offline",           # request refresh token
    include_granted_scopes="true",
    prompt="consent"                 # force Google to always return refresh_token
    )
    return redirect(auth_url)

@app.route("/user/signin", methods = ['POST'])
def user_signin():
    username = request.form.get('username')
    password = request.form.get('password')
    return f"Received username: {username}, password: {password}"
    
@app.route("/oauth",methods = ['GET'])
def get_refresh_token():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    refresh_token= credentials.refresh_token
    print("Refresh token "+ refresh_token)
    return redirect("/owner/home")

@app.route("/videos/<filename>")
def get_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)


@app.route("/thumbnails/<filename>")
def get_thumbnail(filename):
    return send_from_directory(THUMBNAIL_FOLDER, filename)

@app.route("/owner/home", methods =['GET'])
def home_owner():
   return render_template("home_owner.html")
    
@app.route("/upload",methods = ['GET'])
def home_user():
    youtube =get_youtube_service("1//0gUz1eN4xbkvcCgYIARAAGBASNgF-L9IrJpJC0yztXehjYMFgIGeSlG_-1z35gklLJ5Zr8kT-e54D2GCz9yT0O6I9tjrIKBsvHA")
    channel_name =get_channel_name(youtube)
    print(channel_name)
    return render_template("video_upload.html",channel_name=channel_name)

@app.route("/upload",methods = ['POST'])
def upload_video():
    title = request.form.get("title")
    description = request.form.get("description")

    video_file = request.files.get("video_file")
    thumb_file = request.files.get("thumbnail_file")

    # Save video in PV
    if video_file and allowed_file(video_file.filename, VIDEO_EXTENSIONS):
        video_path = os.path.join(VIDEO_FOLDER, video_file.filename)
        video_file.save(video_path)

    # Save thumbnail in PV
    if thumb_file and allowed_file(thumb_file.filename, IMAGE_EXTENSIONS):
        thumb_path = os.path.join(THUMBNAIL_FOLDER, thumb_file.filename)
        thumb_file.save(thumb_path)

    flash(f"File '{video.filename}' upload request sent successfully!", "success")
    return redirect()


if __name__ == "__main__":
    app.run(debug=True)
    # 