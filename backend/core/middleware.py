import uuid
import threading
from asgiref.local import Local

# Global thread-local storage for request context
_request_context = Local()

def get_current_request_id():
    return getattr(_request_context, 'request_id', None)

def get_current_user_id():
    return getattr(_request_context, 'user_id', None)

class RequestIDMiddleware:
    """
    Middleware that generates a unique UUID for every request and stores it
    in a thread-local context for use in logging. It also attaches the ID
    to the response header for client-side tracking.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate or use existing request ID
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        _request_context.request_id = request_id
        
        # Store user context if already authenticated (e.g. from session)
        if hasattr(request, 'user') and request.user.is_authenticated:
            _request_context.user_id = request.user.user_id
        else:
            _request_context.user_id = None

        response = self.get_response(request)
        
        # Attach to response for debugging
        response['X-Request-ID'] = request_id
        
        # Cleanup
        _request_context.request_id = None
        _request_context.user_id = None
        
        return response

def get_user(token_key):
    from channels.db import database_sync_to_async
    from rest_framework_simplejwt.tokens import AccessToken
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import AnonymousUser

    @database_sync_to_async
    def _get_user():
        try:
            User = get_user_model()
            token = AccessToken(token_key)
            user_id = token.payload['user_id']
            return User.objects.get(user_id=user_id)
        except Exception:
            return AnonymousUser()
    return _get_user()

class JWTAuthMiddleware:
    """
    Custom middleware for Django Channels to authenticate users via JWT.
    Expects the token in the 'token' query parameter.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        from urllib.parse import parse_qs
        from django.contrib.auth.models import AnonymousUser
        
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            scope["user"] = await get_user(token)
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
