from django.db import migrations

def move_comments(apps, schema_editor):
    Vulnerability = apps.get_model('vulnerabilities', 'Vulnerability')
    VulnerabilityComment = apps.get_model('vulnerabilities', 'VulnerabilityComment')
    CustomUser = apps.get_model('vulnerabilities', 'CustomUser')

    # Try to find a suitable admin user to attribute these comments to
    admin_user = CustomUser.objects.filter(role='ADMIN').first()
    if not admin_user:
        admin_user = CustomUser.objects.filter(is_superuser=True).first()
    
    if not admin_user:
        # If no admin/superuser exists yet (unlikely in prod, but possible in fresh dev)
        # We might need to skip or create a placeholder. For now, let's just skip if no user.
        return

    for vuln in Vulnerability.objects.exclude(assignment_comment__isnull=True).exclude(assignment_comment=''):
        VulnerabilityComment.objects.create(
            vulnerability=vuln,
            author=admin_user,
            text=vuln.assignment_comment
        )

class Migration(migrations.Migration):

    dependencies = [
        ('vulnerabilities', '0005_add_vulnerability_comment_model'),
    ]

    operations = [
        migrations.RunPython(move_comments),
    ]
