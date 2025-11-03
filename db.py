from pymongo import MongoClient
from pymongo.errors import PyMongoError
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

def insert_video(title,description,tags,category_id,privacy_status,owner_email,user_email,password,channel_name,video_extension,thumbnail_extension):
    channel_pending_video_list=get_pending_video_list_channel(owner_email,channel_name)
    user_pending_video_list=get_pending_video_list_user(user_email,password)
    with client.start_session() as session:
        with session.start_transaction():
            # inseet video info
            entry ={
                "title":title,
                "description":description,
                "tags": tags,
                "category_id": category_id,
                "privacy_status":privacy_status,
                "video_extension":video_extension,
                "thumbnail_extension": thumbnail_extension
            }
            result = video_info.insert_one(entry,session=session)
            #  update user's pending video table
            user_pending_video_list.append(result.inserted_id)
            user_filter={"email":user_email,"password":password}
            user_update_value= {"$set": {"pending_video_list": user_pending_video_list}}
            user_info.update_one(user_filter,user_update_value,session=session)
            #  update channels's pending video table
            channel_pending_video_list.append(result.inserted_id)
            channel_filter={"owner_email":owner_email,"channel_name":channel_name}
            channel_update_value= {"$set": {"pending_video_list": channel_pending_video_list}}
            channel_info.update_one(channel_filter,channel_update_value,session=session)
            print("Inserted video id ", result.inserted_id)
            return result.inserted_id


def get_pending_video_list_user(email,password):
    query = {"email":email, "password": password}
    result = user_info.find_one(query,{"pending_video_list": 1})
    return result["pending_video_list"]

def get_pending_video_list_channel(owner_email,channel_name):
    query = {"owner_email":owner_email, "channel_name": channel_name}
    result = user_info.find_one(query,{"pending_video_list": 1})
    return result["pending_video_list"]

def get_approved_video_list_user(email,password):
    query = {"email":email, "password": password}
    result = user_info.find_one(query,{"approved_video_list": 1})
    return result["pending_video_list"]

def get_approved_video_list_channel(owner_email,channel_name):
    query = {"owner_email":owner_email, "channel_name": channel_name}
    result = user_info.find_one(query,{"approved_video_list": 1})
    return result["pending_video_list"]

def get_video_info(video_id_list):
    video_info=[]
    for video_id in video_id_list:
        vid_query={"_id": video_id}
        result = video_info.find_one(vid_query)
        video_info.append(result)
    return video_info

def get_all_channel_names_and_owner_emails():
    channels = channel_info.find({}, {"_id": 0, "channel_name": 1,"owner_email": 1})
    return channels

def delete_pending_video(owner_email,channel_name,video_id):
    channel_pending_video_list=get_pending_video_list_channel(owner_email,channel_name)
    channel_pending_video_list.remove(video_id)
    with client.start_session() as session:
        with session.start_transaction():
            # delete video info
            query ={"_id":video_id}
            result = video_info.delete_one(query,session=session)
            #  update channels's pending video table
            channel_filter={"owner_email":owner_email,"channel_name":channel_name}
            channel_update_value= {"$set": {"pending_video_list": channel_pending_video_list}}
            channel_info.update_one(channel_filter,channel_update_value,session=session)
            print("delete video id",video_id)

def approve_pending_video(owner_email, channel_name, video_id):
    # Get current lists
    channel_pending_video_list = get_pending_video_list_channel(owner_email, channel_name)
    channel_approved_video_list = get_approved_video_list_channel(owner_email, channel_name)
    channel_pending_video_list.remove(video_id)
    channel_approved_video_list.append(video_id)

    with client.start_session() as session:
        with session.start_transaction():
            # Common filter
            channel_filter = {"owner_email": owner_email, "channel_name": channel_name}

            # Update pending video list
            channel_pending_update_value = {"$set": {"pending_video_list": channel_pending_video_list}}
            channel_info.update_one(channel_filter, channel_pending_update_value, session=session)

            # Update approved video list
            channel_approved_update_value = {"$set": {"approved_video_list": channel_approved_video_list}}
            channel_info.update_one(channel_filter, channel_approved_update_value, session=session)

            print("Video approved:", video_id)