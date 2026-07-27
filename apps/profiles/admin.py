from django.contrib import admin
from .models import Profile, Address

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'kyc_status', 'kyc_document_type', 'level', 'rating', 'completed_trips')
    list_filter = ('kyc_status', 'kyc_document_type', 'level')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    fieldsets = (
        ('User Reference', {'fields': ('user',)}),
        ('KYC Status & Details', {
            'fields': ('kyc_status', 'kyc_document_type', 'kyc_document_front', 'kyc_document_back', 'kyc_selfie', 'kyc_rejection_reason')
        }),
        ('Preferences & Profile Info', {
            'fields': ('avatar', 'bio', 'languages', 'emergency_contact', 'pref_fragile', 'pref_electronics', 'pref_documents', 'pref_liquid')
        }),
        ('User Trust & Levels', {
            'fields': ('level', 'completed_trips', 'rating')
        }),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag', 'text', 'created_at')
    list_filter = ('tag', 'created_at')
    search_fields = ('user__email', 'text')
