from pymongo.mongo_client import MongoClient
import certifi

uri = "mongodb+srv://seanhyde04:8kWiZWCqz1hsdGaV@discordbotannouncements.elqf3.mongodb.net/?retryWrites=true&w=majority&appName=DiscordBotAnnouncements"
client = MongoClient(uri, tlsCAFile=certifi.where())

def getDataBase():
    # Replace 'stored_announcements' with your actual database name if needed.
    return client['stored_announcements']