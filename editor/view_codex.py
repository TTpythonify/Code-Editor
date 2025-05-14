from django.shortcuts import render, redirect
from django.contrib import messages
from .firebase import *
import json
import datetime

def codex_home_page(request):
    current_user = request.session.get("user_id")

    # Check if user_id is missing
    if not current_user:
        return redirect('/login/')  # Or another appropriate page

    try:
        # Get user profile
        user_profile = get_user_profile(current_user)

        # Make sure 'username' exists in the profile
        username = user_profile.get('username', 'User')
        
        # Get user's email for shared projects
        user_email = user_profile.get('email')
        
        # Get projects owned by the user
        owned_projects = get_user_projects(current_user)
        
        # Get projects shared with the user
        if user_email:
            shared_projects = get_projects_shared_with_user(user_email)
        else:
            shared_projects = []
        
        # Combine owned and shared projects
        all_projects = owned_projects + shared_projects
        
        # Sort projects by creation date (newest first)
        all_projects.sort(key=lambda x: x.get('created_at', 0) if hasattr(x.get('created_at'), 'seconds') 
                         else 0, reverse=True)

        return render(
            request, 
            "codex/codex_home_page.html", 
            {
                'name': username.upper(),
                'projects': all_projects,
                'profile': user_profile,
            }
        )

    except Exception as e:
        # Log the error and handle gracefully
        print(f"Error loading user profile: {e}")
        return render(
            request, 
            "codex/codex_home_page.html", 
            {'name': 'Guest'}
        )

def create_project(request):
    if request.method != 'POST':
        return redirect('/codex-home/')
    
    # Get user ID from session
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('/login/')
    
    try:
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        language = request.POST.get('language')
        
        # Parse members JSON
        members_json = request.POST.get('members', '[]')
        try:
            members = json.loads(members_json)
        except json.JSONDecodeError:
            members = []
        
        # Get user profile to add owner's info
        user_profile = get_user_profile(user_id)
        owner_email = user_profile.get('email', '')
        owner_name = user_profile.get('display_name') or f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip()
        
        # Create project data
        project_data = {
            'title': title,
            'description': description,
            'language': language,
            'owner_id': user_id,
            'owner_email': owner_email,
            'owner_name': owner_name,
            'members': members,
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now(),
            'code_content': '',  # Initial empty content
            'is_public': False,  # Default to private
        }
        
        # Create the project in Firebase
        project_id = create_code_project(project_data)
        
        # Add success message
        messages.success(request, f'Project "{title}" created successfully!')
        
        # Redirect to the code editor for this project (you'll implement this later)
        # For now, redirect back to the home page
        return redirect('/codex-home/')
        
    except Exception as e:
        # Log the error
        print(f"Error creating project: {str(e)}")
        
        # Add error message
        messages.error(request, f'Error creating project: {str(e)}')
        
        # Redirect back to home page
        return redirect('/codex-home/')