import logging
import traceback
from django.conf import settings
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotAuthenticated, PermissionDenied
from django.http import Http404
from rest_framework.exceptions import APIException

try:
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
except Exception:
    TokenError = None
    InvalidToken = None


logger = logging.getLogger(__name__)


def _normalize_validation_errors(exc):
    if isinstance(exc.detail, (list, tuple)):
        return {"non_field_errors": [str(x) for x in exc.detail]}
    if isinstance(exc.detail, dict):
        out = {}
        for key, value in exc.detail.items():
            if isinstance(value, (list, tuple)):
                out[key] = [str(v) for v in value]
            elif isinstance(value, dict):
                out[key] = []
                for subk, subv in value.items():
                    if isinstance(subv, (list, tuple)):
                        out[key].extend([str(x) for x in subv])
                    else:
                        out[key].append(str(subv))
            else:
                out[key] = [str(value)]
        return out
    return {"detail": [str(exc.detail)]}


def api_error_response(message=None, errors=None, code=status.HTTP_400_BAD_REQUEST, extra=None):
    payload = {
        "success": False,
        "message": message or "Something went wrong",
        "errors": errors or {},
    }
    if extra:
        payload.update(extra)
    return Response(payload, status=code)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    request = context.get("request", None)
    view = context.get("view", None)
    view_name = getattr(view, "__class__", None)
    try:
        if InvalidToken and isinstance(exc, InvalidToken):
            return api_error_response(
                "Invalid or expired token",
                errors={"token": ["Token is invalid or expired"]},
                code=status.HTTP_401_UNAUTHORIZED
            )

        if TokenError and isinstance(exc, TokenError):
            return api_error_response(
                "Invalid or expired token",
                errors={"token": ["Token is invalid or expired"]},
                code=status.HTTP_401_UNAUTHORIZED
            )
        if isinstance(exc, Http404):
            return api_error_response("Not found", errors={"detail": ["Not found"]}, code=status.HTTP_404_NOT_FOUND)

        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            msg = getattr(exc, "detail", "Authentication failed")
            return api_error_response(str(msg), errors={"auth": [str(msg)]}, code=status.HTTP_401_UNAUTHORIZED)

        if isinstance(exc, PermissionDenied):
            msg = getattr(exc, "detail", "Permission denied")
            return api_error_response(str(msg), errors={"permission": [str(msg)]}, code=status.HTTP_403_FORBIDDEN)

        if isinstance(exc, ValidationError):
            errors = _normalize_validation_errors(exc)
            return api_error_response("Validation error", errors=errors, code=status.HTTP_400_BAD_REQUEST)

        if response is not None:
            data = response.data
            if isinstance(data, dict) and "success" in data:
                return response

            if isinstance(data, dict) and "detail" in data:
                detail = data.get("detail")
                return api_error_response(str(detail), errors={"detail": [str(detail)]}, code=response.status_code)

            if isinstance(data, dict):
                normalized = {}
                for k, v in data.items():
                    if isinstance(v, (list, tuple)):
                        normalized[k] = [str(x) for x in v]
                    else:
                        normalized[k] = [str(v)]
                return api_error_response("Validation error", errors=normalized, code=response.status_code)

            return api_error_response(str(data), errors={"detail": [str(data)]}, code=response.status_code)

        tb = traceback.format_exc()
        logger.error("Unhandled exception in view: %s %s\nTraceback:\n%s", request and getattr(request, "path", ""), view_name, tb)

        if settings.DEBUG:
            return api_error_response("Internal server error", errors={"traceback": [tb]}, code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return api_error_response("Internal server error", errors={"detail": ["Internal server error"]}, code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as handler_exc:
        logger.exception("Exception in custom_exception_handler: %s", handler_exc)
        return api_error_response("Internal server error", errors={"detail": ["Internal server error"]}, code=status.HTTP_500_INTERNAL_SERVER_ERROR)

