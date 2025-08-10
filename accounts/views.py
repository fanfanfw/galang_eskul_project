from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import CreateUserForm, EskulForm
from eskul.models import Eskul

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

# === ESKUL MANAGEMENT VIEWS ===
@user_passes_test(is_admin)
def manage_eskul(request):
    eskul_list = Eskul.objects.all().order_by('-created_at')
    return render(request, 'admin/manage_eskul.html', {'eskul_list': eskul_list})

@user_passes_test(is_admin)
def create_eskul(request):
    if request.method == 'POST':
        form = EskulForm(request.POST)
        if form.is_valid():
            eskul = form.save()
            messages.success(request, f'Eskul {eskul.nama_eskul} berhasil dibuat!')
            return redirect('manage_eskul')
    else:
        form = EskulForm()
    
    return render(request, 'admin/create_eskul.html', {'form': form})

@user_passes_test(is_admin)
def edit_eskul(request, eskul_id):
    eskul = get_object_or_404(Eskul, id=eskul_id)
    if request.method == 'POST':
        form = EskulForm(request.POST, instance=eskul)
        if form.is_valid():
            eskul = form.save()
            messages.success(request, f'Eskul {eskul.nama_eskul} berhasil diupdate!')
            return redirect('manage_eskul')
    else:
        form = EskulForm(instance=eskul)
    
    return render(request, 'admin/edit_eskul.html', {'form': form, 'eskul': eskul})

@user_passes_test(is_admin)
def delete_eskul(request, eskul_id):
    try:
        eskul = Eskul.objects.get(id=eskul_id)
        eskul_name = eskul.nama_eskul
        eskul.delete()
        messages.success(request, f'Eskul {eskul_name} berhasil dihapus!')
    except Eskul.DoesNotExist:
        messages.error(request, 'Eskul tidak ditemukan!')
    
    return redirect('manage_eskul')

@user_passes_test(is_admin)
def assign_pelatih(request, eskul_id):
    eskul = get_object_or_404(Eskul, id=eskul_id)
    
    if request.method == 'POST':
        pelatih_id = request.POST.get('pelatih_id')
        if pelatih_id:
            try:
                pelatih = User.objects.get(id=pelatih_id, role='pelatih')
                eskul.pelatih = pelatih
                eskul.save()
                messages.success(request, f'Pelatih {pelatih.nama_lengkap} berhasil ditugaskan ke eskul {eskul.nama_eskul}!')
            except User.DoesNotExist:
                messages.error(request, 'Pelatih tidak ditemukan!')
        return redirect('manage_eskul')
    
    available_pelatih = User.objects.filter(role='pelatih', is_active=True)
    return render(request, 'admin/assign_pelatih.html', {
        'eskul': eskul,
        'available_pelatih': available_pelatih
    })
