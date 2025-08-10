from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import CreateUserForm

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })

@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Akun pelatih {user.nama_lengkap} berhasil dibuat!')
            return redirect('manage_users')
    else:
        form = CreateUserForm()
    
    return render(request, 'admin/create_user.html', {'form': form})

@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.filter(role='pelatih').order_by('-created_at')
    return render(request, 'admin/manage_users.html', {'users': users})

@user_passes_test(is_admin)
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id, role='pelatih')
        user_name = user.nama_lengkap
        user.delete()
        messages.success(request, f'Akun pelatih {user_name} berhasil dihapus!')
    except User.DoesNotExist:
        messages.error(request, 'User tidak ditemukan!')
    
    return redirect('manage_users')
