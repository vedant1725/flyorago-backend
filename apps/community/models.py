from django.db import models
from django.conf import settings
from django.utils import timezone

class CommunityGroup(models.Model):
    GROUP_TYPE_CHOICES = (
        ('CITY', 'City Community'),
        ('ROUTE', 'Route Community'),
    )

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPE_CHOICES, default='CITY')
    description = models.TextField(blank=True, default='')
    icon_name = models.CharField(max_length=60, default='globe-outline')
    
    # Specific route fields if type == ROUTE
    origin_city = models.CharField(max_length=100, blank=True, null=True)
    destination_city = models.CharField(max_length=100, blank=True, null=True)

    # Activity counters
    members_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['group_type', 'name']

    def __str__(self):
        return f"{self.get_group_type_display()}: {self.name}"


class CommunityMember(models.Model):
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} in {self.group.name}"


class CommunityPost(models.Model):
    POST_CATEGORY_CHOICES = (
        ('UPCOMING_TRAVEL', 'Upcoming Travel'),
        ('TRAVEL_EXPERIENCE', 'Travel Experience'),
        ('AVAILABLE_ROUTE', 'Available Travel Route'),
        ('PARCEL_REQUIREMENT', 'Parcel Requirement'),
        ('SUCCESS_STORY', 'Successful Delivery Story'),
        ('TRAVEL_TIPS', 'Travel Tips'),
        ('FLYORA_EXPERIENCE', 'Flyorago Experience'),
    )

    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_posts')
    
    category = models.CharField(max_length=40, choices=POST_CATEGORY_CHOICES, default='UPCOMING_TRAVEL')
    title = models.CharField(max_length=250)
    content = models.TextField()

    # Route / Travel metadata (optional for trips/requirements)
    origin_city = models.CharField(max_length=100, blank=True, null=True)
    destination_city = models.CharField(max_length=100, blank=True, null=True)
    travel_date = models.DateField(blank=True, null=True)
    available_capacity_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Optional linked trip or booking
    linked_trip_id = models.IntegerField(null=True, blank=True)
    linked_booking_id = models.IntegerField(null=True, blank=True)

    # Social stats
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    saves_count = models.PositiveIntegerField(default=0)

    # Moderation & spam guard
    is_moderated = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title} by {self.author.email}"


class PostLike(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')


class PostSave(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='saved_by')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')


class PostComment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.post_id}"


class UserFollow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.email} follows {self.following.email}"


class PostReport(models.Model):
    REPORT_REASON_CHOICES = (
        ('SPAM', 'Spam or irrelevant advertising'),
        ('INAPPROPRIATE', 'Inappropriate or harmful content'),
        ('NOT_LOGISTICS', 'Not related to travel or parcel logistics'),
        ('FRAUD', 'Potential scam or fraud'),
        ('OTHER', 'Other violation of Community Guidelines'),
    )

    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_posts')
    reason = models.CharField(max_length=40, choices=REPORT_REASON_CHOICES, default='SPAM')
    details = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'reporter')
        ordering = ['-created_at']
