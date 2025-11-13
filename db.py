from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
import os
MONGO_URL = os.getenv("MONGO_URL")


client = MongoClient(MONGO_URL)
db = client["myproject"]
channel_info = db["channel"]
user_info = db["user"]
video_info=db["video"]

def get_user_id(email,password):
    query = {"email":email, "password": password}
    result = user_info.find_one(query,{"_id": 1})
    if result is not None:
        return result["_id"]
    return ""

def get_owner_id(owner_email,channel_name):
    query = {"owner_email":owner_email,"channel_name":channel_name}
    result = channel_info.find_one(query,{"_id": 1})
    if result is not None:
        return result["_id"]
    return ""


def get_user_email_from_id(user_id):
    query = {"_id":user_id}
    result = user_info.find_one(query)
    if result is not None:
        return result["email"]

def check_user(email,password):
    query = {"email":email,"password":password}
    result = user_info.find_one(query,{"_id": 1})
    if result:
        return True
    else :
        return False
def get_password(email):
     query = {"email":email}
     result = user_info.find_one(query,{"password": 1})
     if result :
         return result["password"]
     else:
         return ""

def get_owner_email_and_channel_name_from_id(owner_id):
    query = {"_id":owner_id}
    result = channel_info.find_one(query)
    if result is not None:
        return {"owner_email":result["owner_email"],"channel_name": result["channel_name"]}  
    return {"owner_email":"","channel_name": ""} 

def get_refresh_token(owner_email,channel_name):
    query={"owner_email":owner_email,"channel_name":channel_name}
    result = channel_info.find_one(query,{"refresh_token":1})
    if result is not None:
        return result["refresh_token"]
    return ""

def check_channel(channel_name,owner_email):
    query = {"channel_name":channel_name, "owner_email":owner_email}
    result = channel_info.find_one(query,{"_id": 1})
    if result:
        return True
    else :
        return False

def insert_channel(refresh_token,channel_name,owner_email):
    entry={
        "channel_name":channel_name,
        "refresh_token":refresh_token,
        "owner_email":owner_email,
    }
    result = channel_info.insert_one(entry)
    print("Inserted channel ID:", result.inserted_id)

def insert_user(email,password):
    entry={
        "email":email,
        "password":password,
    }
    result = user_info.insert_one(entry)
    print("Inserted user ID:", result.inserted_id)

def insert_video(title,description,tags,category_id,privacy_status,video_file_name,video_extension,thumbnail_file_name,thumbnail_extension,user_id,owner_id):
    entry ={
        "title":title,
        "description":description,
        "tags": tags,
        "category_id": category_id,
        "privacy_status":privacy_status,
        "video_file_name": video_file_name,
        "video_extension":video_extension,
        "thumbnail_file_name":thumbnail_file_name,
        "thumbnail_extension": thumbnail_extension,
        "user_id":user_id,
        "owner_id":owner_id,
        "is_approved":False
    }
    result = video_info.insert_one(entry)
    print("Inserted video id ", result.inserted_id)
    return result.inserted_id

def get_video_info(video_id_list):
    video_info=[]
    for video_id in video_id_list:
        vid_query={"_id": video_id}
        result = video_info.find_one(vid_query)
        if result is not None:
            video_info.append(result)
    return video_info

def get_all_channel_names_and_owner_emails():
    channels = channel_info.find({}, {"_id": 0, "channel_name": 1,"owner_email": 1})
    if channels is not None:
        return channels
    return []
def delete_pending_video(video_id):
    print(video_id)
    query = {"_id": ObjectId(video_id), "is_approved": False}
    result = video_info.delete_one(query)
    print("Deleted count:", result.deleted_count)
    return result.deleted_count

def get_pending_video_info_user(user_id):
    query={"user_id": user_id, "is_approved":False}
    result = list(video_info.find(query))
    if result is not None:
        return result
    return []

def get_pending_video_info_owner(owner_id):
    query={"owner_id": owner_id, "is_approved":False}
    result = list(video_info.find(query))
    if result is not None:
        return result
    return []

def get_approved_video_info_user(user_id):
    query={"user_id": user_id, "is_approved":True}
    result = list(video_info.find(query))
    if result is not None:
        return result
    return []

def get_approved_video_info_owner(owner_id):
    query={"owner_id": owner_id, "is_approved":True}
    result = list(video_info.find(query))
    if result is not None:
        return result
    return []

def approve_video(video_id):
    query={"_id":ObjectId(video_id)}
    update_params={"$set":{"is_approved":True}}
    result = video_info.update_one(query,update_params)
    print("video approved in db")

# def approve_pending_video(owner_email, channel_name, video_id):