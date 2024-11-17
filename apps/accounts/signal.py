from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from django.core.mail import send_mail
from django.conf import settings
import uuid

@receiver(post_save, sender=User)
def send_email_verification(sender, instance, created, **kwargs):
    if created:
        # Generate a unique token for email verification
        instance.email_verification_token = str(uuid.uuid4())
        instance.save()

        # Send the email verification email
        subject = 'Verify your email'
        message = f'Please click the following link to verify your email: {settings.SITE_URL}/accounts/verify/{instance.email_verification_token}/'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)