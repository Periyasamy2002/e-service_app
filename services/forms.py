from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Service, ServiceRequest

class UserRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role']

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'charges', 'documents_required', 'tutorial_link', 'apply_link', 'page']

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['service', 'description']