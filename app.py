from flask import Flask, render_template, request, redirect, url_for,flash,send_from_directory,session
import os
import db 
import communication
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
import google.auth.transport.requests
from googleapiclient.discovery import build
app = Flask(__name__)
app.secret_key = "super_secret_key"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/oauth"
BASE_UPLOAD_PATH = "/data/uploads"
VIDEO_FOLDER = os.path.join(BASE_UPLOAD_PATH, "videos") 
THUMBNAIL_FOLDER = os.path.join(BASE_UPLOAD_PATH, "thumbnails")
VIDEO_EXTENSIONS = {"mp4", "webm", "ogg","ogv"}
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
def get_channel_info(youtube): #channel_name+owner_email
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
def get_new_name(new_name,orignal_name):
    name,ext=orignal_name.rsplit(".",1)
    return new_name+"."+ext
@app.route("/")
def start():
    return render_template("start.html")


@app.route("/owner/signin", methods = ['GET'])
def register_as_owner():
    return render_template("signin_owner.html")

@app.route("/owner/signin", methods=['POST'])
def get_consent_screen():
    if session["owner_email"]:
        return redirect("/owner/home")
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
    channel,owner_email = get_channel_info(youtube)
    session["owner_email"]=owner_email
    if db.check_channel(refresh_token,channel) ==False:
        db.insert_channel(refresh_token,channel,owner_email)
    return redirect("/owner/home")

@app.route("/owner/home", methods =['GET'])
def home_owner():
    return render_template("home_user.html")

@app.route("/user/signin", methods = ['GET'])
def register_as_user():
    return render_template("signin_user.html")

@app.route("/user/signin", methods = ['POST'])
def user_signin():
    session["email"] = request.form.get('email')
    session["password"] = request.form.get('password')
    if db.check_user(session["email"],session["password"]) == False:
        session["otp"]  = communication.send_otp(session["email"])
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

@app.route("/user/home", methods =['GET'])
def home_user():
    channels_info = db.get_all_channel_names_and_owner_emails()
    return render_template("home_user.html",channels_info=channels_info)

          
@app.route("/videos/<filename>")
def get_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

@app.route("/thumbnails/<filename>")
def get_thumbnail(filename):
    return send_from_directory(THUMBNAIL_FOLDER, filename)

@app.route("/upload-request",methods = ['GET'])
def video_upload():
    channel_name = request.args.get('channel_name')
    owner_email = request.args.get('owner_email')
    return render_template("video_upload.html",channel_name=channel_name,owner_email=owner_email)

@app.route("/upload-request",methods = ['POST'])
def upload_video():
    title = request.form.get("title")
    description = request.form.get("description")
    tags = request.form.get("tags")
    category_id = request.form.get("categoryId")
    privacy_status = request.form.get("privacyStatus")
    channel_name = request.args.get('channel_name')
    owner_email = request.args.get('owner_email')
    video_id=db.insert_video(title,description,tags,category_id,privacy_status,owner_email,session["email"],session["password"],channel_name)
    video_file = request.files.get("video_file")
    thumb_file = request.files.get("thumbnail_file")
    if video_file and allowed_file(video_file.filename, VIDEO_EXTENSIONS):
        video_path = os.path.join(VIDEO_FOLDER, get_new_name(video_id,video_file.filename))
        video_file.save(video_path)
    if thumb_file and allowed_file(thumb_file.filename, IMAGE_EXTENSIONS):
        thumb_path = os.path.join(THUMBNAIL_FOLDER, get_new_name(video_id,thumb_file.filename))
        thumb_file.save(thumb_path)
    communication.send_approval_message(owner_email,channel_name)
    flash(f"upload request sent successfully!", "success")
    return redirect("/user/home")

@app.route("/pending-approvals",methods=['GET'])
def check_approvals():
    if session["owner_email"]:
        return redirect("/owner/home")
    else :
        return redirect("/owner/signin")

if __name__ == "__main__":
    app.run(debug=True)
    # 