from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    return Response({
        "success": True,
        "status": "success",
        "message": message,
        "data": data or {}
    }, status=status_code)

def failure_response(errors=None, message="Error occurred", status_code=status.HTTP_400_BAD_REQUEST):
    return Response({
        "success": False,
        "status": "error",
        "message": message,
        "errors": errors or {}
    }, status=status_code)
