import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.core.mail import send_mail

send_mail(
    subject='Test SendGrid',
    message='Test email body',
    from_email='danielnsanzabandi@gmail.com',
    recipient_list=['nsanzabandidani@gmail.com'],
    fail_silently=False,
)