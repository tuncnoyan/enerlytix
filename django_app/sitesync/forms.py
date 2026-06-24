"""
Forms for runtime configuration.
"""

from django import forms
from .models import AppSettings


class SettingsForm(forms.ModelForm):
    """Form for editing app settings."""

    class Meta:
        model = AppSettings
        fields = ['etainabl_api_url', 'page_size', 'api_timeout']
        widgets = {
            'etainabl_api_url': forms.URLInput(attrs={'placeholder': 'https://api.etainabl.com/2.0'}),
            'page_size': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'api_timeout': forms.NumberInput(attrs={'min': 1, 'step': 1}),
        }

    def clean_page_size(self):
        page_size = self.cleaned_data['page_size']
        if page_size < 1:
            raise forms.ValidationError('Page size must be at least 1.')
        return page_size

    def clean_api_timeout(self):
        api_timeout = self.cleaned_data['api_timeout']
        if api_timeout < 1:
            raise forms.ValidationError('API timeout must be at least 1 second.')
        return api_timeout
