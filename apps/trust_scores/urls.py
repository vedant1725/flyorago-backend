from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyTrustProfileView, AdminTrustProfileViewSet

router = DefaultRouter()
router.register(r'admin', AdminTrustProfileViewSet, basename='trust-admin')

urlpatterns = [
    # User: GET own live trust profile (always a single object)
    path('profile/', MyTrustProfileView.as_view(), name='trust-profile'),
    path('profile', MyTrustProfileView.as_view(), name='trust-profile-noslash'),
    # Direct list view fallback for both /admin and /admin/
    path('admin', AdminTrustProfileViewSet.as_view({'get': 'list'}), name='trust-admin-noslash'),
    path('admin/', AdminTrustProfileViewSet.as_view({'get': 'list'}), name='trust-admin-slash'),
    # Admin: full CRUD + freeze/override
    path('', include(router.urls)),
]
