from django.urls import path
from .views import *


urlpatterns = [
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('home/', home_page, name='home_page'),

]