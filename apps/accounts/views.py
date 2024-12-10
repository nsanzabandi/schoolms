# apps/accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.conf import settings
from decouple import config
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib import messages
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.contrib import messages
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User
from .tokens import account_activation_token

import os

# Dashboard Views
@login_required
def dashboard(request):
    """Main dashboard view with different displays for staff and regular users."""
    if request.user.is_staff:
        context = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'pending_activations': User.objects.filter(is_active=False).count(),
        }
        return render(request, 'accounts/admin_dashboard.html', context)
    return render(request, 'accounts/user_dashboard.html')

# Authentication Views
def register(request):
    """Handle user registration with email verification."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create inactive user
                user = form.save(commit=False)
                user.is_active = False
                user.save()

                # Prepare activation email
                current_site = get_current_site(request)
                mail_subject = 'Activate Your Account'
                html_message = render_to_string('accounts/email/activation_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'protocol': 'https' if request.is_secure() else 'http',
                })

                # Send activation email using SendGrid
                try:
                    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
                    email = Mail(
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to_emails=user.email,
                        subject=mail_subject,
                        html_content=html_message,
                    )
                    response = sg.send(email)
                    print(f"SendGrid API response status code: {response.status_code}")  # Debug log

                    if response.status_code == 202:  # SendGrid success status code
                        messages.success(request, 'Please check your email to complete registration.')
                        return redirect('accounts:login')
                    else:
                        raise Exception(f"SendGrid API returned status code {response.status_code}")

                except Exception as e:
                    print(f"Email sending error: {e}")  # Debug log
                    user.delete()  # Clean up user if email fails
                    messages.error(request, 'Error sending activation email. Please try again.')
                    return render(request, 'accounts/register.html', {'form': form})

            except Exception as e:
                print(f"Registration error: {e}")  # Debug log
                form.add_error(None, str(e))
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

def activation_sent(request):
    """Display message after sending activation email."""
    return render(request, 'accounts/email/activation_sent.html')

def activate(request, uidb64, token):
    """Handle account activation from email link."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully!')
        return redirect('accounts:password_reset')
    
    messages.error(request, 'Activation link is invalid or has expired!')
    return redirect('accounts:login')

# Profile Management Views
@login_required
def profile(request):
    """Handle user profile updates."""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def change_password(request):
    """Handle password changes."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

# User Management Views (Staff Only)
@staff_member_required
def user_management(request):
    """Display and filter user list for staff members."""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.all()
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
        
    if status_filter:
        is_active = status_filter == 'active'
        users = users.filter(is_active=is_active)
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'accounts/user_management.html', context)

@staff_member_required
def edit_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if request.method == 'POST':
            form = CustomUserChangeForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                if form.cleaned_data['profile_picture']:
                    user.profile_picture = form.cleaned_data['profile_picture']
                user.save()
                messages.success(request, f'User {user.username} has been updated.')
                return redirect('accounts:users')
        else:
            form = CustomUserChangeForm(instance=user)
        return render(request, 'accounts/edit_user.html', {
            'form': form,
            'user_obj': user,
            'has_profile_picture': bool(user.profile_picture)
        })
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:users')

@staff_member_required
def toggle_user_status(request, user_id):
    """Allow staff to activate/deactivate users."""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            if user != request.user:  # Prevent self-deactivation
                user.is_active = not user.is_active
                user.save()
                status = 'activated' if user.is_active else 'deactivated'
                messages.success(request, f'User {user.username} has been {status}.')
            else:
                messages.error(request, 'You cannot change your own status.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return redirect('accounts:users')

# Password reset view
class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/email/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        try:
            # Generate the password reset email
            user = form.get_user()
            current_site = get_current_site(self.request)
            mail_subject = 'Reset Your Password'
            html_message = render_to_string('accounts/email/password_reset_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if self.request.is_secure() else 'http',
            })

            # Send the password reset email using SendGrid
            sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            email = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=user.email,
                subject=mail_subject,
                html_content=html_message,
            )
            response = sg.send(email)

            if response.status_code == 202:
                messages.success(self.request, 'Please check your email to reset your password.')
            else:
                messages.error(self.request, 'Error sending password reset email. Please try again.')

        except Exception as e:
            messages.error(self.request, 'Error sending password reset email. Please try again.')

        return super().form_valid(form)
    
# Reset confirmation

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Your password has been reset successfully.')
            return redirect('accounts:login')

        # Generate the plain-text password reset email
        text_message = render_to_string('accounts/email/password_reset_email.txt', {
            'user': user,
            'domain': request.get_host(),
            'protocol': 'https' if request.is_secure() else 'http',
        })

        # Send the password reset email using SendGrid
        try:
            sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            email = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=user.email,
                subject='Reset Your Password',
                text_content=text_message,
            )
            response = sg.send(email)

            if response.status_code == 202:
                messages.success(request, 'Please check your email to reset your password.')
            else:
                messages.error(request, 'Error sending password reset email. Please try again.')

        except Exception as e:
            messages.error(request, 'Error sending password reset email. Please try again.')

        return render(request, 'accounts/password_reset_confirm.html')
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('accounts:password_reset')

# Delete a user
@staff_member_required
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if user != request.user:
            user.delete()
            messages.success(request, f'User {user.username} has been deleted.')
        else:
            messages.error(request, 'You cannot delete your own account.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    return redirect('accounts:users')
