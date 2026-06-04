from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Vulnerability
from guardian.admin import GuardedModelAdmin

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Vulnerability)
class VulnerabilityAdmin(GuardedModelAdmin):
    list_display = ('title', 'severity', 'status', 'reporter', 'created_at')
    list_filter = ('severity', 'status')
    search_fields = ('title', 'description')
