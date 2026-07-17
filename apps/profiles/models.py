from django.db import models
from django.conf import settings

class Profile(models.Model):
    KYC_STATUS_CHOICES = (
        ('NOT_SUBMITTED', 'Not Submitted'),
        ('PENDING', 'Pending Approval'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    DOC_TYPE_CHOICES = (
        ('national_id', 'Government ID'),
        ('passport', 'International Passport'),
        ('driving_license', 'Driving License'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.CharField(max_length=500, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    languages = models.CharField(max_length=200, default='English')
    emergency_contact = models.CharField(max_length=100, null=True, blank=True)
    
    # Cargo preferences
    pref_fragile = models.BooleanField(default=True)
    pref_electronics = models.BooleanField(default=True)
    pref_documents = models.BooleanField(default=True)
    pref_liquid = models.BooleanField(default=False)
    
    # KYC Details
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='NOT_SUBMITTED')
    kyc_document_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='national_id')
    kyc_document_front = models.TextField(null=True, blank=True)  # Store base64 or URL
    kyc_document_back = models.TextField(null=True, blank=True)
    kyc_selfie = models.TextField(null=True, blank=True)
    kyc_rejection_reason = models.TextField(null=True, blank=True)
    
    # Level & Trust Stats
    level = models.IntegerField(default=1)
    completed_trips = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    trust_score = models.IntegerField(default=50)

    def __str__(self):
        return f"Profile of {self.user.email}"

class Address(models.Model):
    TAG_CHOICES = (
        ('Home', 'Home'),
        ('Office', 'Office'),
        ('Billing', 'Billing'),
        ('Warehouse', 'Warehouse'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    tag = models.CharField(max_length=20, choices=TAG_CHOICES, default='Home')
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.tag} address of {self.user.email}"

class KYCDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(max_length=20, choices=Profile.DOC_TYPE_CHOICES)
    document_front = models.TextField() # URL or Base64
    document_back = models.TextField(null=True, blank=True)
    selfie = models.TextField()
    status = models.CharField(max_length=20, choices=Profile.KYC_STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_kyc_docs')

    def __str__(self):
        return f"KYC ({self.document_type}) for {self.user.email} - {self.status}"
