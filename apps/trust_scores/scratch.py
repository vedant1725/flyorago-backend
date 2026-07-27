from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class TrustProfile(models.fields.related.OneToOneField):
    pass
