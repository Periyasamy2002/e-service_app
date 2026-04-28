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
        fields = [
            'full_name', 'dob', 'email', 'address', 'mobile', 
            'aadhaar_number', 'photo', 'aadhaar_card', 'pan_card', 
            'signature', 'address_proof', 'description'
        ]

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile and (not mobile.isdigit() or len(mobile) != 10):
            raise forms.ValidationError("Mobile number must be 10 digits.")
        return mobile

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number')
        if aadhaar:
            # Remove spaces and validate length
            aadhaar = aadhaar.replace(' ', '')
            if not aadhaar.isdigit() or len(aadhaar) != 12:
                raise forms.ValidationError("Aadhaar number must be 12 digits.")
        return aadhaar