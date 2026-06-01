from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect

from apps.users.models import is_email_allowed


class AllowedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not is_email_allowed(request.user.email):
                logout(request)
                messages.error(
                    request,
                    'Your Google account is no longer authorized to access Claaxy Log.',
                )
                return redirect('core:home')
        return self.get_response(request)
