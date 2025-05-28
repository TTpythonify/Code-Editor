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
    

def create_code_project(project_data):
    """
    Create a new code project in Firestore
    
    Args:
        project_data (dict): Dictionary containing project information
            - title: Project title
            - description: Project description
            - language: Programming language
            - owner_id: Firebase user ID of the project owner
            - members: List of member email addresses (optional)
            - created_at: Creation timestamp
            
    Returns:
        str: The ID of the newly created project document
    """
    try:
        # Get a reference to the Firestore database
        db = firestore.client()
        
        # Add project to the 'code_projects' collection
        project_ref = db.collection('code_projects').document()
        
        # Initialize members count
        member_count = 0
        if 'members' in project_data and project_data['members']:
            member_count = len(project_data['members'])
        
        # Add member_count to the project data
        project_data['member_count'] = member_count
        
        # Set the document with project data
        project_ref.set(project_data)
        
        # Return the document ID
        return project_ref.id
        
    except Exception as e:
        print(f"Error creating code project: {str(e)}")
        raise e

def get_user_projects(user_id):
    """
    Get all code projects owned by a specific user
    
    Args:
        user_id (str): Firebase user ID
        
    Returns:
        list: List of project dictionaries with formatted timestamps
    """
    try:
        # Get a reference to the Firestore database
        db = firestore.client()
        
        # Query the code_projects collection for projects owned by this user
        projects_ref = db.collection('code_projects').where('owner_id', '==', user_id)
        projects = projects_ref.stream()
        
        # Convert to a list of dictionaries
        project_list = []
        for project in projects:
            project_data = project.to_dict()
            # Add the project ID to the data
            project_data['id'] = project.id
            
            # Format timestamps for display
            if 'created_at' in project_data and hasattr(project_data['created_at'], 'seconds'):
                timestamp = project_data['created_at'].seconds + project_data['created_at'].nanos/1e9
                project_data['created_at_formatted'] = format_timestamp_relative(timestamp)
            
            project_list.append(project_data)
        
        return project_list
    
    except Exception as e:
        print(f"Error getting user projects: {str(e)}")
        return []

def get_projects_shared_with_user(user_email):
    """
    Get all code projects shared with a specific user via their email
    
    Args:
        user_email (str): User's email address
        
    Returns:
        list: List of project dictionaries with formatted timestamps
    """
    try:
        # Get a reference to the Firestore database
        db = firestore.client()
        
        # Query the code_projects collection for projects where the user is a member
        projects_ref = db.collection('code_projects').where('members', 'array_contains', user_email)
        projects = projects_ref.stream()
        
        # Convert to a list of dictionaries
        project_list = []
        for project in projects:
            project_data = project.to_dict()
            # Add the project ID to the data
            project_data['id'] = project.id
            
            # Format timestamps for display
            if 'created_at' in project_data and hasattr(project_data['created_at'], 'seconds'):
                timestamp = project_data['created_at'].seconds + project_data['created_at'].nanos/1e9
                project_data['created_at_formatted'] = format_timestamp_relative(timestamp)
            
            project_list.append(project_data)
        
        return project_list
    
    except Exception as e:
        print(f"Error getting shared projects: {str(e)}")
        return []

def format_timestamp_relative(timestamp):
    """
    Format a timestamp into a human-readable relative time string
    e.g., "2 days ago", "5 minutes ago", etc.
    
    Args:
        timestamp (float): Unix timestamp (seconds since epoch)
        
    Returns:
        str: Formatted relative time string
    """
    import datetime
    
    # Convert timestamp to datetime
    dt = datetime.datetime.fromtimestamp(timestamp)
    now = datetime.datetime.now()
    diff = now - dt
    
    if diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds // 3600 > 0:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds // 60 > 0:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"

