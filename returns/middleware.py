from django.db.utils import DatabaseError, OperationalError
from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import SiteConfiguration, UserProfile


class SiteTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            configured_timezone = SiteConfiguration.load().timezone
            timezone.activate(ZoneInfo(configured_timezone))
        except (DatabaseError, OperationalError, ZoneInfoNotFoundError):
            timezone.deactivate()

        response = self.get_response(request)
        timezone.deactivate()
        return response


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
