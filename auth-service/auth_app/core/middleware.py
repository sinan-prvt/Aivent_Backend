import traceback
import logging
from django.conf import settings
from django.http import JsonResponse, Http404
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    PermissionDenied,
    AuthenticationFailed,
    NotAuthenticated,
)



logger = logging.getLogger(__name__)


class ExceptionLoggingMiddleware(MiddlewareMixin): 
    def process_exception(self, request, exception): 
        if isinstance(exception, (APIException, ValidationError, PermissionDenied, AuthenticationFailed, NotAuthenticated)): 
            return None 
        if isinstance(exception, Http404): 
            return None 
        tb = traceback.format_exc() 
        logger.error("Unhandled exception at %s\n%s", request.path, tb) 
    
        payload = { 
            "success": False, 
            "message": "Internal server error", 
            "errors": {"detail": ["Internal server error"]}, 
        } 
    
        if settings.DEBUG: 
            payload["errors"]["traceback"] = [tb]
            payload["message"] = str(exception) 
        return JsonResponse(payload, status=500)
    