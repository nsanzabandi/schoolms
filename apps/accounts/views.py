from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.contrib import messages
from django.views.generic import View, UpdateView, TemplateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.conf import settings
from django.db.models import Q

from .forms import (
    UserRegistrationForm, 
    UserUpdateForm, 
    CustomPasswordChangeForm,
    CustomPasswordResetForm, 
    StaffCreationForm
)
from .utils import send_verification_email, generate_verification_token, send_credentials_email

User = get_user_model()

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    login_url = 'accounts:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Different querysets based on user type
        if user.user_type == User.UserType.ADMIN:
            context['users'] = User.objects.all().order_by('-date_joined')
        else:
            context['users'] = User.objects.filter(pk=user.pk)

        # Add counts and stats
        context['total_users'] = User.objects.count()
        context['total_staff'] = User.objects.filter(user_type=User.UserType.STAFF).count()
        context['total_admins'] = User.objects.filter(user_type=User.UserType.ADMIN).count()
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        context['unverified_users'] = User.objects.filter(email_verified=False).count()

        return context

class SignUpView(View):
    template_name = 'accounts/signup.html'
    form_class = UserRegistrationForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(user, request)
            messages.success(
                request,
                'Registration successful. Please check your email to verify your account.'
            )
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})

class EmailVerificationView(View):
    def get(self, request, token):
        user = get_object_or_404(User, email_verification_token=token)
        
        if not user.email_verified:
            user.email_verified = True
            user.email_verification_token = ''  # Clear token after use
            user.save()
            messages.success(request, 'Your email has been verified. You can now login.')
        else:
            messages.info(request, 'Your email was already verified.')
        
        return redirect('accounts:login')

class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'accounts/profile.html'
    form_class = UserUpdateForm
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email_not_verified'] = not self.request.user.email_verified
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.must_change_password:
            self.request.user.must_change_password = False
            self.request.user.save()
        messages.success(self.request, 'Your password has been changed successfully.')
        return response

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

class CustomPasswordResetView(PasswordResetView):
    email_template_name = 'accounts/email/password_reset_email.html'
    subject_template_name = 'accounts/email/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    html_email_template_name = 'accounts/email/password_reset_email.html'
    from_email = settings.DEFAULT_FROM_EMAIL
    form_class = CustomPasswordResetForm
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            'If an account exists with the provided email, you will receive password reset instructions.'
        )
        return super().form_valid(form)

class StaffManagementView(UserPassesTestMixin, View):
    template_name = 'accounts/staff_management.html'
    login_url = 'accounts:login'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == User.UserType.ADMIN

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')

    def get(self, request):
        staff_users = User.objects.filter(user_type=User.UserType.STAFF)
        form = StaffCreationForm(initial={'is_admin_creating': True})
        return render(request, self.template_name, {
            'staff_users': staff_users,
            'form': form
        })

    def post(self, request):
        form = StaffCreationForm(request.POST, initial={'is_admin_creating': True})
        if form.is_valid():
            user = form.save(commit=False)
            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()
            
            try:
                send_credentials_email(user, password, request)
                messages.success(
                    request, 
                    f'Staff account created for {user.email}. Credentials have been sent to their email.'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'Account created but failed to send email. Please manage credentials manually.'
                )
            return redirect('accounts:staff_management')
        
        staff_users = User.objects.filter(user_type=User.UserType.STAFF)
        return render(request, self.template_name, {
            'staff_users': staff_users,
            'form': form
        })

class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('accounts:login')

    def post(self, request):
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('accounts:login')

@login_required
def resend_verification_email(request):
    if not request.user.email_verified:
        token = generate_verification_token()
        request.user.email_verification_token = token
        request.user.save()
        
        try:
            send_verification_email(request.user, request)
            messages.success(request, 'Verification email has been sent.')
        except Exception as e:
            messages.error(request, 'Failed to send verification email. Please try again later.')
    else:
        messages.info(request, 'Your email is already verified.')
    
    return redirect('accounts:profile')