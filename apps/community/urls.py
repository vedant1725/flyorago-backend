from django.urls import path
from .views import (
    CommunityGroupListView,
    CommunityGroupJoinToggleView,
    CommunityPostListView,
    CommunityPostLikeToggleView,
    CommunityPostSaveToggleView,
    CommunityPostCommentListView,
    UserFollowToggleView,
    CommunityPostReportView
)

urlpatterns = [
    # Groups
    path('groups/', CommunityGroupListView.as_view(), name='community_groups'),
    path('groups', CommunityGroupListView.as_view(), name='community_groups_noslash'),
    path('groups/<int:group_id>/join/', CommunityGroupJoinToggleView.as_view(), name='community_group_join'),
    path('groups/<int:group_id>/join', CommunityGroupJoinToggleView.as_view(), name='community_group_join_noslash'),

    # Posts
    path('posts/', CommunityPostListView.as_view(), name='community_posts'),
    path('posts', CommunityPostListView.as_view(), name='community_posts_noslash'),
    path('posts/<int:post_id>/like/', CommunityPostLikeToggleView.as_view(), name='community_post_like'),
    path('posts/<int:post_id>/like', CommunityPostLikeToggleView.as_view(), name='community_post_like_noslash'),
    path('posts/<int:post_id>/save/', CommunityPostSaveToggleView.as_view(), name='community_post_save'),
    path('posts/<int:post_id>/save', CommunityPostSaveToggleView.as_view(), name='community_post_save_noslash'),
    path('posts/<int:post_id>/comments/', CommunityPostCommentListView.as_view(), name='community_post_comments'),
    path('posts/<int:post_id>/comments', CommunityPostCommentListView.as_view(), name='community_post_comments_noslash'),
    path('posts/<int:post_id>/report/', CommunityPostReportView.as_view(), name='community_post_report'),
    path('posts/<int:post_id>/report', CommunityPostReportView.as_view(), name='community_post_report_noslash'),

    # User follow
    path('users/<int:user_id>/follow/', UserFollowToggleView.as_view(), name='community_user_follow'),
    path('users/<int:user_id>/follow', UserFollowToggleView.as_view(), name='community_user_follow_noslash'),
]
