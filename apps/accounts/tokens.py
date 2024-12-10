from django.contrib.auth.tokens import PasswordResetTokenGenerator
import hashlib

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        login_timestamp = user.last_login.timestamp() if user.last_login else ''
        activation_key = f"{user.pk}{timestamp}{user.is_active}{login_timestamp}{user.email}"
        return hashlib.sha256(activation_key.encode()).hexdigest()

account_activation_token = AccountActivationTokenGenerator()