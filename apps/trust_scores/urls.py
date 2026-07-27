from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyTrustProfileView, AdminTrustProfileViewSet

router = DefaultRouter()
router.register(r'admin', AdminTrustProfileViewSet, basename='trust-admin')

urlpatterns = [
    # User: GET own live trust profile (always a single object)
    path('profile/', MyTrustProfileView.as_view(), name='trust-profile'),
    # Admin: full CRUD + freeze/override
    path('', include(router.urls)),
]
