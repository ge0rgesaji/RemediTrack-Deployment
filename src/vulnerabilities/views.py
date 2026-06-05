from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.db import models
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from .models import Vulnerability, CustomUser, VulnerabilityComment, Team
from .forms import (
    VulnerabilityReportForm, 
    VulnerabilityManagementForm, 
    UserManagementForm, 
    VulnerabilityCompleteForm,
    UserProfileForm,
    TeamForm
)

@login_required
def dashboard(request):
    user = request.user
    # A user is unassigned if they are not an Admin AND not in any Django Group 
    # AND not in any custom Team (as member) AND not leading any Team.
    is_unassigned = (
        not user.is_admin_role and 
        not user.groups.exists() and 
        not user.teams.exists() and 
        not user.led_teams.exists()
    )

    if is_unassigned:
        vulnerabilities = Vulnerability.objects.none()
    elif user.is_developer_role:
        # Developers, Teamleaders, and Admins can view all vulnerabilities
        vulnerabilities = Vulnerability.objects.all().order_by('-created_at')
    else:
        # Analysts and others see vulnerabilities they are involved in, 
        # or those reported by members of their teams.
        vulnerabilities = Vulnerability.objects.filter(
            models.Q(reporter=user) | 
            models.Q(developer_assignee=user) |
            models.Q(comments__author=user) |
            models.Q(reporter__teams__in=user.teams.all())
        ).distinct().order_by('-created_at')
    
    return render(request, 'vulnerabilities/dashboard.html', {
        'vulnerabilities': vulnerabilities,
        'is_unassigned': is_unassigned
    })

@method_decorator(ratelimit(key='user', rate='10/m', method='POST', block=True), name='post')
class VulnerabilityCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Vulnerability
    form_class = VulnerabilityReportForm
    template_name = 'vulnerabilities/report_form.html'
    success_url = reverse_lazy('dashboard')
    raise_exception = True

    def test_func(self):
        # Only the Analyst role is allowed to report vulnerabilities
        return self.request.user.role == 'ANALYST'

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        # Set reporting team if user is in any team
        if self.request.user.teams.exists():
            form.instance.reporting_team = self.request.user.teams.first()
        return super().form_valid(form)

class VulnerabilityDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Vulnerability
    template_name = 'vulnerabilities/detail.html'
    context_object_name = 'vulnerability'

    def test_func(self):
        vulnerability = self.get_object()
        user = self.request.user
        return (
            user.is_developer_role or 
            vulnerability.reporter == user or 
            vulnerability.developer_assignee == user or
            vulnerability.comments.filter(author=user).exists()
        )

class VulnerabilityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Vulnerability
    form_class = VulnerabilityManagementForm
    template_name = 'vulnerabilities/manage_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        vulnerability = self.get_object()
        return self.request.user.role == 'TEAMLEADER' and vulnerability.status != 'CLOSED'

    def form_valid(self, form):
        response = super().form_valid(form)
        comment_text = form.cleaned_data.get('comment')
        if comment_text:
            VulnerabilityComment.objects.create(
                vulnerability=self.object,
                author=self.request.user,
                text=comment_text
            )
        return response

class VulnerabilityCompleteView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = VulnerabilityComment
    form_class = VulnerabilityCompleteForm
    template_name = 'vulnerabilities/complete_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        vulnerability = get_object_or_404(Vulnerability, pk=self.kwargs['pk'])
        return self.request.user == vulnerability.developer_assignee

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vulnerability'] = get_object_or_404(Vulnerability, pk=self.kwargs['pk'])
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Remove 'instance' because VulnerabilityCompleteForm is a plain forms.Form, not ModelForm
        if 'instance' in kwargs:
            del kwargs['instance']
        return kwargs

    def form_valid(self, form):
        vulnerability = get_object_or_404(Vulnerability, pk=self.kwargs['pk'])
        user = self.request.user
        
        # Determine status based on role
        if user.role == 'DEVELOPER':
            vulnerability.status = 'FIXED'
        elif user.role == 'ANALYST':
            vulnerability.status = 'MITIGATED'
        
        vulnerability.save()
        
        VulnerabilityComment.objects.create(
            vulnerability=vulnerability,
            author=user,
            text=form.cleaned_data['comment']
        )
        return redirect(self.success_url)

# User Management Views
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin_role

class TeamleaderRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_teamleader_role

class UserListView(LoginRequiredMixin, TeamleaderRequiredMixin, ListView):
    model = CustomUser
    template_name = 'vulnerabilities/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_role:
            return CustomUser.objects.all()
        # Teamleaders only see members of teams they lead
        return CustomUser.objects.filter(teams__leader=user).distinct()

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = CustomUser
    form_class = UserManagementForm
    template_name = 'vulnerabilities/user_form.html'
    success_url = reverse_lazy('user_list')

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserManagementForm
    template_name = 'vulnerabilities/user_form.html'
    success_url = reverse_lazy('user_list')

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'vulnerabilities/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'vulnerabilities/user_form.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        # Re-authenticate the user to prevent logout after password change
        update_session_auth_hash(self.request, self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_profile_edit'] = True
        return context

class UserPublicProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'vulnerabilities/public_profile.html'
    context_object_name = 'profile_user'

# Team Management Views
class TeamListView(LoginRequiredMixin, TeamleaderRequiredMixin, ListView):
    model = Team
    template_name = 'vulnerabilities/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_role:
            return Team.objects.all()
        return Team.objects.filter(leader=user)

class TeamDetailView(LoginRequiredMixin, TeamleaderRequiredMixin, DetailView):
    model = Team
    template_name = 'vulnerabilities/team_detail.html'
    context_object_name = 'team'

    def test_func(self):
        user = self.request.user
        if user.is_admin_role:
            return True
        team = self.get_object()
        return team.leader == user

class TeamCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'vulnerabilities/team_form.html'
    success_url = reverse_lazy('team_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class TeamUpdateView(LoginRequiredMixin, TeamleaderRequiredMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = 'vulnerabilities/team_form.html'
    success_url = reverse_lazy('team_list')

    def test_func(self):
        user = self.request.user
        if user.is_admin_role:
            return True
        team = self.get_object()
        return team.leader == user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class TeamDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Team
    template_name = 'vulnerabilities/team_confirm_delete.html'
    success_url = reverse_lazy('team_list')

from django.http import HttpResponse
from django.db import connections
from django.db.utils import OperationalError

def health_check(request):
    try:
        connections['default'].cursor()
    except OperationalError:
        return HttpResponse("Database unreachable", status=503)
    return HttpResponse("OK", status=200)
