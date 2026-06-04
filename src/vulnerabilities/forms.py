from django import forms
from django.db import models
from .models import Vulnerability, CustomUser, Team

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'leader', 'members', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'members': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If user is not an Admin, they cannot change the team leader
        if user and not user.is_admin_role:
            if 'leader' in self.fields:
                del self.fields['leader']
        else:
            # Admins can see/set the leader
            if 'leader' in self.fields:
                self.fields['leader'].queryset = CustomUser.objects.filter(role='TEAMLEADER')
                # Edit mode: show unassigned leaders OR the current leader
                if self.instance.pk:
                    self.fields['leader'].queryset = CustomUser.objects.filter(
                        models.Q(role='TEAMLEADER') & (models.Q(led_teams__isnull=True) | models.Q(led_teams=self.instance))
                    ).distinct()
                else:
                    self.fields['leader'].queryset = CustomUser.objects.filter(
                        models.Q(role='TEAMLEADER') & models.Q(led_teams__isnull=True)
                    ).distinct()
                self.fields['leader'].widget.attrs.update({'class': 'form-select'})
        
        # Filter members: 
        # 1. Must be Developer or Analyst
        # 2. Must not be in any other team (if editing, include current members)
        member_filter = models.Q(role__in=['DEVELOPER', 'ANALYST'])
        
        if self.instance.pk:
            # Edit mode: show unassigned users OR users already in this team
            self.fields['members'].queryset = CustomUser.objects.filter(
                member_filter & (models.Q(teams__isnull=True) | models.Q(teams=self.instance))
            ).distinct()
        else:
            # Create mode: show only unassigned users
            self.fields['members'].queryset = CustomUser.objects.filter(
                member_filter & models.Q(teams__isnull=True)
            ).distinct()

class VulnerabilityReportForm(forms.ModelForm):
    class Meta:
        model = Vulnerability
        fields = ['title', 'description', 'poc_screenshot']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class VulnerabilityManagementForm(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Add a comment about this update...'}), required=False)

    class Meta:
        model = Vulnerability
        fields = ['severity', 'status', 'developer_assignee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show Developers and Analysts
        self.fields['developer_assignee'].queryset = CustomUser.objects.filter(
            models.Q(role='DEVELOPER') | models.Q(role='ANALYST')
        )

class VulnerabilityCompleteForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Describe how you fixed this vulnerability...'}),
        label="Fix Comment",
        required=True
    )

class UserManagementForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False, help_text="Required for new users. Leave blank to keep current password if editing.")
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'job_title', 'phone_number', 'bio', 'address', 'profile_picture', 'is_active']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Determine if we are creating a new user
        is_creating = self.instance.pk is None
        
        # Fields that are mandatory on creation
        mandatory_fields = ['username', 'first_name', 'last_name', 'email', 'role', 'job_title']
        
        for field_name in mandatory_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        if is_creating:
            self.fields['password'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            # Sync Django Groups based on role
            from django.contrib.auth.models import Group
            role_to_group = {
                'ADMIN': 'Admins',
                'TEAMLEADER': 'Teamleaders',
                'DEVELOPER': 'Developers',
                'ANALYST': 'Analysts',
            }
            group_name = role_to_group.get(user.role)
            if group_name:
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.clear()
                user.groups.add(group)
        return user

class UserProfileForm(forms.ModelForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False, help_text="Required ONLY if you are changing your password.")
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False, help_text="Leave blank if you don't want to change your password.")
    confirm_new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'job_title', 'phone_number', 'bio', 'address', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')

        if new_password:
            # Password change requested
            if not old_password:
                self.add_error('old_password', "Current password is required to change your password.")
            elif not self.user.check_password(old_password):
                self.add_error('old_password', "Incorrect current password.")

            if new_password != confirm_new_password:
                self.add_error('confirm_new_password', "New passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user
