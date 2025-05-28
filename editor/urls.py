from django.urls import path
from .views import *
from .view_codex import *


urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('', landing_page, name='landing_page'),
    path("logout/", logout_view, name="logout"),



    path("codex-home/", codex_home_page, name="codex_home_page"),
    path("create-project/", create_project, name="create_project"),

    path('search-users/', search_users, name='search_users'),
    
    # Notification management
    path('notifications/', get_notifications, name='get_notifications'),
    path('handle-invitation/', handle_invitation, name='handle_invitation'),
    path('mark-notification-read/', mark_notification_read, name='mark_notification_read'),


]