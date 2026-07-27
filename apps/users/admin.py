from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from profiles.models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile / KYC Verification'
    fk_name = 'user'
    fieldsets = (
        ('KYC Verification Details', {
            'fields': (
                'kyc_status',
                'kyc_document_type',
                'kyc_document_front',
                'kyc_document_back',
                'kyc_selfie',
                'kyc_rejection_reason',
            )
        }),
        ('User Trust & Level Stats', {
            'fields': ('level', 'completed_trips', 'rating')
        }),
        ('Cargo Preferences', {
            'fields': (
                'pref_fragile',
                'pref_electronics',
                'pref_documents',
                'pref_liquid',
            )
        }),
    )

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, )
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'phone_number', 'role', 'is_verified'),
        }),
    )