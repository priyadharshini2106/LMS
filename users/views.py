from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import LoginForm


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if getattr(user, 'role', None) == 'admin':
                return redirect('users:admin_dashboard')
            if user.is_superuser:
                return redirect(reverse('admin:index'))
            if getattr(user, 'role', None) == 'teacher':
                return redirect('users:teacher_dashboard')
            if getattr(user, 'role', None) == 'student':
                return redirect('users:student_dashboard')

        return render(request, 'login.html', {'form': form, 'error': 'Invalid credentials'})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('users:login')


@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


@login_required
def teacher_dashboard(request):
    return render(request, 'teacher_dashboard.html')


@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html')

