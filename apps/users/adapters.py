from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import filter_users_by_email, user_email
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

from apps.users.models import is_email_allowed


def _username_from_email(email: str) -> str:
    max_length = get_user_model()._meta.get_field('username').max_length
    return email.lower().strip()[:max_length]


def _social_login_email(sociallogin) -> str:
    email = sociallogin.user.email
    if email:
        return email
    account = getattr(sociallogin, 'account', None)
    if account and account.extra_data:
        return account.extra_data.get('email') or ''
    return ''


class EmailAccountAdapter(DefaultAccountAdapter):
    """Use email as username when allauth username field is disabled."""

    def populate_username(self, request, user):
        email = user_email(user)
        if email and not user.username:
            user.username = _username_from_email(email)
            return
        super().populate_username(request, user)


class WhitelistSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = _social_login_email(sociallogin)
        if not is_email_allowed(email):
            messages.error(
                request,
                'Your Google account is not authorized to access Claaxy Log.',
            )
            raise ImmediateHttpResponse(redirect('core:home'))

        if sociallogin.is_existing:
            return

        if email:
            existing_users = filter_users_by_email(email)
            if existing_users:
                sociallogin.connect(request, existing_users[0])

    def populate_user(self, request, sociallogin, data):
        super().populate_user(request, sociallogin, data)
        email = sociallogin.user.email or data.get('email')
        if email and not sociallogin.user.username:
            sociallogin.user.username = _username_from_email(email)

    def is_open_for_signup(self, request, sociallogin):
        return is_email_allowed(_social_login_email(sociallogin))
