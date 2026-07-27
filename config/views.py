from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

class ApiRootResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    version = serializers.CharField()
    docs = serializers.CharField()
    schema = serializers.CharField()
    admin = serializers.CharField()

@extend_schema(
    responses={200: ApiRootResponseSerializer},
    auth=[],
    description="Main entry point and health check for the FlyoraGo REST API."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    Root API view providing metadata and schema/admin links.
    """
    return JsonResponse({
        "status": "success",
        "message": "FlyoraGo Backend is running successfully",
        "version": "1.0.0",
        "docs": "/api/docs/",
        "schema": "/api/schema/",
        "admin": "/admin/"
    }, status=200)
