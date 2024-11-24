# apps/accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib import messages

class PasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.must_change_password:
                # Allowed URLs when password change is required
                allowed_urls = [
                    reverse('accounts:password_change'),
                    reverse('accounts:logout'),
                ]
                
                if request.path not in allowed_urls:
                    messages.warning(
                        request,
                        'You must change your password before continuing.'
                    )
                    return redirect('accounts:password_change')
        
        response = self.get_response(request)
        return response

class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.email_verified:
            # URLs that don't require email verification
            exempt_urls = [
                reverse('accounts:logout'),
                reverse('accounts:resend_verification'),
                reverse('accounts:password_change'),
                reverse('accounts:profile'),  # Allow access to profile
                '/admin/',  # Allow admin access
            ]
            
            # Add verify_email URL to exempt_urls if token exists
            if request.user.email_verification_token:
                try:
                    verify_url = reverse('accounts:verify_email', 
                                       kwargs={'token': request.user.email_verification_token})
                    exempt_urls.append(verify_url)
                except:
                    pass

            current_url = request.path
            is_exempt = any(
                current_url.startswith(exempt_url) 
                for exempt_url in exempt_urls
            )
            
            # Check if it's a verification URL
            try:
                current_url_name = resolve(current_url).url_name
                is_verification_url = current_url_name in ['verify_email', 'profile']
            except:
                is_verification_url = False

            if not is_exempt and not is_verification_url:
                messages.warning(
                    request,
                    'Please verify your email address to access all features.'
                )
                return redirect('accounts:profile')
        
        response = self.get_response(request)
        return response