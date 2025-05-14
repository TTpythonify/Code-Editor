from django.urls import path
from .views import *
from .view_codex import *


urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('', landing_page, name='landing_page'),
    path("logout/", logout_view, name="logout"),



    path("codex-home/", codex_home_page, name="codex_home_page"),



]