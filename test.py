from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from django.conf import settings

class EmailVerificationTestCase(TestCase):
    def setUp(self):
        # Configure test email backend
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.registration_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'testpassword123!',  # Make sure this meets password requirements
            'password2': 'testpassword123!'
        }

    def test_email_verification(self):
        # Clear the outbox before the test
        mail.outbox = []

        # Submit registration
        response = self.client.post(
            reverse('accounts:register'),
            self.registration_data
        )

        # Check redirect to login page
        self.assertRedirects(response, reverse('accounts:login'))

        # Check that exactly one email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Verify email content
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.registration_data['email']])
        self.assertIn('Verify your email', email.subject)

        # Extract verification token from email
        token = email.body.split('verify-email/')[1].split('/')[0]

        # Use token to verify email
        response = self.client.get(reverse('accounts:verify_email', args=[token]))
        self.assertRedirects(response, reverse('accounts:login'))

        # Check that user is now active and verified
        User = get_user_model()
        user = User.objects.get(email=self.registration_data['email'])
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)