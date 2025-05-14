from django.shortcuts import render,redirect
from .firebase import *



def codex_home_page(request):
    current_user = request.session.get("user_id")

    # Check if user_id is missing
    if not current_user:
        return redirect('/login/')  # Or another appropriate page

    try:
        user_profile = get_user_profile(current_user)

        # Make sure 'username' exists in the profile
        username = user_profile.get('username', 'User')

        return render(
            request, 
            "codex/codex_home_page.html", 
            {'name': username.upper()}
        )

    except Exception as e:
        # Log the error (optional) and handle gracefully
        print(f"Error loading user profile: {e}")
        return render(
            request, 
            "codex/codex_home_page.html", 
            {'name': 'Guest'}
        )