def get_project_by_id(project_id):
    """
    Get a specific code project by its ID
    
    Args:
        project_id (str): The ID of the project to retrieve
        
    Returns:
        dict: Project data or None if not found
    """
    try:
        # Get a reference to the Firestore database
        db = firestore.client()
        
        # Get the document
        project_ref = db.collection('code_projects').document(project_id)
        project = project_ref.get()
        
        if project.exists:
            project_data = project.to_dict()
            # Add the project ID to the data
            project_data['id'] = project.id
            
            # Format timestamps for display
            if 'created_at' in project_data and hasattr(project_data['created_at'], 'seconds'):
                timestamp = project_data['created_at'].seconds + project_data['created_at'].nanos/1e9
                project_data['created_at_formatted'] = format_timestamp_relative(timestamp)
                
            return project_data
        else:
            return None
            
    except Exception as e:
        print(f"Error getting project: {str(e)}")
        return None
    




def search_users_by_username(query, limit=10):
    """
    Search for users by username in the users_profile collection
    
    Args:
        query (str): Search query for username
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of user dictionaries with username and email
    """
    try:
        # Get a reference to the Firestore database
        db = firestore.client()
        
        # Query users_profile collection for usernames that start with the query
        # Note: Firestore doesn't support case-insensitive searches, so we'll do exact match
        # and then filter in Python for better matching
        users_ref = db.collection('users_profile')
        
        # Get all users and filter in Python (not efficient for large datasets)
        # For production, consider using Algolia or similar for better search
        all_users = users_ref.stream()
        
        matching_users = []
        query_lower = query.lower()
        
        for user_doc in all_users:
            user_data = user_doc.to_dict()
            username = user_data.get('username', '').lower()
            
            # Check if username contains the query
            if query_lower in username and len(matching_users) < limit:
                matching_users.append({
                    'user_id': user_doc.id,
                    'username': user_data.get('username', ''),
                    'email': user_data.get('email', ''),
                    'display_name': user_data.get('display_name', ''),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', '')
                })
        
        return matching_users
        
    except Exception as e:
        print(f"Error searching users: {str(e)}")
        return []

def create_project_invitation(sender_id, recipient_username, project_id, project_title, project_description=""):
    """
    Create a project invitation notification
    
    Args:
        sender_id (str): Firebase user ID of the person sending the invite
        recipient_username (str): Username of the person being invited
        project_id (str): ID of the project being shared
        project_title (str): Title of the project
        project_description (str): Description of the project
        
    Returns:
        str: The ID of the created notification
    """
    try:
        # Get sender's profile
        sender_profile = get_user_profile(sender_id)
        sender_name = sender_profile.get('display_name') or f"{sender_profile.get('first_name', '')} {sender_profile.get('last_name', '')}".strip()
        
        # Find recipient by username
        recipient_users = search_users_by_username(recipient_username, limit=1)
        if not recipient_users:
            raise Exception(f"User with username '{recipient_username}' not found")
        
        recipient = recipient_users[0]
        recipient_id = recipient['user_id']
        
        # Create notification data
        notification_data = {
            'type': 'project_invitation',
            'sender_id': sender_id,
            'sender_name': sender_name,
            'sender_email': sender_profile.get('email', ''),
            'recipient_id': recipient_id,
            'recipient_username': recipient_username,
            'recipient_email': recipient['email'],
            'project_id': project_id,
            'project_title': project_title,
            'project_description': project_description,
            'message': f"{sender_name} invited you to join '{project_title}'",
            'status': 'pending',  # pending, accepted, declined
            'created_at': datetime.datetime.now(),
            'read': False
        }
        
        # Add notification to Firestore
        db = firestore.client()
        notification_ref = db.collection('notifications').document()
        notification_ref.set(notification_data)
        
        return notification_ref.id
        
    except Exception as e:
        print(f"Error creating project invitation: {str(e)}")
        raise e

