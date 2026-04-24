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
