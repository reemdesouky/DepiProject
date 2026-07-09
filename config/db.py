import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = None
db     = None

def init_db(app=None):
    global client, db
    uri    = os.getenv("MONGO_URI")
    client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
    db     = client.get_default_database()
    print(f"Connected to MongoDB: {db.name}")

def get_db():
    return db