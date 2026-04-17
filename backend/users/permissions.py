from rest_framework.permissions import BasePermission


class BaselineCompleted(BasePermission):
    """
    Blocks access to experiment endpoints until the user has completed
    the mandatory baseline questionnaire.
    """
    message = "You must complete the baseline assessment before accessing this resource."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_completed_baseline
        )
