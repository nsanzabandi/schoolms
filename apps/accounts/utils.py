# apps/accounts/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings

def send_verification_email(user, request=None):
    """Send email verification link to user"""
    subject = render_to_string('accounts/email/email_verification_subject.txt').strip()
    
    if request:
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'token': user.email_verification_token})
        )
    else:
        verification_url = f"{settings.SITE_URL}{reverse('accounts:verify_email', kwargs={'token': user.email_verification_token})}"
    
    context = {
        'user': user,
        'verification_url': verification_url
    }
    
    html_message = render_to_string('accounts/email/verification_email.html', context)
    plain_message = render_to_string('accounts/email/verification_email_plain.txt', context)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_credentials_email(user, password, request=None):
    """Send initial credentials to new staff members"""
    subject = render_to_string('accounts/email/staff_credentials_subject.txt').strip()
    
    if request:
        login_url = request.build_absolute_uri(reverse('accounts:login'))
    else:
        login_url = f"{settings.SITE_URL}{reverse('accounts:login')}"
    
    context = {
        'user': user,
        'password': password,
        'login_url': login_url
    }
    
    html_message = render_to_string('accounts/email/credentials_email.html', context)
    plain_message = render_to_string('accounts/email/credentials_email_plain.txt', context)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def generate_verification_token():
    """Generate a random token for email verification"""
    from django.utils.crypto import get_random_string
    return get_random_string(100)