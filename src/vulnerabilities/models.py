from django.contrib.auth.models import AbstractUser, Group
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('TEAMLEADER', 'Teamleader'),
        ('DEVELOPER', 'Developer'),
        ('ANALYST', 'Analyst'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='ANALYST')
    
    # Optional Profile Fields
    job_title = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.role})" if full_name else f"{self.username} ({self.role})"

    @property
    def is_admin_role(self):
        return self.role == 'ADMIN' or self.is_superuser

    @property
    def is_teamleader_role(self):
        return self.role == 'TEAMLEADER' or self.is_admin_role

    @property
    def is_developer_role(self):
        return self.role == 'DEVELOPER' or self.is_teamleader_role

    @property
    def is_analyst_role(self):
        return self.role == 'ANALYST' or self.is_developer_role

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    leader = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='led_teams', limit_choices_to={'role': 'TEAMLEADER'})
    members = models.ManyToManyField(CustomUser, related_name='teams', blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Vulnerability(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('REPORTED', 'Reported'),
        ('IN_PROGRESS', 'In Progress'),
        ('FIXED', 'Fixed (Pending Verification)'),
        ('MITIGATED', 'Mitigated'),
        ('CLOSED', 'Closed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    poc_screenshot = models.ImageField(upload_to='poc_screenshots/', blank=True, null=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='REPORTED')
    
    reporter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reported_vulnerabilities')
    reporting_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_vulnerabilities')
    developer_assignee = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vulnerabilities', verbose_name='Assignee')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('view_all_vulnerabilities', 'Can view all vulnerabilities'),
            ('change_vulnerability_status', 'Can change vulnerability status'),
        )

    def __str__(self):
        return self.title

class VulnerabilityComment(models.Model):
    vulnerability = models.ForeignKey(Vulnerability, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.vulnerability.title}"
