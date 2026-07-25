from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import TrustProfile, TrustActivityLog, RiskLog
from .serializers import TrustProfileSerializer, TrustActivityLogSerializer, RiskLogSerializer
from .engine import TrustEngine


class MyTrustProfileView(APIView):
    """
    GET /api/trust/profile/
    Returns the authenticated user's live trust profile after recalculating actual database activity.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = TrustEngine.recalculate_profile(request.user)
        serializer = TrustProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)


class IsAdminOrStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, 'role', '') == 'admin' or user.is_staff or user.is_superuser


class AdminTrustProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrStaffUser]
    serializer_class = TrustProfileSerializer

    def get_queryset(self):
        """
        Return all trust profiles, recalculating live score for every user.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.all()
        for u in users:
            try:
                TrustEngine.recalculate_profile(u)
            except Exception:
                pass
        return TrustProfile.objects.select_related('user').order_by('-score')

    @action(detail=True, methods=['post'])
    def override_score(self, request, pk=None):
        profile = self.get_object()
        new_score = request.data.get('score')
        reason = request.data.get('reason', 'Admin Override')

        if new_score is None:
            return Response({'error': 'Score is required'}, status=status.HTTP_400_BAD_REQUEST)

        old_score = profile.score
        profile.score = int(new_score)
        profile.save()

        TrustActivityLog.objects.create(
            profile=profile,
            activity_type='ADMIN_OVERRIDE',
            score_change=profile.score - old_score,
            reason=reason
        )
        return Response(TrustProfileSerializer(profile, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def freeze(self, request, pk=None):
        profile = self.get_object()
        profile.status = 'FROZEN'
        profile.save()
        return Response({'status': 'frozen', 'score': profile.score, 'level': profile.level})

    @action(detail=True, methods=['post'])
    def unfreeze(self, request, pk=None):
        profile = self.get_object()
        profile.status = 'ACTIVE'
        profile.save()
        return Response({'status': 'active'})
