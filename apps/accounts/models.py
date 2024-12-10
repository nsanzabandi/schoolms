# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True,
        verbose_name=_('Profile Picture')
    )
    role = models.CharField(
        max_length=20, 
        choices=[
            ('admin', _('Admin')),
            ('staff', _('Staff')),
            ('teacher', _('Teacher')),
            ('student', _('Student'))
        ],
        verbose_name=_('Role')
    )
    is_active = models.BooleanField(
        _('active status'),
        default=False,
        help_text=_('Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.')
    )

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def is_student(self):
        return self.role == 'student'

    def get_profile_picture_url(self):
        """Safe method to get profile picture URL"""
        try:
            if self.profile_picture and hasattr(self.profile_picture, 'url'):
                return self.profile_picture.url
        except (ValueError, AttributeError):
            pass
        return None

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']