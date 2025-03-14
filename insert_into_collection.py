from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi

from get_database import getDataBase
dbname = getDataBase()
collectionName = dbname['announcements']  # Specify the actual collection name

# Example function to insert a document
def insert_announcement(title, time, message, links, name):
    doc = {
        "title": title,
        "time": time,
        "message": message,
        "links": links,
        "name": name
    }
    result = collectionName.insert_one(doc)
    print(f"Inserted document with ID: {result.inserted_id}")

