from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import make_password
import firebase_admin
from firebase_admin import auth, exceptions
import datetime
from .firebase import *


# Helper function to handle Firebase DatetimeWithNanoseconds for JSON serialization
def convert_firebase_timestamps(obj):
    """Convert Firebase timestamps to Python datetime objects"""
    # Check if it's a dictionary
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[key] = convert_firebase_timestamps(value)
        return result
    # Check if it's a list
    elif isinstance(obj, list):
        return [convert_firebase_timestamps(item) for item in obj]
    # If it's a Firebase DatetimeWithNanoseconds object, convert to standard datetime
    elif hasattr(obj, 'seconds') and hasattr(obj, 'nanos'):
        # Convert to standard Python datetime
        return datetime.datetime.fromtimestamp(obj.seconds + obj.nanos/1e9)
    # If it's any other type of object, return as is
    return obj


def landing_page(request):
    return render(request, "editor/home_page.html")


def login_view(request):
    if request.method == 'POST':
        # Process the login form
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if username is actually an email
        # For simplicity in this implementation, we'll assume username is email
        email = username
        
        try:
            # Attempt to authenticate the user
            user = authenticate_firebase_user(email, password)
            
            if user:
                # User authenticated successfully
                # Store user data in the session
                user_data = {
                    'uid': user.uid,
                    'email': user.email,
                    'display_name': user.display_name,
                }
                request.session['user_data'] = user_data
                print(user_data)
                
                # Get additional profile data from Firestore
                profile = get_user_profile(user.uid)
                if profile:
                    # Convert Firebase timestamps to Python datetime objects
                    profile = convert_firebase_timestamps(profile)
                    # Store in session
                    request.session['user_profile'] = profile
                
                print(" This is where the user now goes to the actual app")
                return redirect('/codex-home/') 
                
            else:
                # Authentication failed
                return render(request, 'editor/login.html', {
                    'error_message': 'Invalid email or password.'
                })
                
        except Exception as e:
            # Handle any exceptions during authentication
            return render(request, 'editor/login.html', {
                'error_message': f'Login error: {str(e)}'
            })
    
    # If GET request, just show the login form
    return render(request, 'editor/login.html')


def signup_view(request):
    if request.method == 'POST':
        # Process the signup form
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Basic validation
        if password != confirm_password:
            return render(request, 'editor/signup.html', {
                'error_message': 'Passwords do not match.'
            })
        
        try:
            # Create user in Firebase Authentication
            # Note: Firebase handles password encryption automatically
            display_name = f"{first_name} {last_name}" if last_name else first_name
            firebase_user = create_firebase_user(email, password, display_name)
            
            # Create user profile in Firestore
            profile_data = {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'display_name': display_name,
                'created_at': datetime.datetime.now(),
                'last_login': datetime.datetime.now()
            }
            
            # Store user profile in Firestore
            create_user_profile(firebase_user.uid, profile_data)
            
            # Redirect to login page with success message
            return render(request, 'editor/login.html', {
                'success_message': 'Account created successfully! Please login.'
            })
            
        except firebase_admin.auth.EmailAlreadyExistsError:
            return render(request, 'editor/signup.html', {
                'error_message': 'Email already registered.'
            })
        except firebase_admin.auth.UidAlreadyExistsError:
            return render(request, 'editor/signup.html', {
                'error_message': 'Username already taken.'
            })
        except Exception as e:
            # Handle any other exceptions
            return render(request, 'editor/signup.html', {
                'error_message': f'Error creating account: {str(e)}'
            })
    
    # If GET request, just show the signup form
    return render(request, 'editor/signup.html')


def logout_view(request):
    # Clear the user session
    if 'user_data' in request.session:
        del request.session['user_data']
    if 'user_profile' in request.session:
        del request.session['user_profile']
    
    # Redirect to home page
    return redirect('landing_page')