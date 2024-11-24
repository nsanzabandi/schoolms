from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('', views.DashboardView.as_view(), name='dashboard'),  # Root URL

    # Authentication URLs
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True,
        next_page='accounts:dashboard'
    ), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Email Verification
    path('verify-email/<str:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),

    # Password Management
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Profile Management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileView.as_view(), name='profile_update'),

    # Staff Management (Admin only)
    path('staff/', views.StaffManagementView.as_view(), name='staff_management'),
]