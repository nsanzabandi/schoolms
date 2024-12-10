from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text='Required. Enter a valid email address.'
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        help_text='Required. Enter your first name.'
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        help_text='Required. Enter your last name.'
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required except profile_picture
        for field_name, field in self.fields.items():
            if field_name != 'profile_picture':
                field.required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email

class CustomUserChangeForm(UserChangeForm):
    password = None  # Remove password field from form
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'profile_picture')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True