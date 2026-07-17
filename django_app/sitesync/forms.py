"""
Forms for runtime configuration.
"""

from django import forms

from .models import AppSettings


class SettingsForm(forms.ModelForm):
    """Form for editing app settings."""

    class Meta:
        model = AppSettings
        fields = [
            'electricity_benchmark_intensity',
            'gas_benchmark_intensity',
            'water_benchmark_intensity',
            'etainabl_api_url',
            'page_size',
            'api_timeout',
        ]
        widgets = {
            'electricity_benchmark_intensity': forms.NumberInput(attrs={'min': 0, 'step': '0.001'}),
            'gas_benchmark_intensity': forms.NumberInput(attrs={'min': 0, 'step': '0.001'}),
            'water_benchmark_intensity': forms.NumberInput(attrs={'min': 0, 'step': '0.001'}),
            'etainabl_api_url': forms.URLInput(attrs={'placeholder': 'https://api.etainabl.com/2.0'}),
            'page_size': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'api_timeout': forms.NumberInput(attrs={'min': 1, 'step': 1}),
        }

    def _clean_non_negative_decimal(self, field_name, label):
        value = self.cleaned_data[field_name]
        if value < 0:
            raise forms.ValidationError(f'{label} must be zero or greater.')
        return value

    def clean_electricity_benchmark_intensity(self):
        return self._clean_non_negative_decimal(
            'electricity_benchmark_intensity',
            'Electricity benchmark intensity',
        )

    def clean_gas_benchmark_intensity(self):
        return self._clean_non_negative_decimal(
            'gas_benchmark_intensity',
            'Gas benchmark intensity',
        )

    def clean_water_benchmark_intensity(self):
        return self._clean_non_negative_decimal(
            'water_benchmark_intensity',
            'Water benchmark intensity',
        )

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


class CapacityUploadForm(forms.Form):
    """Form for uploading available capacity reference files."""

    capacity_upload_file = forms.FileField(required=True)

    def clean_capacity_upload_file(self):
        upload = self.cleaned_data['capacity_upload_file']
        filename = (upload.name or '').lower()
        if not filename.endswith('.xlsx'):
            raise forms.ValidationError('Only .xlsx files are supported.')
        return upload
