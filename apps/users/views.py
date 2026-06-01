from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.users.forms import AllowedUserForm
from apps.users.models import AllowedUser, is_user_module_admin


def user_module_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_user_module_admin(request.user):
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


@user_module_admin_required
def user_list(request):
    allowed_users = AllowedUser.objects.all()
    form = AllowedUserForm()
    if request.method == 'POST':
        form = AllowedUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User added to the login whitelist.')
            return redirect('users:list')
    return render(
        request,
        'users/user_list.html',
        {
            'allowed_users': allowed_users,
            'form': form,
        },
    )


@user_module_admin_required
@require_POST
def user_delete(request, pk):
    allowed_user = get_object_or_404(AllowedUser, pk=pk)
    allowed_user.delete()
    messages.success(request, 'User removed from the login whitelist.')
    return redirect('users:list')
