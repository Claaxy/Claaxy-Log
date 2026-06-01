from django import forms

from apps.users.models import AllowedUser, get_user_module_admin_email


class AllowedUserForm(forms.ModelForm):
    class Meta:
        model = AllowedUser
        fields = ['name', 'google_email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'google_email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'name@gmail.com'},
            ),
        }

    def clean_google_email(self):
        email = (self.cleaned_data.get('google_email') or '').strip().lower()
        if email == get_user_module_admin_email():
            raise forms.ValidationError('The admin account is always allowed and cannot be added here.')
        if AllowedUser.objects.filter(google_email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This Google account is already on the list.')
        return email
