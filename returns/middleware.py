from django.shortcuts import redirect
from django.urls import reverse

from .models import UserProfile


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            allowed_paths = {
                reverse('password_change_required'),
                reverse('logout'),
            }
            if (
                request.path not in allowed_paths
                and not request.path.startswith('/static/')
                and not request.path.startswith('/media/')
                and not request.path.startswith('/admin/')
            ):
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                if profile.force_password_change:
                    return redirect('password_change_required')

        return self.get_response(request)
