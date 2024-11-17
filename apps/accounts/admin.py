from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import UserRegistrationForm, UserUpdateForm

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = UserRegistrationForm
    form = UserUpdateForm
    model = User
    list_display = ('username', 'email', 'user_type', 'is_active', 'email_verified')
    list_filter = ('user_type', 'is_active', 'email_verified')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 
                                    'phone_number')}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'email_verified',
                                  'is_staff', 'is_superuser', 'groups', 
                                  'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