def get_user_notifications(user_id, limit=20):
    """
    Get all notifications for a user
    
    Args:
        user_id (str): Firebase user ID
        limit (int): Maximum number of notifications to return
        
    Returns:
        list: List of notification dictionaries
    """
    try:
        db = firestore.client()
        
        # Query notifications where the user is the recipient
        notifications_ref = db.collection('notifications').where('recipient_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
        notifications = notifications_ref.stream()
        
        notification_list = []
        for notification in notifications:
            notification_data = notification.to_dict()
            notification_data['id'] = notification.id
            
            # Format timestamp
            if 'created_at' in notification_data and hasattr(notification_data['created_at'], 'seconds'):
                timestamp = notification_data['created_at'].seconds + notification_data['created_at'].nanos/1e9
                notification_data['created_at_formatted'] = format_timestamp_relative(timestamp)
            
            notification_list.append(notification_data)
        
        return notification_list
        
    except Exception as e:
        print(f"Error getting user notifications: {str(e)}")
        return []

def update_notification_status(notification_id, status, user_id=None):
    """
    Update the status of a notification (accept/decline invitation)
    
    Args:
        notification_id (str): ID of the notification
        status (str): New status ('accepted', 'declined', 'read')
        user_id (str): Optional user ID for validation
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db = firestore.client()
        notification_ref = db.collection('notifications').document(notification_id)
        
        # Get the notification first to validate
        notification = notification_ref.get()
        if not notification.exists:
            return False
        
        notification_data = notification.to_dict()
        
        # Validate user has permission to update this notification
        if user_id and notification_data.get('recipient_id') != user_id:
            return False
        
        # Update the notification
        update_data = {
            'status': status,
            'updated_at': datetime.datetime.now()
        }
        
        if status in ['accepted', 'declined']:
            update_data['read'] = True
        elif status == 'read':
            update_data['read'] = True
        
        notification_ref.update(update_data)
        
        # Handle project invitation responses
        if notification_data.get('type') == 'project_invitation':
            project_id = notification_data.get('project_id')
            recipient_email = notification_data.get('recipient_email')
            
            if status == 'accepted':
                # Add user to project
                add_user_to_project(project_id, recipient_email)
            elif status == 'declined':
                # Remove from pending invitations
                remove_pending_invitation(project_id, recipient_email)
        
        return True
        
    except Exception as e:
        print(f"Error updating notification status: {str(e)}")
        return False

def add_user_to_project(project_id, user_email):
    """
    Add a user to a project's members list and remove from pending invitations
    
    Args:
        project_id (str): ID of the project
        user_email (str): Email of the user to add
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db = firestore.client()
        project_ref = db.collection('code_projects').document(project_id)
        
        # Get current project data
        project = project_ref.get()
        if not project.exists:
            return False
        
        project_data = project.to_dict()
        current_members = project_data.get('members', [])
        pending_invitations = project_data.get('pending_invitations', [])
        
        # Add user if not already a member
        if user_email not in current_members:
            current_members.append(user_email)
            
            # Remove from pending invitations
            if user_email in pending_invitations:
                pending_invitations.remove(user_email)
            
            # Update project with new member
            project_ref.update({
                'members': current_members,
                'pending_invitations': pending_invitations,
                'member_count': len(current_members),
                'updated_at': datetime.datetime.now()
            })
        
        return True
        
    except Exception as e:
        print(f"Error adding user to project: {str(e)}")
        return False

def remove_pending_invitation(project_id, user_email):
    """
    Remove a user from pending invitations when they decline
    
    Args:
        project_id (str): ID of the project
        user_email (str): Email of the user who declined
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db = firestore.client()
        project_ref = db.collection('code_projects').document(project_id)
        
        # Get current project data
        project = project_ref.get()
        if not project.exists:
            return False
        
        project_data = project.to_dict()
        pending_invitations = project_data.get('pending_invitations', [])
        
        # Remove from pending invitations
        if user_email in pending_invitations:
            pending_invitations.remove(user_email)
            
            # Update project
            project_ref.update({
                'pending_invitations': pending_invitations,
                'updated_at': datetime.datetime.now()
            })
        
        return True
        
    except Exception as e:
        print(f"Error removing pending invitation: {str(e)}")
        return False

def get_unread_notifications_count(user_id):
    """
    Get the count of unread notifications for a user
    
    Args:
        user_id (str): Firebase user ID
        
    Returns:
        int: Number of unread notifications
    """
    try:
        db = firestore.client()
        
        # Query unread notifications
        notifications_ref = db.collection('notifications').where('recipient_id', '==', user_id).where('read', '==', False)
        notifications = notifications_ref.stream()
        
        return len(list(notifications))
        
    except Exception as e:
        print(f"Error getting unread notifications count: {str(e)}")
        return 0