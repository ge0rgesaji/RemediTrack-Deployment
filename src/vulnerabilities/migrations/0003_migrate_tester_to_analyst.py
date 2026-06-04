from django.db import migrations

def migrate_tester_to_analyst(apps, schema_editor):
    CustomUser = apps.get_model('vulnerabilities', 'CustomUser')
    CustomUser.objects.filter(role='TESTER').update(role='ANALYST')

def reverse_migrate_analyst_to_tester(apps, schema_editor):
    CustomUser = apps.get_model('vulnerabilities', 'CustomUser')
    CustomUser.objects.filter(role='ANALYST').update(role='TESTER')

class Migration(migrations.Migration):

    dependencies = [
        ('vulnerabilities', '0002_alter_customuser_role'),
    ]

    operations = [
        migrations.RunPython(migrate_tester_to_analyst, reverse_migrate_analyst_to_tester),
    ]
