# community/urls.py

from django.urls import path
from .views import signup_view, login_view, signup_view, create_profile_view, edit_profile_view, profile_detail_view, start_thread_view, reply_message_view, thread_detail_view, apply_to_block_view, approve_application_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'), 
    path('profile/<int:pk>/', profile_detail_view, name='profile_detail'),
    path('profile/create/', create_profile_view, name='create_profile'),
    path('profile/<int:pk>/edit/', edit_profile_view, name='edit_profile'),
    path('start_thread/', start_thread_view, name='start_thread'),
    path('reply_message/<int:tid>/', reply_message_view, name='reply_message'),
    path('thread/<int:pk>/', thread_detail_view, name='thread_detail'),
    path('approve_application/<int:appid>/', approve_application_view, name='approve_application'),
    path('apply_to_block/', apply_to_block_view, name='apply_to_block'),
]