from django.conf import settings
from django.db import models


class AllowedUser(models.Model):
    name = models.CharField(max_length=200)
    google_email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name', 'google_email']

    def __str__(self):
        return f'{self.name} ({self.google_email})'

    def save(self, *args, **kwargs):
        if self.google_email:
            self.google_email = self.google_email.strip().lower()
        super().save(*args, **kwargs)


def get_user_module_admin_email() -> str:
    return getattr(settings, 'USER_MODULE_ADMIN_EMAIL', 'clu@taxnova.ca').lower().strip()


def is_user_module_admin(user) -> bool:
    if not user.is_authenticated:
        return False
    email = (user.email or '').lower().strip()
    return email == get_user_module_admin_email()


def is_email_allowed(email: str) -> bool:
    if not email:
        return False
    normalized = email.lower().strip()
    if normalized == get_user_module_admin_email():
        return True
    return AllowedUser.objects.filter(google_email=normalized, is_active=True).exists()
