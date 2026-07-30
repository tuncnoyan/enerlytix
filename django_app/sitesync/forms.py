"""
Forms for runtime configuration and user-management workflows.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone as dj_timezone

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
            'invoice_page_limit',
            'invoice_start_page',
        ]
        widgets = {
            'electricity_benchmark_intensity': forms.NumberInput(attrs={'min': 0, 'step': '0.001'}),
            'gas_benchmark_intensity': forms.NumberInput(attrs={'min': 0, 'step': '0.001'}),
            'water_benchmark_intensity': forms.NumberInput(attrs={'min': 0, 'step': '0.001'}),
            'etainabl_api_url': forms.URLInput(attrs={'placeholder': 'https://api.etainabl.com/2.0'}),
            'page_size': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'api_timeout': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'invoice_page_limit': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'invoice_start_page': forms.NumberInput(attrs={'min': 1, 'step': 1}),
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

    def clean_invoice_page_limit(self):
        invoice_page_limit = self.cleaned_data['invoice_page_limit']
        if invoice_page_limit < 1:
            raise forms.ValidationError('Invoice data page limit must be at least 1.')
        return invoice_page_limit

    def clean_invoice_start_page(self):
        invoice_start_page = self.cleaned_data['invoice_start_page']
        if invoice_start_page < 1:
            raise forms.ValidationError('Invoice data start page number must be at least 1.')
        return invoice_start_page


class CapacityUploadForm(forms.Form):
    """Form for uploading available capacity reference files."""

    capacity_upload_file = forms.FileField(required=True)

    def clean_capacity_upload_file(self):
        upload = self.cleaned_data['capacity_upload_file']
        filename = (upload.name or '').lower()
        if not filename.endswith('.xlsx'):
            raise forms.ValidationError('Only .xlsx files are supported.')
        return upload


class InvitationForm(forms.Form):
    """Create a pending invitation for a new user."""

    email = forms.EmailField(required=True)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class AccountActionForm(forms.Form):
    """Supports simple account-state changes for a selected user."""

    action = forms.ChoiceField(
        choices=[
            ('enable', 'Enable account'),
            ('disable', 'Disable account'),
            ('reset_password', 'Reset password'),
            ('delete', 'Delete account'),
        ],
        required=True,
    )
    new_username = forms.CharField(required=False)

    def clean_new_username(self):
        value = (self.cleaned_data.get('new_username') or '').strip()
        if value:
            return value
        return value


class TeamForm(forms.Form):
    """Form for creating and editing teams."""

    from .models import Team, RoleAssignment

    name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Team name',
        }),
        help_text='Display name for the team'
    )
    level = forms.IntegerField(
        required=False,
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'step': 1,
        }),
        help_text='Hierarchy level (root teams should be level 1)'
    )
    parent_team = forms.ModelChoiceField(
        queryset=Team.objects.all(),
        required=False,
        empty_label='Root team (no parent)',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Parent team for hierarchical structure'
    )
    manager = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_active=True),
        required=False,
        empty_label='No manager assigned',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='User to assign as team manager'
    )
    team_lead = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_active=True),
        required=False,
        empty_label='No team lead assigned',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='User to assign as team lead'
    )

    def clean(self):
        """Validate team level alignment with parent selection."""
        cleaned_data = super().clean()
        level = cleaned_data.get('level') or 1
        parent_team = cleaned_data.get('parent_team')
        cleaned_data['level'] = level

        if parent_team:
            expected_level = parent_team.level + 1
            if level != expected_level:
                self.add_error(
                    'level',
                    f'Level must be {expected_level} when parent team is "{parent_team.name}".'
                )
        elif level != 1:
            self.add_error('level', 'Root teams must be level 1.')

        return cleaned_data


class UserTeamAssignmentForm(forms.Form):
    """Form for assigning a user to a team."""

    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='User to assign to the team'
    )
    team = forms.ModelChoiceField(
        queryset=None,  # Will be set dynamically
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Team to assign the user to'
    )

    def __init__(self, *args, **kwargs):
        from .models import Team
        super().__init__(*args, **kwargs)
        self.fields['team'].queryset = Team.objects.all()


class RoleAssignmentForm(forms.Form):
    """Form for assigning roles to users."""

    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='User to assign the role to'
    )
    role_name = forms.ChoiceField(
        choices=[
            ('admin', 'Administrator'),
            ('manager', 'Manager'),
            ('team_lead', 'Team Lead'),
            ('user', 'User'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Role to assign to the user'
    )


class AuditLogFilterForm(forms.Form):
    """Validate and normalize admin audit filter query parameters."""

    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.order_by('username'),
        required=False,
        empty_label='All users',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    keyword = forms.CharField(max_length=200, required=False)
    start = forms.DateTimeField(required=False)
    end = forms.DateTimeField(required=False)
    action_type = forms.CharField(max_length=64, required=False)

    def clean_keyword(self):
        return (self.cleaned_data.get('keyword') or '').strip()

    def clean_action_type(self):
        return (self.cleaned_data.get('action_type') or '').strip()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start')
        end = cleaned.get('end')

        if start and dj_timezone.is_naive(start):
            cleaned['start'] = dj_timezone.make_aware(start, dj_timezone.utc)
        if end and dj_timezone.is_naive(end):
            cleaned['end'] = dj_timezone.make_aware(end, dj_timezone.utc)

        if cleaned.get('start') and cleaned.get('end') and cleaned['start'] > cleaned['end']:
            self.add_error('end', 'End date must be greater than or equal to start date.')

        return cleaned
