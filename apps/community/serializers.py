from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CommunityGroup, CommunityMember, CommunityPost,
    PostLike, PostSave, PostComment, UserFollow, PostReport
)

User = get_user_model()

class CommunityAuthorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    is_verified_traveler = serializers.SerializerMethodField()
    is_verified_sender = serializers.SerializerMethodField()
    kyc_status = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role', 'avatar',
            'is_verified_traveler', 'is_verified_sender', 'kyc_status', 'is_following'
        ]

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.email.split('@')[0]

    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile and obj.profile.avatar:
            return obj.profile.avatar
        return None

    def get_kyc_status(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.kyc_status
        return 'NOT_SUBMITTED'

    def get_is_verified_traveler(self, obj):
        is_kyc = hasattr(obj, 'profile') and obj.profile and obj.profile.kyc_status == 'APPROVED'
        return is_kyc or (obj.role == 'traveler' and obj.is_verified)

    def get_is_verified_sender(self, obj):
        is_kyc = hasattr(obj, 'profile') and obj.profile and obj.profile.kyc_status == 'APPROVED'
        return is_kyc or (obj.role == 'sender' and obj.is_verified)

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.id != obj.id:
            return UserFollow.objects.filter(follower=request.user, following=obj).exists()
        return False


class CommunityGroupSerializer(serializers.ModelSerializer):
    is_joined = serializers.SerializerMethodField()

    class Meta:
        model = CommunityGroup
        fields = [
            'id', 'name', 'slug', 'group_type', 'description', 'icon_name',
            'origin_city', 'destination_city', 'members_count', 'posts_count',
            'is_joined', 'created_at'
        ]

    def get_is_joined(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommunityMember.objects.filter(group=obj, user=request.user).exists()
        return False


class PostCommentSerializer(serializers.ModelSerializer):
    author = CommunityAuthorSerializer(read_only=True)

    class Meta:
        model = PostComment
        fields = ['id', 'post', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class CommunityPostSerializer(serializers.ModelSerializer):
    author = CommunityAuthorSerializer(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    group_type = serializers.CharField(source='group.group_type', read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'group', 'group_name', 'group_type', 'author',
            'category', 'title', 'content',
            'origin_city', 'destination_city', 'travel_date', 'available_capacity_kg',
            'linked_trip_id', 'linked_booking_id',
            'likes_count', 'comments_count', 'saves_count',
            'is_liked', 'is_saved', 'created_at'
        ]
        read_only_fields = [
            'id', 'author', 'likes_count', 'comments_count', 'saves_count',
            'is_liked', 'is_saved', 'created_at'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user).exists()
        return False

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostSave.objects.filter(post=obj, user=request.user).exists()
        return False
