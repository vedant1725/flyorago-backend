from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import F, Q
from django.contrib.auth import get_user_model

from .models import (
    CommunityGroup, CommunityMember, CommunityPost,
    PostLike, PostSave, PostComment, UserFollow, PostReport
)
from .serializers import (
    CommunityGroupSerializer, CommunityPostSerializer,
    PostCommentSerializer, CommunityAuthorSerializer
)

User = get_user_model()

DEFAULT_INITIAL_GROUPS = [
    # A. City-wise Communities
    {'name': 'Ahmedabad Community', 'slug': 'ahmedabad', 'group_type': 'CITY', 'origin_city': 'Ahmedabad', 'icon_name': 'business', 'description': 'Hub for travelers, senders & local parcel requests in Ahmedabad.'},
    {'name': 'Vadodara Community', 'slug': 'vadodara', 'group_type': 'CITY', 'origin_city': 'Vadodara', 'icon_name': 'location', 'description': 'Vadodara cultural & business travel parcel coordination network.'},
    {'name': 'Surat Community', 'slug': 'surat', 'group_type': 'CITY', 'origin_city': 'Surat', 'icon_name': 'diamond', 'description': 'Surat textile & diamond trade route traveler and sender community.'},
    {'name': 'Rajkot Community', 'slug': 'rajkot', 'group_type': 'CITY', 'origin_city': 'Rajkot', 'icon_name': 'map', 'description': 'Saurashtra travel & parcel express connection community.'},
    {'name': 'Mumbai Community', 'slug': 'mumbai', 'group_type': 'CITY', 'origin_city': 'Mumbai', 'icon_name': 'airplane', 'description': 'Mumbai commercial hub luggage sharing and high-frequency dispatch network.'},

    # B. Route-wise Communities
    {'name': 'Ahmedabad to Mumbai', 'slug': 'ahmedabad-to-mumbai', 'group_type': 'ROUTE', 'origin_city': 'Ahmedabad', 'destination_city': 'Mumbai', 'icon_name': 'navigate', 'description': 'High demand daily travel corridor for urgent parcels & travel luggage.'},
    {'name': 'Vadodara to Surat', 'slug': 'vadodara-to-surat', 'group_type': 'ROUTE', 'origin_city': 'Vadodara', 'destination_city': 'Surat', 'icon_name': 'swap-horizontal', 'description': 'South Gujarat direct courier & traveler parcel express sharing.'},
    {'name': 'Ahmedabad to Rajkot', 'slug': 'ahmedabad-to-rajkot', 'group_type': 'ROUTE', 'origin_city': 'Ahmedabad', 'destination_city': 'Rajkot', 'icon_name': 'trail-sign', 'description': 'Fast intercity road/rail traveler delivery community.'},
    {'name': 'Surat to Mumbai', 'slug': 'surat-to-mumbai', 'group_type': 'ROUTE', 'origin_city': 'Surat', 'destination_city': 'Mumbai', 'icon_name': 'infinite', 'description': 'Same-day and next-day cross-state trusted luggage courier corridor.'},
]

def ensure_seed_groups():
    for g_data in DEFAULT_INITIAL_GROUPS:
        CommunityGroup.objects.get_or_create(
            slug=g_data['slug'],
            defaults=g_data
        )


class CommunityGroupListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        ensure_seed_groups()
        group_type = request.query_params.get('type')  # 'CITY' or 'ROUTE'
        search = request.query_params.get('search')

        qs = CommunityGroup.objects.filter(is_active=True)
        if group_type and group_type.upper() in ['CITY', 'ROUTE']:
            qs = qs.filter(group_type=group_type.upper())

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

        serializer = CommunityGroupSerializer(qs, many=True, context={'request': request})
        return Response({
            'success': True,
            'groups': serializer.data,
            'total': qs.count()
        })


class CommunityGroupJoinToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(CommunityGroup, id=group_id)
        membership = CommunityMember.objects.filter(group=group, user=request.user).first()
        
        if membership:
            membership.delete()
            if group.members_count > 0:
                group.members_count = F('members_count') - 1
                group.save(update_fields=['members_count'])
            group.refresh_from_db()
            return Response({
                'success': True,
                'joined': False,
                'members_count': group.members_count,
                'message': f'Left {group.name}'
            })
        else:
            CommunityMember.objects.create(group=group, user=request.user)
            group.members_count = F('members_count') + 1
            group.save(update_fields=['members_count'])
            group.refresh_from_db()
            return Response({
                'success': True,
                'joined': True,
                'members_count': group.members_count,
                'message': f'Joined {group.name}'
            })


class CommunityPostListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        ensure_seed_groups()
        group_id = request.query_params.get('group_id')
        category = request.query_params.get('category')
        tab = request.query_params.get('tab')  # 'all', 'saved', 'my_posts'
        search = request.query_params.get('search')

        qs = CommunityPost.objects.filter(is_moderated=True).select_related('author', 'group')

        if group_id:
            qs = qs.filter(group_id=group_id)
        if category:
            qs = qs.filter(category=category)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search) | Q(origin_city__icontains=search) | Q(destination_city__icontains=search))

        if tab == 'saved' and request.user.is_authenticated:
            saved_post_ids = PostSave.objects.filter(user=request.user).values_list('post_id', flat=True)
            qs = qs.filter(id__in=saved_post_ids)
        elif tab == 'my_posts' and request.user.is_authenticated:
            qs = qs.filter(author=request.user)

        serializer = CommunityPostSerializer(qs, many=True, context={'request': request})
        return Response({
            'success': True,
            'posts': serializer.data,
            'total': qs.count()
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'success': False, 'message': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        serializer = CommunityPostSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            post = serializer.save(author=request.user)
            # Increment group posts count
            CommunityGroup.objects.filter(id=post.group_id).update(posts_count=F('posts_count') + 1)
            
            # Ensure author joins group automatically
            CommunityMember.objects.get_or_create(group_id=post.group_id, user=request.user)
            
            output = CommunityPostSerializer(post, context={'request': request}).data
            return Response({
                'success': True,
                'post': output,
                'message': 'Community post published successfully.'
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CommunityPostLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(CommunityPost, id=post_id)
        like = PostLike.objects.filter(post=post, user=request.user).first()
        if like:
            like.delete()
            if post.likes_count > 0:
                post.likes_count = F('likes_count') - 1
                post.save(update_fields=['likes_count'])
            is_liked = False
        else:
            PostLike.objects.create(post=post, user=request.user)
            post.likes_count = F('likes_count') + 1
            post.save(update_fields=['likes_count'])
            is_liked = True

        post.refresh_from_db()
        return Response({
            'success': True,
            'is_liked': is_liked,
            'likes_count': post.likes_count
        })


class CommunityPostSaveToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(CommunityPost, id=post_id)
        save = PostSave.objects.filter(post=post, user=request.user).first()
        if save:
            save.delete()
            if post.saves_count > 0:
                post.saves_count = F('saves_count') - 1
                post.save(update_fields=['saves_count'])
            is_saved = False
        else:
            PostSave.objects.create(post=post, user=request.user)
            post.saves_count = F('saves_count') + 1
            post.save(update_fields=['saves_count'])
            is_saved = True

        post.refresh_from_db()
        return Response({
            'success': True,
            'is_saved': is_saved,
            'saves_count': post.saves_count
        })


class CommunityPostCommentListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, post_id):
        post = get_object_or_404(CommunityPost, id=post_id)
        comments = post.comments.select_related('author').all()
        serializer = PostCommentSerializer(comments, many=True, context={'request': request})
        return Response({'success': True, 'comments': serializer.data})

    def post(self, request, post_id):
        if not request.user.is_authenticated:
            return Response({'success': False, 'message': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        post = get_object_or_404(CommunityPost, id=post_id)
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'success': False, 'message': 'Comment content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        comment = PostComment.objects.create(post=post, author=request.user, content=content)
        post.comments_count = F('comments_count') + 1
        post.save(update_fields=['comments_count'])
        post.refresh_from_db()

        serializer = PostCommentSerializer(comment, context={'request': request})
        return Response({
            'success': True,
            'comment': serializer.data,
            'comments_count': post.comments_count
        }, status=status.HTTP_201_CREATED)


class UserFollowToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)
        if target_user.id == request.user.id:
            return Response({'success': False, 'message': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        follow = UserFollow.objects.filter(follower=request.user, following=target_user).first()
        if follow:
            follow.delete()
            is_following = False
            msg = f'Unfollowed {target_user.email}'
        else:
            UserFollow.objects.create(follower=request.user, following=target_user)
            is_following = True
            msg = f'Now following {target_user.email}'

        return Response({
            'success': True,
            'is_following': is_following,
            'message': msg
        })


class CommunityPostReportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(CommunityPost, id=post_id)
        reason = request.data.get('reason', 'SPAM')
        details = request.data.get('details', '')

        PostReport.objects.update_or_create(
            post=post,
            reporter=request.user,
            defaults={'reason': reason, 'details': details}
        )
        post.is_flagged = True
        post.save(update_fields=['is_flagged'])

        return Response({
            'success': True,
            'message': 'Thank you. The post has been flagged for admin moderation.'
        })
