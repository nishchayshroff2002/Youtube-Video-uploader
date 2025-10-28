from pymongo import MongoClient
import os
MONGO_URL = os.getenv("MONGO_URL")


client = MongoClient(MONGO_URI)
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

def insert_channel(refresh_token,channel_name):
    video_list=[]
    entry={
        "channel_name":channel_name,
        "refresh_token":refresh_token,
        "video_list":video_list
    }
    result = channel_info.insert_one(entry)
    print("Inserted channel ID:", result.inserted_id)

def insert_user(email,password):
    video_list=[]
    entry={
        "email":email,
        "password":password,
        "video_list":video_list
    }
    result = user_info.insert_one(entry)
    print("Inserted user ID:", result.inserted_id)