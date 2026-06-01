from apps.users.models import is_user_module_admin


def user_module_nav(request):
    return {
        'show_user_module': is_user_module_admin(request.user),
    }
