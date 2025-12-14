from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", code=status.HTTP_200_OK, extra=None):
    payload = {
        "success": True,
        "message": message,
        "data": data or {},
    }
    if extra:
        payload.update(extra)
    return Response(payload, status=code)

