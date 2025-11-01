from pymongo import MongoClient
import os
MONGO_URL = os.getenv("MONGO_URL")


client = MongoClient(MONGO_URL)
db = client["myproject"]
channel_info = db["channel"]
user_info = db["user"]
video_info=db["video"]

def check_user(email,password):
    query = {"email":email, "password": password}
    result = user_info.find_one(query,{"_id": 1})
    if result:
        return True
    else :
        return False

def check_channel(refresh_token,channel_name):
    query = {"channel_name":channel_name, "refresh_token": refresh_token}
    result = user_info.find_one(query,{"_id": 1})
    if result:
        return True
    else :
        return False

def insert_channel(refresh_token,channel_name,owner_email):
    uploaded_video_list=[]
    pending_video_list=[]
    entry={
        "channel_name":channel_name,
        "refresh_token":refresh_token,
        "owner_email":owner_email,
        "uploaded_video_list":uploaded_video_list,
        "pending_video_list":pending_video_list
    }
    result = channel_info.insert_one(entry)
    print("Inserted channel ID:", result.inserted_id)

def insert_user(email,password):
    uploaded_video_list=[]
    pending_video_list=[]
    entry={
        "email":email,
        "password":password,
        "uploaded_video_list":uploaded_video_list,
        "pending_video_list":pending_video_list
    }
    result = user_info.insert_one(entry)
    print("Inserted user ID:", result.inserted_id)
def insert_video(title,description,tags,category_id,privacy_status):
    entry ={
        "title":title,
        "description":description,
        "tags": tags,
        "category_id": category_id,
        "privacy_status":privacy_status
    }
    result = video_info.insert_one(entry)

    print("Inserted video id ", result.inserted_id)
    return result.inserted_id
def allocate_pending_video_to_user(email,password,video_id):
    query={"email":email,"password":password}
    result = user_info.find_one(query,{"pending_video_list": 1})
    pending_list=result["pending_video_list"]
    pending_list.append(video_id)
    new_update={"$set": {"pending_video_list":pending_list}}
    update_result = user_info.update_one(query,new_update)
    if update_result.matched_count > 0:
        print(" Video added to pending list of user!")
    else:
        print("Error in adding video to pending list")
def get_all_channels():
    channels = channel_info.find({}, {"_id": 0, "channel_name": 1})
    channel_names = [ch["channel_name"] for ch in channels]
    return channel_names