# apps/accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings

class PasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            exempt_urls = [
                reverse('accounts:logout'),
                reverse('accounts:change_password'),
                reverse('accounts:password_reset'),
                reverse('accounts:password_reset_done'),
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': 'dummy', 'token': 'dummy'}).split('/dummy/')[0],
                reverse('accounts:password_reset_complete'),
            ]
            
            # Check if user needs to change password
            if hasattr(request.user, 'password_change_required') and request.user.password_change_required:
                if not any(request.path.startswith(url) for url in exempt_urls):
                    messages.warning(request, 'Please change your password to continue.')
                    return redirect('accounts:change_password')
        
        response = self.get_response(request)
        return response

class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            exempt_urls = [
                reverse('accounts:logout'),
                reverse('accounts:activation_sent'),
                reverse('admin:index'),  # Allow access to admin
                # Add any other exempt URLs here
            ]
            
            # Check if email verification is required
            if not request.user.is_active and not any(request.path.startswith(url) for url in exempt_urls):
                messages.warning(request, 'Please verify your email address to continue.')
                return redirect('accounts:activation_sent')
        
        response = self.get_response(request)
        return response