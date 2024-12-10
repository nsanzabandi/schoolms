# apps/accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('register/', views.register, name='register'),
    
    # User Management
    path('users/', views.user_management, name='users'),  # Changed to 'users'
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    
    # Profile & Password
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Activation
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('activation-sent/', views.activation_sent, name='activation_sent'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset_form.html',
             email_template_name='accounts/email/password_reset_email.txt',
             subject_template_name='accounts/email/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]