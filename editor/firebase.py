import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import requests
import json
import datetime

# Initialize Firebase Admin SDK with your credentials file
cred = credentials.Certificate("C:\\Users\\chidu\\Downloads\\codex-c5ff0-firebase-adminsdk-fbsvc-10d716f3a4.json")
firebase_app = firebase_admin.initialize_app(cred)

# Get Firestore database instance
db = firestore.client()
firebase_api_key = "AIzaSyD89rKPQvjcIDhVivNIfU-JFpZa-ildhjw"  

# Helper function for creating a new user in Firebase Auth
def create_firebase_user(email, password, display_name=None):
    """
    Create a new user in Firebase Authentication
    Returns the user record or raises an exception
    """
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False
        )
        return user
    except Exception as e:
        # Handle specific Firebase Auth exceptions here
        raise e

# Helper function for creating a user profile in Firestore
def create_user_profile(uid, profile_data):
    """
    Create a user profile document in Firestore 'users_profile' collection
    """
    users_ref = db.collection('users_profile')
    users_ref.document(uid).set(profile_data)

# Helper function for authenticating a user
def authenticate_firebase_user(email, password):
    """
    Authenticate user with Firebase Auth REST API
    This method properly verifies the password
    """
    # If we have the API key, use the REST API for proper authentication
    if firebase_api_key:
        try:
            # Call the Firebase Auth REST API to authenticate with email/password
            auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(auth_url, data=json.dumps(payload))
            data = response.json()
            
            if response.status_code == 200:
                # Authentication successful, get the user data from Firebase
                user = auth.get_user_by_email(email)
                return user
            else:
                # Authentication failed
                print(f"Auth error: {data.get('error', {}).get('message')}")
                return None
                
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    else:
        # Fallback to just checking if user exists (not secure for production)
        try:
            # WARNING: This fallback method does not verify passwords!
            # It only checks if the user exists which is insecure
            user = auth.get_user_by_email(email)
            print("WARNING: PASSWORD VERIFICATION SKIPPED. This is insecure!")
            print("Please set the Firebase API key in firebase.py for secure authentication.")
            return user
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            raise e

# Helper function for retrieving a user profile
def get_user_profile(uid):
    """
    Retrieve a user profile from Firestore
    """
    doc_ref = db.collection('users_profile').document(uid)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None




def get_user_profile(user_id):
    """
    Retrieve a user's profile from the 'users_profile' collection in Firestore
    based on their user_id
    
    Args:
        user_id (str): The Firebase Auth user ID
        
    Returns:
        dict: User profile information including username, email, names, 
              and login timestamps, or None if not found
    """
    try:
        # Get a reference to the Firestore database
        db = firestore.client()
        
        # Reference the specific document in the users_profile collection
        user_ref = db.collection('users_profile').document(user_id)
        
        # Get the document
        user_doc = user_ref.get()
        
        # Check if the document exists
        if user_doc.exists:
            # Convert to dictionary
            profile_data = user_doc.to_dict()
            
            # Format timestamps for display if needed
            if 'created_at' in profile_data and hasattr(profile_data['created_at'], 'seconds'):
                timestamp = profile_data['created_at'].seconds + profile_data['created_at'].nanos/1e9
                profile_data['created_at_formatted'] = datetime.datetime.fromtimestamp(timestamp).strftime('%B %d, %Y at %I:%M:%S %p %Z')
                
            if 'last_login' in profile_data and hasattr(profile_data['last_login'], 'seconds'):
                timestamp = profile_data['last_login'].seconds + profile_data['last_login'].nanos/1e9
                profile_data['last_login_formatted'] = datetime.datetime.fromtimestamp(timestamp).strftime('%B %d, %Y at %I:%M:%S %p %Z')
            
            return profile_data
        else:
            print(f"No user profile found for user_id: {user_id}")
            return None
            
    except Exception as e:
        print(f"Error retrieving user profile: {str(e)}")
        return None