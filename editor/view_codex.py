from django.shortcuts import render, redirect
from django.contrib import messages
from .firebase import *
import json
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json



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

# Add these views to your view_codex.py file

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def search_users(request):
    """
    AJAX endpoint to search for users by username
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    # Check if user is logged in
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'users': []})
        
        # Search for users
        users = search_users_by_username(query, limit=10)
        
        # Remove current user from results
        current_user_profile = get_user_profile(user_id)
        current_username = current_user_profile.get('username', '')
        
        filtered_users = [user for user in users if user.get('username') != current_username]
        
        return JsonResponse({'users': filtered_users})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Error in search_users: {str(e)}")
        return JsonResponse({'error': 'Search failed'}, status=500)

def create_project(request):
    """
    Updated create_project view to handle username-based invitations
    """
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
        
        # Parse members JSON - now contains username and email objects
        members_json = request.POST.get('members', '[]')
        try:
            invited_members = json.loads(members_json)
        except json.JSONDecodeError:
            invited_members = []
        
        # Get user profile to add owner's info
        user_profile = get_user_profile(user_id)
        owner_email = user_profile.get('email', '')
        owner_name = user_profile.get('display_name') or f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip()
        
        # Don't add invited members to the project yet - they need to accept first
        # Only the owner is initially a member
        
        # Create project data
        project_data = {
            'title': title,
            'description': description,
            'language': language,
            'owner_id': user_id,
            'owner_email': owner_email,
            'owner_name': owner_name,
            'members': [],  # Start with empty members list - users will be added when they accept
            'pending_invitations': [member.get('email') for member in invited_members if member.get('email')],  # Track pending invites
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now(),
            'code_content': '',  # Initial empty content
            'is_public': False,  # Default to private
        }
        
        # Create the project in Firebase
        project_id = create_code_project(project_data)
        
        # Send invitations to selected members
        invitation_count = 0
        failed_invitations = []
        
        for member in invited_members:
            try:
                username = member.get('username')
                if username:
                    create_project_invitation(
                        sender_id=user_id,
                        recipient_username=username,
                        project_id=project_id,
                        project_title=title,
                        project_description=description
                    )
                    invitation_count += 1
            except Exception as inv_error:
                print(f"Failed to send invitation to {username}: {str(inv_error)}")
                failed_invitations.append(username)
        
        # Create success message
        success_msg = f'Project "{title}" created successfully!'
        if invitation_count > 0:
            success_msg += f' {invitation_count} invitation(s) sent.'
        
        if failed_invitations:
            success_msg += f' Failed to invite: {", ".join(failed_invitations)}'
        
        # Add success message
        messages.success(request, success_msg)
        
        # Redirect to the project page or home
        return redirect('/codex-home/')
        
    except Exception as e:
        # Log the error
        print(f"Error creating project: {str(e)}")
        
        # Add error message
        messages.error(request, f'Error creating project: {str(e)}')
        
        # Redirect back to home page
        return redirect('/codex-home/')

def get_notifications(request):
    """
    Get notifications for the current user
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('/login/')
    
    try:
        notifications = get_user_notifications(user_id)
        unread_count = get_unread_notifications_count(user_id)
        
        return JsonResponse({
            'notifications': notifications,
            'unread_count': unread_count
        })
        
    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        return JsonResponse({'error': 'Failed to get notifications'}, status=500)

@csrf_exempt
def handle_invitation(request):
    """
    Handle invitation acceptance/decline
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        action = data.get('action')  # 'accept' or 'decline'
        
        if not notification_id or action not in ['accept', 'decline']:
            return JsonResponse({'error': 'Invalid parameters'}, status=400)
        
        # Update notification status
        status = 'accepted' if action == 'accept' else 'declined'
        success = update_notification_status(notification_id, status, user_id)
        
        if success:
            message = f'Invitation {"accepted" if action == "accept" else "declined"} successfully!'
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'error': 'Failed to update invitation'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Error handling invitation: {str(e)}")
        return JsonResponse({'error': 'Failed to handle invitation'}, status=500)

@csrf_exempt
def mark_notification_read(request):
    """
    Mark a notification as read
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return JsonResponse({'error': 'Notification ID required'}, status=400)
        
        success = update_notification_status(notification_id, 'read', user_id)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Failed to mark as read'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        return JsonResponse({'error': 'Failed to mark as read'}, status=500)