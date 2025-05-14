from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import make_password
import firebase_admin
from firebase_admin import auth, exceptions
import datetime
from .firebase import *


def landing_page(request):
    return render(request, "editor/home_page.html")


def login_view(request):
    if request.method == 'POST':
        # Process the login form
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # For simplicity, assume username is email
        email = username
        
        try:
            # Attempt to authenticate the user
            user = authenticate_firebase_user(email, password)
            
            if user:
                # Store only the user ID in the session
                request.session['user_id'] = user.uid
                
                print("User successfully logged in")
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
                'username': username.lower(),
                'email': email.lower(),
                'first_name': first_name.lower(),
                'last_name': last_name.lower(),
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
    if 'user_id' in request.session:
        del request.session['user_id']
    
    # Or alternatively, flush the entire session
    # request.session.flush()
    
    # Redirect to home page
    return redirect('landing_page')