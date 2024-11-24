from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, PasswordResetForm
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.email_verification_token = get_random_string(100)
        user.must_change_password = True
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True  # Email cannot be changed directly

class CustomPasswordChangeForm(PasswordChangeForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.must_change_password = False  # Reset the flag when password is changed
        if commit:
            user.save()
        return user

class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset."""
        return User.objects.filter(email=email, is_active=True)

class StaffCreationForm(UserRegistrationForm):
    class Meta(UserRegistrationForm.Meta):
        model = User
        fields = UserRegistrationForm.Meta.fields + ('user_type',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].initial = User.UserType.STAFF
        if not kwargs.get('initial', {}).get('is_admin_creating'):
            self.fields['user_type'].disabled = True