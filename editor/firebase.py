import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("C:\Users\chidu\Downloads\codex-c5ff0-firebase-adminsdk-fbsvc-10d716f3a4.json")

firebase_admin.initialize_app(cred)
