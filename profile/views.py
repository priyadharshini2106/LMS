from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from users.models import CustomUser
from .forms import ProfileForm

@login_required
def view_profile(request):
    return render(request, 'profile/profile_view.html')

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('view_profile')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'profile/profile_edit.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('view_profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'profile/change_password.html', {'form': form})
