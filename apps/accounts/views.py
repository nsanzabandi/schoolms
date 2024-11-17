from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.utils.crypto import get_random_string
from .forms import UserRegistrationForm, UserUpdateForm
from .models import User
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.email_verified:
                    login(request, user)
                    messages.success(request, f'Welcome back, {username}!')
                    return redirect('accounts:dashboard')
                else:
                    messages.warning(request, 'Please verify your email before logging in.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user but don't save yet
            user = form.save(commit=False)
            user.is_active = False  # User starts inactive
            user.email_verified = False  # Email starts unverified
            
            # Generate verification token
            user.email_verification_token = get_random_string(64)
            user.save()

            # Send verification email
            if send_verification_email(request, user):
                messages.success(
                    request, 
                    'Registration successful. Please check your email to verify your account.'
                )
            else:
                # If email sending fails, delete the user and show error
                user.delete()
                messages.error(
                    request, 
                    'Registration failed. Could not send verification email. Please try again.'
                )
                return render(request, 'accounts/register.html', {'form': form})
                
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def verify_email(request, token):
    try:
        user = User.objects.get(email_verification_token=token)
        if not user.email_verified:
            user.email_verified = True
            user.is_active = True
            user.email_verification_token = ''  # Clear the token after use
            user.save()
            messages.success(request, 'Email verified successfully. You can now login.')
        else:
            messages.info(request, 'Email already verified. You can login.')
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
    
    return redirect('accounts:login')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:login')

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/update_profile.html', {'form': form})

def send_verification_email(request, user):
    """
    Send verification email to user with verification link.
    Returns True if email was sent successfully, False otherwise.
    """
    try:
        # Generate verification URL with token
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', args=[user.email_verification_token])
        )

        # Prepare email context
        context = {
            'user': user,
            'verification_url': verification_url,
        }

        # Render email templates
        html_message = render_to_string('accounts/email/verify_email.html', context)
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject='Verify your email address',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Verification email sent successfully to {user.email}")
        return True

    except BadHeaderError:
        logger.error(f"Invalid header found in verification email for {user.email}")
        return False
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

def resend_verification_email(request):
    """
    Resend verification email if user hasn't verified their email yet.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, email_verified=False)
            
            # Generate new verification token
            user.email_verification_token = get_random_string(64)
            user.save()
            
            if send_verification_email(request, user):
                messages.success(request, 'Verification email has been resent. Please check your inbox.')
            else:
                messages.error(request, 'Failed to resend verification email. Please try again later.')
        except User.DoesNotExist:
            messages.error(request, 'No unverified account found with this email address.')
    
    return redirect('accounts:login')

def password_reset_confirm(request, token):
    """
    Confirm password reset using token.
    """
    try:
        user = User.objects.get(password_reset_token=token)
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password1'])
                user.password_reset_token = ''  # Clear the token
                user.save()
                messages.success(request, 'Password has been reset successfully. You can now login.')
                return redirect('accounts:login')
        else:
            form = PasswordResetConfirmForm()
        
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    except User.DoesNotExist:
        messages.error(request, 'Invalid password reset token.')
        return redirect('accounts:login')