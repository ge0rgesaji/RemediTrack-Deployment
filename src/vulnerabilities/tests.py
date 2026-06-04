from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, Vulnerability, VulnerabilityComment, Team
from django.contrib.auth.models import Group

class AuthenticationTests(TestCase):
    def test_invalid_login_shows_error(self):
        response = self.client.post(reverse('login'), {
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200) # Should stay on login page
        self.assertContains(response, 'Login Failed')
        self.assertContains(response, 'Invalid username or password')

class VulnerabilityTests(TestCase):
    def setUp(self):
        # Create groups
        self.analyst_group = Group.objects.create(name='Analysts')
        self.dev_group = Group.objects.create(name='Developers')
        self.teamleader_group = Group.objects.create(name='Teamleaders')
        
        # Create users
        self.analyst = CustomUser.objects.create_user(username='analyst', password='password123', role='ANALYST')
        self.dev = CustomUser.objects.create_user(username='dev', password='password123', role='DEVELOPER')
        self.teamleader = CustomUser.objects.create_user(username='teamleader_user', password='password123', role='TEAMLEADER')
        self.admin = CustomUser.objects.create_user(username='admin_user', password='password123', role='ADMIN')
        
        self.analyst.groups.add(self.analyst_group)
        self.dev.groups.add(self.dev_group)
        self.teamleader.groups.add(self.teamleader_group)

    def test_analyst_can_report_vulnerability(self):
        self.client.login(username='analyst', password='password123')
        response = self.client.post(reverse('report_vulnerability'), {
            'title': 'Analyst Report',
            'description': 'Desc',
        })
        self.assertEqual(response.status_code, 302)

    def test_dev_cannot_report_vulnerability(self):
        self.client.login(username='dev', password='password123')
        response = self.client.post(reverse('report_vulnerability'), {
            'title': 'Dev Report',
            'description': 'Description',
        })
        self.assertEqual(response.status_code, 403)

    def test_teamleader_cannot_report_vulnerability(self):
        self.client.login(username='teamleader_user', password='password123')
        response = self.client.post(reverse('report_vulnerability'), {
            'title': 'Teamleader Report',
            'description': 'Description',
        })
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_report_vulnerability(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.post(reverse('report_vulnerability'), {
            'title': 'Admin Report',
            'description': 'Desc'
        })
        self.assertEqual(response.status_code, 403)

    def test_dashboard_restricted_without_group(self):
        no_group_user = CustomUser.objects.create_user(username='nogroup', password='password123', role='DEVELOPER')
        self.client.login(username='nogroup', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assignment Pending')
        self.assertContains(response, 'restricted until your Admin assigns you to a group')

    def test_admin_can_access_dashboard_without_group(self):
        admin_user = CustomUser.objects.create_user(username='admin_no_group', password='password123', role='ADMIN')
        self.client.login(username='admin_no_group', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dev_can_view_assigned_vulnerability(self):
        Vulnerability.objects.create(title='Assigned V', reporter=self.analyst, developer_assignee=self.dev)
        self.client.login(username='dev', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assigned V')

    def test_dev_can_view_unassigned_vulnerability(self):
        Vulnerability.objects.create(title='Unassigned V', reporter=self.analyst)
        self.client.login(username='dev', password='password123')
        # Dashboard must be unlocked for this user
        self.dev.groups.add(self.dev_group)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unassigned V')

    def test_dev_can_access_assigned_detail(self):
        v = Vulnerability.objects.create(title='Assigned V', reporter=self.analyst, developer_assignee=self.dev)
        self.client.login(username='dev', password='password123')
        response = self.client.get(reverse('vulnerability_detail', kwargs={'pk': v.pk}))
        self.assertEqual(response.status_code, 200)

    def test_dev_can_access_unassigned_detail(self):
        v = Vulnerability.objects.create(title='Unassigned V', reporter=self.analyst)
        self.client.login(username='dev', password='password123')
        response = self.client.get(reverse('vulnerability_detail', kwargs={'pk': v.pk}))
        self.assertEqual(response.status_code, 200)

    def test_analyst_cannot_access_others_detail(self):
        analyst2 = CustomUser.objects.create_user(username='analyst2', password='password123', role='ANALYST')
        v = Vulnerability.objects.create(title='Analyst 2 Report', reporter=analyst2)
        self.client.login(username='analyst', password='password123')
        response = self.client.get(reverse('vulnerability_detail', kwargs={'pk': v.pk}))
        self.assertEqual(response.status_code, 403)

    def test_teamleader_can_access_all_details(self):
        v = Vulnerability.objects.create(title='Secret Vuln', reporter=self.analyst)
        self.client.login(username='teamleader_user', password='password123')
        response = self.client.get(reverse('vulnerability_detail', kwargs={'pk': v.pk}))
        self.assertEqual(response.status_code, 200)

    def test_dev_cannot_access_manage_view_assigned(self):
        v = Vulnerability.objects.create(title='Assigned V', reporter=self.analyst, developer_assignee=self.dev)
        self.client.login(username='dev', password='password123')
        response = self.client.get(reverse('manage_vulnerability', kwargs={'pk': v.pk}))
        self.assertEqual(response.status_code, 403)

    def test_dev_visibility_logic(self):
        # Dev should see ALL vulnerabilities
        v1 = Vulnerability.objects.create(title='Assigned to Dev', reporter=self.analyst, developer_assignee=self.dev)
        v2 = Vulnerability.objects.create(title='Reported by Dev', reporter=self.dev)
        v3 = Vulnerability.objects.create(title='Secret Other', reporter=self.analyst)
        
        self.client.login(username='dev', password='password123')
        # Unlock dashboard
        self.dev.groups.add(self.dev_group)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Assigned to Dev')
        self.assertContains(response, 'Reported by Dev')
        self.assertContains(response, 'Secret Other')

    def test_dev_can_view_own_report_detail(self):
        v = Vulnerability.objects.create(title='Dev Own Report', reporter=self.dev)
        self.client.login(username='dev', password='password123')
        response = self.client.get(reverse('vulnerability_detail', kwargs={'pk': v.pk}))
        self.assertEqual(response.status_code, 200)

    def test_teamleader_cannot_delete_user(self):
        user_to_delete = CustomUser.objects.create_user(username='to_delete', password='password123', role='ANALYST')
        # Teamleaders can no longer delete users
        self.client.login(username='teamleader_user', password='password123')
        response = self.client.post(reverse('user_delete', kwargs={'pk': user_to_delete.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(CustomUser.objects.filter(username='to_delete').exists())

    def test_non_teamleader_cannot_delete_user(self):
        user_to_delete = CustomUser.objects.create_user(username='to_delete', password='password123', role='ANALYST')
        self.client.login(username='analyst', password='password123')
        response = self.client.post(reverse('user_delete', kwargs={'pk': user_to_delete.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(CustomUser.objects.filter(username='to_delete').exists())

    def test_teamleader_can_access_user_management(self):
        self.client.login(username='teamleader_user', password='password123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)

    def test_analyst_cannot_access_user_management(self):
        self.client.login(username='analyst', password='password123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 403) # Forbidden

class AdminTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='admin_user', password='password123', role='ADMIN')
        self.teamleader = CustomUser.objects.create_user(username='tl', password='password123', role='TEAMLEADER')
        self.dev = CustomUser.objects.create_user(username='dev_user', password='password123', role='DEVELOPER')

    def test_admin_can_access_team_management(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('team_list'))
        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_access_team_management(self):
        # Analyst/Developer still blocked
        analyst = CustomUser.objects.create_user(username='an_test', password='password123', role='ANALYST')
        self.client.login(username='an_test', password='password123')
        response = self.client.get(reverse('team_list'))
        self.assertEqual(response.status_code, 403)
        
        # Teamleader is allowed (gets empty list if they lead no teams)
        self.client.login(username='tl', password='password123')
        response = self.client.get(reverse('team_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_team_and_assign_members(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.post(reverse('team_add'), {
            'name': 'Blue Team',
            'leader': self.teamleader.pk,
            'members': [self.dev.pk],
            'description': 'Security operations team'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Team.objects.count(), 1)
        team = Team.objects.first()
        self.assertEqual(team.leader, self.teamleader)
        self.assertIn(self.dev, team.members.all())

    def test_admin_can_manage_all_users(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        # Should be able to delete any user
        response = self.client.post(reverse('user_delete', kwargs={'pk': self.dev.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CustomUser.objects.filter(username='dev_user').exists())

    def test_admin_user_creation_mandatory_fields(self):
        self.client.login(username='admin_user', password='password123')
        # Attempt to create with missing fields
        response = self.client.post(reverse('user_add'), {
            'username': 'new_guy',
            # missing first_name, last_name, email, role, job_title, password
        })
        # Should stay on form and show errors
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors['first_name'])
        self.assertTrue(form.errors['last_name'])
        self.assertTrue(form.errors['email'])
        self.assertTrue(form.errors['role'])
        self.assertTrue(form.errors['job_title'])
        self.assertTrue(form.errors['password'])

        # Create with all mandatory fields
        response = self.client.post(reverse('user_add'), {
            'username': 'complete_user',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'role': 'DEVELOPER',
            'job_title': 'Software Engineer',
            'password': 'securepassword123',
            'is_active': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(username='complete_user').exists())
        u = CustomUser.objects.get(username='complete_user')
        self.assertEqual(u.first_name, 'John')
        self.assertEqual(u.job_title, 'Software Engineer')

    def test_admin_can_view_vulnerability_details(self):
        analyst = CustomUser.objects.create_user(username='an', password='password123', role='ANALYST')
        v = Vulnerability.objects.create(title='Test Vuln', reporter=analyst)
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('vulnerability_detail', kwargs={'pk': v.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Vuln')

    def test_admin_cannot_manage_vulnerability(self):
        analyst = CustomUser.objects.create_user(username='an', password='password123', role='ANALYST')
        v = Vulnerability.objects.create(title='Test Vuln', reporter=analyst)
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('manage_vulnerability', kwargs={'pk': v.pk}))
        self.assertEqual(response.status_code, 403) # Forbidden for Admin

    def test_admin_sees_reporting_team_on_dashboard(self):
        team = Team.objects.create(name='Analyst Team', leader=self.teamleader)
        analyst = CustomUser.objects.create_user(username='reporter_analyst', password='password123', role='ANALYST')
        team.members.add(analyst)
        
        self.client.login(username='reporter_analyst', password='password123')
        self.client.post(reverse('report_vulnerability'), {
            'title': 'Team Vuln',
            'description': 'Desc'
        })
        
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team Vuln')
        self.assertContains(response, 'Analyst Team')

class ProfileTests(TestCase):
    def setUp(self):
        self.dev_group = Group.objects.create(name='Developers')
        self.user = CustomUser.objects.create_user(username='testuser', password='password123', role='DEVELOPER')
        self.user.groups.add(self.dev_group)

    def test_user_can_access_profile(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update Your Profile')

    def test_user_can_update_profile(self):
        self.client.login(username='testuser', password='password123')
        # Old password NOT required for general changes now
        response = self.client.post(reverse('profile'), {
            'username': 'updated_testuser',
            'first_name': 'New',
            'last_name': 'Name',
            'email': 'newemail@example.com',
            'job_title': 'Senior Developer',
            'phone_number': '123456789',
            'address': '123 Test St',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updated_testuser')
        self.assertEqual(self.user.first_name, 'New')

    def test_password_change_fails_without_old_password(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('profile'), {
            'username': 'testuser',
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'old_password', 'Current password is required to change your password.')

    def test_password_change_fails_with_wrong_old_password(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('profile'), {
            'username': 'testuser',
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'old_password', 'Incorrect current password.')

    def test_user_can_change_password_securely(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('profile'), {
            'username': 'updateduser',
            'old_password': 'password123',
            'new_password': 'newsecurepassword',
            'confirm_new_password': 'newsecurepassword'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertTrue(self.user.check_password('newsecurepassword'))
        
        # Verify still logged in (session auth hash update)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'updateduser')

class WorkflowTests(TestCase):
    def setUp(self):
        self.analyst = CustomUser.objects.create_user(username='analyst', password='password123', role='ANALYST')
        self.dev = CustomUser.objects.create_user(username='dev', password='password123', role='DEVELOPER')
        self.teamleader = CustomUser.objects.create_user(username='teamleader_user', password='password123', role='TEAMLEADER')
        self.vuln = Vulnerability.objects.create(title='Test Vuln', reporter=self.analyst, description='Desc')

    def test_teamleader_can_assign_and_comment(self):
        self.client.login(username='teamleader_user', password='password123')
        response = self.client.post(reverse('manage_vulnerability', kwargs={'pk': self.vuln.pk}), {
            'severity': 'HIGH',
            'status': 'IN_PROGRESS',
            'developer_assignee': self.dev.pk,
            'comment': 'Please fix this ASAP.'
        })
        self.assertEqual(response.status_code, 302)
        self.vuln.refresh_from_db()
        self.assertEqual(self.vuln.developer_assignee, self.dev)
        self.assertEqual(self.vuln.comments.count(), 1)
        self.assertEqual(self.vuln.comments.first().text, 'Please fix this ASAP.')

    def test_dev_can_mark_fixed_and_comment(self):
        self.vuln.developer_assignee = self.dev
        self.vuln.status = 'IN_PROGRESS'
        self.vuln.save()
        
        self.client.login(username='dev', password='password123')
        response = self.client.post(reverse('complete_task', kwargs={'pk': self.vuln.pk}), {
            'comment': 'I have fixed the issue.'
        })
        self.assertEqual(response.status_code, 302)
        self.vuln.refresh_from_db()
        self.assertEqual(self.vuln.status, 'FIXED')
        self.assertEqual(self.vuln.comments.count(), 1)
        self.assertEqual(self.vuln.comments.first().text, 'I have fixed the issue.')

    def test_teamleader_can_reassign_to_analyst(self):
        self.vuln.status = 'FIXED'
        self.vuln.developer_assignee = self.dev
        self.vuln.save()
        
        self.client.login(username='teamleader_user', password='password123')
        response = self.client.post(reverse('manage_vulnerability', kwargs={'pk': self.vuln.pk}), {
            'severity': 'HIGH',
            'status': 'FIXED',
            'developer_assignee': self.analyst.pk,
            'comment': 'Analyst, please verify.'
        })
        self.assertEqual(response.status_code, 302)
        self.vuln.refresh_from_db()
        self.assertEqual(self.vuln.developer_assignee, self.analyst)
        self.assertEqual(self.vuln.comments.last().text, 'Analyst, please verify.')

    def test_analyst_can_verify_and_mitigate(self):
        # Analysts can still use the manage view if we allow them, or they can use the complete view.
        # But the user specifically said "don't give the dev ability to manage".
        # Let's see if Analyst can still use manage.
        self.vuln.status = 'FIXED'
        self.vuln.developer_assignee = self.analyst
        self.vuln.save()
        
        self.client.login(username='analyst', password='password123')
        response = self.client.post(reverse('complete_task', kwargs={'pk': self.vuln.pk}), {
            'comment': 'I have verified the fix.'
        })
        self.assertEqual(response.status_code, 302)
        self.vuln.refresh_from_db()
        self.assertEqual(self.vuln.status, 'MITIGATED') 
        self.assertEqual(self.vuln.comments.last().text, 'I have verified the fix.')

    def test_history_is_visible_to_all_involved(self):
        VulnerabilityComment.objects.create(vulnerability=self.vuln, author=self.teamleader, text='Teamleader comment')
        VulnerabilityComment.objects.create(vulnerability=self.vuln, author=self.dev, text='Dev comment')
        self.vuln.developer_assignee = self.dev
        self.vuln.save()

        for user in [self.teamleader, self.dev, self.analyst]:
            self.client.login(username=user.username, password='password123')
            response = self.client.get(reverse('vulnerability_detail', kwargs={'pk': self.vuln.pk}))
            self.assertContains(response, 'Teamleader comment')
            self.assertContains(response, 'Dev comment')

    def test_dev_can_view_after_reassignment(self):
        # Dev works on it and comments
        VulnerabilityComment.objects.create(vulnerability=self.vuln, author=self.dev, text='I fixed it')
        self.vuln.status = 'FIXED'
        self.vuln.developer_assignee = self.dev
        self.vuln.save()
        
        # Teamleader reassigns to Analyst
        self.vuln.developer_assignee = self.analyst
        self.vuln.save()
        
        # Dev should still be able to view it
        self.client.login(username='dev', password='password123')
        response = self.client.get(reverse('vulnerability_detail', kwargs={'pk': self.vuln.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'I fixed it')
        # Button should be hidden
        self.assertNotContains(response, 'Mark as Completed')
