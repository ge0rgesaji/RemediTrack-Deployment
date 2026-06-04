import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vms_project.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from vulnerabilities.models import CustomUser, Vulnerability, Team

def setup():
    # Create Groups
    admin_group, _ = Group.objects.get_or_create(name='Admins')
    teamleader_group, _ = Group.objects.get_or_create(name='Teamleaders')
    dev_group, _ = Group.objects.get_or_create(name='Developers')
    analyst_group, _ = Group.objects.get_or_create(name='Analysts')

    # ContentTypes
    vulnerability_ct = ContentType.objects.get_for_model(Vulnerability)
    user_ct = ContentType.objects.get_for_model(CustomUser)
    team_ct = ContentType.objects.get_for_model(Team)

    # Permissions
    add_vuln = Permission.objects.get(codename='add_vulnerability', content_type=vulnerability_ct)
    view_vuln = Permission.objects.get(codename='view_vulnerability', content_type=vulnerability_ct)
    change_vuln = Permission.objects.get(codename='change_vulnerability', content_type=vulnerability_ct)
    view_all = Permission.objects.get(codename='view_all_vulnerabilities', content_type=vulnerability_ct)
    change_status = Permission.objects.get(codename='change_vulnerability_status', content_type=vulnerability_ct)
    
    # User management permissions
    add_user = Permission.objects.get(codename='add_customuser', content_type=user_ct)
    change_user = Permission.objects.get(codename='change_customuser', content_type=user_ct)
    view_user = Permission.objects.get(codename='view_customuser', content_type=user_ct)
    delete_user = Permission.objects.get(codename='delete_customuser', content_type=user_ct)

    # Team management permissions
    add_team = Permission.objects.get(codename='add_team', content_type=team_ct)
    change_team = Permission.objects.get(codename='change_team', content_type=team_ct)
    view_team = Permission.objects.get(codename='view_team', content_type=team_ct)
    delete_team = Permission.objects.get(codename='delete_team', content_type=team_ct)

    # Assign permissions to Groups
    analyst_group.permissions.add(add_vuln, view_vuln)
    dev_group.permissions.add(add_vuln, view_vuln, change_vuln, view_all, change_status)
    teamleader_group.permissions.add(add_vuln, view_vuln, change_vuln, view_all, change_status, add_user, change_user, view_user)
    
    # Admin gets everything
    admin_group.permissions.add(
        add_vuln, view_vuln, change_vuln, view_all, change_status,
        add_user, change_user, view_user, delete_user,
        add_team, change_team, view_team, delete_team
    )

    # Create Superuser/Admin if not exists
    if not CustomUser.objects.filter(username='admin').exists():
        CustomUser.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='ADMIN')
        print("Admin user 'admin' created with password 'admin123'")
    else:
        u = CustomUser.objects.get(username='admin')
        u.role = 'ADMIN'
        u.save()
        u.groups.add(admin_group)

    print("Groups, permissions, and Admin user initialized.")

if __name__ == '__main__':
    setup()
