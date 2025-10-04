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
    if request.method == 'POST':
        user = request.user
        user.nama_lengkap = request.POST.get('nama_lengkap')
        user.email = request.POST.get('email')
        user.no_telepon = request.POST.get('no_telepon')
        user.alamat = request.POST.get('alamat')

        # Handle password change if provided
        password = request.POST.get('password')
        if password:
            user.set_password(password)
            # Update session to keep user logged in
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)

        # Handle profile photo upload
        if 'foto_profil' in request.FILES:
            user.foto_profil = request.FILES['foto_profil']

        try:
            user.save()
            messages.success(request, 'Profil berhasil diperbarui!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

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
def edit_user(request, user_id):
    try:
        user = User.objects.get(id=user_id, role='pelatih')
    except User.DoesNotExist:
        messages.error(request, 'User tidak ditemukan!')
        return redirect('manage_users')

    if request.method == 'POST':
        # Get form data
        user.nama_lengkap = request.POST.get('nama_lengkap')
        user.email = request.POST.get('email')
        user.no_telepon = request.POST.get('no_telepon')
        user.alamat = request.POST.get('alamat')

        # Handle password change if provided
        password = request.POST.get('password')
        if password:
            user.set_password(password)

        # Handle profile photo upload
        if 'foto_profil' in request.FILES:
            user.foto_profil = request.FILES['foto_profil']

        # Handle active status
        user.is_active = request.POST.get('is_active') == 'on'

        try:
            user.save()
            messages.success(request, f'Data pelatih {user.nama_lengkap} berhasil diperbarui!')
            return redirect('manage_users')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'admin/edit_user.html', {'edited_user': user})

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
            eskul = form.save(commit=False)
            eskul.full_clean()  # Run model validation
            eskul.save()
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
            eskul = form.save(commit=False)
            eskul.full_clean()  # Run model validation
            eskul.save()
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

                # Check if pelatih already has another eskul
                existing_eskul = Eskul.objects.filter(pelatih=pelatih).exclude(pk=eskul.pk)
                if existing_eskul.exists():
                    existing_eskul_name = existing_eskul.first().nama_eskul
                    messages.error(request, f'{pelatih.nama_lengkap} sudah menjadi pelatih untuk eskul {existing_eskul_name}. Satu pelatih hanya bisa menangani satu eskul.')
                    return render(request, 'admin/assign_pelatih.html', {
                        'eskul': eskul,
                        'available_pelatih': User.objects.filter(role='pelatih', is_active=True)
                    })

                eskul.pelatih = pelatih
                eskul.save()
                messages.success(request, f'Pelatih {pelatih.nama_lengkap} berhasil ditugaskan ke eskul {eskul.nama_eskul}!')
            except User.DoesNotExist:
                messages.error(request, 'Pelatih tidak ditemukan!')
        return redirect('manage_eskul')

    # Filter pelatih yang belum memiliki eskul atau sedang menjadi pelatih eskul ini
    # Get all active pelatih
    base_pelatih = User.objects.filter(role='pelatih', is_active=True)

    # Get pelatih yang sudah punya eskul
    used_pelatih_ids = Eskul.objects.filter(pelatih__isnull=False).exclude(pk=eskul.pk).values_list('pelatih_id', flat=True)

    if eskul.pelatih:
        # If current eskul has a pelatih, show all pelatih including current one
        # but exclude those who are assigned to other eskuls (not current one)
        available_pelatih = base_pelatih.exclude(id__in=used_pelatih_ids)
    else:
        # If no current pelatih, only show pelatih without eskul
        available_pelatih = base_pelatih.exclude(id__in=used_pelatih_ids)

    return render(request, 'admin/assign_pelatih.html', {
        'eskul': eskul,
        'available_pelatih': available_pelatih
    })
