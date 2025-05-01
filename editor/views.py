from django.shortcuts import render
from django.http import HttpResponse




def home_page(request):
    return render(request, "editor/home_page.html")


def login_view(request):
    # This is a placeholder for the actual login logic
    # You'll need to implement the authentication here
    if request.method == 'POST':
        # Process the login form
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f" Hi my name is {username} and my password is {password} ")
        return render(request, 'editor/home_page.html', {
            'name': username
        })
    
    # If GET request, just show the login form
    return render(request, 'editor/login.html')




def signup_view(request):
    # This is a placeholder for the actual signup logic
    # You'll need to implement user creation here
    if request.method == 'POST':
        # Process the signup form
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Here you would create the user
        # If signup successful, redirect to login or home
        # return redirect('login')
        
        # For now, just render the page with an error message
        return render(request, 'editor/signup.html', {
            'error_message': 'Could not create account. (This is a placeholder message)',
        })
    
    # If GET request, just show the signup form
    return render(request, 'editor/signup.html')