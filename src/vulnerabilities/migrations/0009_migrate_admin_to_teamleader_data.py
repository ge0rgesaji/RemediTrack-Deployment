from django.db import migrations

def migrate_admin_to_teamleader(apps, schema_editor):
    CustomUser = apps.get_model('vulnerabilities', 'CustomUser')
    CustomUser.objects.filter(role='ADMIN').update(role='TEAMLEADER')

def reverse_migrate_teamleader_to_admin(apps, schema_editor):
    CustomUser = apps.get_model('vulnerabilities', 'CustomUser')
    CustomUser.objects.filter(role='TEAMLEADER').update(role='ADMIN')

class Migration(migrations.Migration):

    dependencies = [
        ('vulnerabilities', '0008_rename_admin_to_teamleader'),
    ]

    operations = [
        migrations.RunPython(migrate_admin_to_teamleader, reverse_migrate_teamleader_to_admin),
    ]
