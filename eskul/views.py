from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Avg
import pandas as pd
import io
from datetime import datetime, timedelta

from .models import Eskul, Siswa, Pertemuan, Absensi, FotoKegiatan
from accounts.models import CustomUser

@login_required
def dashboard_view(request):
    today = timezone.now().date()
    context = {
        'today': today,
        'user': request.user
    }
    
    if request.user.role == 'admin':
        context.update({
            'total_pelatih': CustomUser.objects.filter(role='pelatih').count(),
            'total_eskul': Eskul.objects.count(),
            'total_siswa': Siswa.objects.count(),
            'pertemuan_hari_ini': Pertemuan.objects.filter(tanggal=today).count(),
        })
    elif request.user.role == 'pelatih':
        my_eskul = Eskul.objects.filter(pelatih=request.user)
        context.update({
            'my_eskul_count': my_eskul.count(),
            'my_eskul_list': my_eskul,
            'my_siswa_count': Siswa.objects.filter(eskul__pelatih=request.user).count(),
            'my_pertemuan_count': Pertemuan.objects.filter(pelatih=request.user).count(),
        })
    
    return render(request, 'dashboard.html', context)

@login_required
def admin_manage_students_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Akses ditolak. Anda bukan admin.')
        return redirect('dashboard')
    
    eskul_list = Eskul.objects.all().select_related('pelatih')
    siswa_list = Siswa.objects.all().select_related('eskul')
    
    # Get unique kelas list
    kelas_list = sorted(set(siswa.kelas for siswa in siswa_list))
    
    context = {
        'eskul_list': eskul_list,
        'siswa_list': siswa_list,
        'kelas_list': kelas_list,
        'total_kelas': len(kelas_list),
        'siswa_aktif': siswa_list.filter(is_active=True).count(),
    }
    return render(request, 'admin/manage_students.html', context)

@login_required
def admin_import_students_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Akses ditolak. Anda bukan admin.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        if 'file' in request.FILES:
            return handle_file_upload(request)
        elif 'confirm_import' in request.POST:
            return handle_confirm_import(request)
    
    eskul_list = Eskul.objects.all().select_related('pelatih')
    return render(request, 'admin/import_students.html', {'eskul_list': eskul_list})

def handle_file_upload(request):
    # Debug logging
    print(f"DEBUG: Files uploaded: {list(request.FILES.keys())}")
    print(f"DEBUG: POST data: {dict(request.POST)}")
    
    if 'file' not in request.FILES:
        messages.error(request, 'File tidak ditemukan. Silakan pilih file.')
        return redirect('admin_import_students')
    
    file = request.FILES['file']
    eskul_id = request.POST.get('eskul_id')
    
    print(f"DEBUG: File name: {file.name}, File size: {file.size}")
    print(f"DEBUG: Eskul ID: {eskul_id}")
    
    if not eskul_id:
        messages.error(request, 'Pilih eskul terlebih dahulu.')
        return redirect('admin_import_students')
    
    try:
        eskul = Eskul.objects.get(id=eskul_id)
    except Eskul.DoesNotExist:
        messages.error(request, 'Eskul tidak ditemukan.')
        return redirect('admin_import_students')
    
    try:
        # Read file
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            messages.error(request, 'Format file tidak didukung. Gunakan CSV atau Excel.')
            return redirect('admin_import_students')
        
        # Validate columns
        expected_columns = ['nama_siswa', 'kelas']
        if not all(col in df.columns for col in expected_columns):
            # Try alternative column names
            df.columns = df.columns.str.lower().str.strip()
            column_mapping = {
                'nama': 'nama_siswa',
                'nama siswa': 'nama_siswa',
                'name': 'nama_siswa',
                'class': 'kelas',
                'kelas siswa': 'kelas'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df.rename(columns={old_col: new_col}, inplace=True)
            
            if not all(col in df.columns for col in expected_columns):
                messages.error(request, f'File harus memiliki kolom: {", ".join(expected_columns)}')
                return redirect('admin_import_students')
        
        # Clean and validate data
        df = df.dropna(subset=expected_columns)
        df['nama_siswa'] = df['nama_siswa'].str.strip().str.upper()
        df['kelas'] = df['kelas'].str.strip().str.upper()
        
        # Validate kelas format (1A-6E)
        valid_kelas = [f"{i}{j}" for i in range(1, 7) for j in ['A', 'B', 'C', 'D', 'E']]
        invalid_kelas = df[~df['kelas'].isin(valid_kelas)]
        
        if not invalid_kelas.empty:
            invalid_list = invalid_kelas['kelas'].unique()
            messages.error(request, f'Format kelas tidak valid: {", ".join(invalid_list)}. Gunakan format 1A-6E.')
            return redirect('admin_import_students')
        
        # Check for duplicates in file
        file_duplicates = df[df.duplicated(subset=['nama_siswa', 'kelas'], keep=False)]
        if not file_duplicates.empty:
            messages.error(request, 'Ada siswa duplikat dalam file yang diupload.')
            return redirect('admin_import_students')
        
        # Check for existing students
        existing_students = []
        new_students = []
        
        for _, row in df.iterrows():
            existing = Siswa.objects.filter(
                nama_siswa=row['nama_siswa'], 
                kelas=row['kelas']
            ).first()
            
            if existing:
                existing_students.append({
                    'nama_siswa': row['nama_siswa'],
                    'kelas': row['kelas'],
                    'current_eskul': existing.eskul.nama_eskul
                })
            else:
                new_students.append({
                    'nama_siswa': row['nama_siswa'],
                    'kelas': row['kelas']
                })
        
        # Store data in session for confirmation
        request.session['import_data'] = {
            'eskul_id': eskul_id,
            'eskul_name': eskul.nama_eskul,
            'new_students': new_students,
            'existing_students': existing_students
        }
        
        return render(request, 'admin/preview_import.html', {
            'eskul': eskul,
            'new_students': new_students,
            'existing_students': existing_students,
            'total_new': len(new_students),
            'total_existing': len(existing_students)
        })
        
    except Exception as e:
        messages.error(request, f'Error membaca file: {str(e)}')
        return redirect('admin_import_students')

def handle_confirm_import(request):
    import_data = request.session.get('import_data')
    if not import_data:
        messages.error(request, 'Data import tidak ditemukan. Silakan upload ulang.')
        return redirect('admin_import_students')
    
    try:
        eskul = Eskul.objects.get(id=import_data['eskul_id'])
        new_students = import_data['new_students']
        
        # Create new students
        created_count = 0
        for student_data in new_students:
            Siswa.objects.create(
                nama_siswa=student_data['nama_siswa'],
                kelas=student_data['kelas'],
                eskul=eskul
            )
            created_count += 1
        
        # Clear session data
        del request.session['import_data']
        
        messages.success(request, f'Berhasil menambahkan {created_count} siswa ke {eskul.nama_eskul}.')
        return redirect('admin_manage_students')
        
    except Exception as e:
        messages.error(request, f'Error saat menyimpan data: {str(e)}')
        return redirect('admin_import_students')

@login_required
def admin_delete_student_view(request, student_id):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Akses ditolak'}, status=403)
    
    try:
        siswa = get_object_or_404(Siswa, id=student_id)
        nama = siswa.nama_siswa
        kelas = siswa.kelas
        siswa.delete()
        messages.success(request, f'Siswa {nama} ({kelas}) berhasil dihapus.')
        return redirect('admin_manage_students')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('admin_manage_students')

# PELATIH VIEWS
@login_required
def pelatih_create_pertemuan_view(request):
    if request.user.role != 'pelatih':
        messages.error(request, 'Akses ditolak. Anda bukan pelatih.')
        return redirect('dashboard')
    
    # Get pelatih's eskul
    try:
        eskul = Eskul.objects.get(pelatih=request.user)
    except Eskul.DoesNotExist:
        messages.error(request, 'Anda belum ditugaskan ke eskul manapun.')
        return redirect('dashboard')
    
    # Get siswa list
    siswa_list = Siswa.objects.filter(eskul=eskul, is_active=True).order_by('nama_siswa')
    
    if request.method == 'POST':
        return handle_create_pertemuan(request, eskul, siswa_list)
    
    context = {
        'eskul': eskul,
        'siswa_list': siswa_list,
        'today': timezone.now().date()
    }
    return render(request, 'pelatih/create_pertemuan.html', context)

def handle_create_pertemuan(request, eskul, siswa_list):
    try:
        with transaction.atomic():
            # Get form data
            tanggal = request.POST.get('tanggal')
            materi = request.POST.get('materi_kegiatan')
            
            if not tanggal or not materi.strip():
                messages.error(request, 'Tanggal dan materi kegiatan harus diisi.')
                return redirect('pelatih_create_pertemuan')
            
            # Check if pertemuan already exists for this date
            if Pertemuan.objects.filter(eskul=eskul, tanggal=tanggal).exists():
                messages.error(request, f'Pertemuan untuk tanggal {tanggal} sudah ada. Satu eskul hanya bisa satu pertemuan per hari.')
                return redirect('pelatih_create_pertemuan')
            
            # Create pertemuan
            pertemuan = Pertemuan.objects.create(
                eskul=eskul,
                tanggal=tanggal,
                materi_kegiatan=materi.strip(),
                pelatih=request.user
            )
            
            # Handle multiple photo uploads
            if request.FILES.getlist('foto_kegiatan'):
                for foto in request.FILES.getlist('foto_kegiatan'):
                    FotoKegiatan.objects.create(
                        pertemuan=pertemuan,
                        foto=foto
                    )
            
            # Handle attendance
            hadir_count = 0
            total_siswa = siswa_list.count()
            
            for siswa in siswa_list:
                keterangan = request.POST.get(f'absensi_{siswa.id}', 'alpha')
                hadir = keterangan == 'hadir'
                
                Absensi.objects.create(
                    pertemuan=pertemuan,
                    siswa=siswa,
                    hadir=hadir,
                    keterangan=keterangan
                )
                
                if hadir:
                    hadir_count += 1
            
            messages.success(request, 
                f'Pertemuan berhasil disimpan! {hadir_count}/{total_siswa} siswa hadir.')
            return redirect('pelatih_history_pertemuan')
            
    except Exception as e:
        messages.error(request, f'Error menyimpan pertemuan: {str(e)}')
        return redirect('pelatih_create_pertemuan')

@login_required
def pelatih_history_pertemuan_view(request):
    if request.user.role != 'pelatih':
        messages.error(request, 'Akses ditolak. Anda bukan pelatih.')
        return redirect('dashboard')
    
    try:
        eskul = Eskul.objects.get(pelatih=request.user)
    except Eskul.DoesNotExist:
        messages.error(request, 'Anda belum ditugaskan ke eskul manapun.')
        return redirect('dashboard')
    
    pertemuan_list = Pertemuan.objects.filter(
        eskul=eskul
    ).prefetch_related('foto_list', 'absensi_list__siswa')
    
    context = {
        'eskul': eskul,
        'pertemuan_list': pertemuan_list
    }
    return render(request, 'pelatih/history_pertemuan.html', context)

# ADMIN REPORT VIEWS
@login_required
def admin_attendance_report_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Akses ditolak. Anda bukan admin.')
        return redirect('dashboard')
    
    # Get filter parameters
    eskul_id = request.GET.get('eskul')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    kelas = request.GET.get('kelas')
    
    # Base queryset
    siswa_list = Siswa.objects.filter(is_active=True).select_related('eskul')
    absensi_query = Absensi.objects.select_related('siswa', 'pertemuan')
    
    # Apply filters
    if eskul_id:
        siswa_list = siswa_list.filter(eskul_id=eskul_id)
        absensi_query = absensi_query.filter(siswa__eskul_id=eskul_id)
    
    if kelas:
        siswa_list = siswa_list.filter(kelas=kelas)
        absensi_query = absensi_query.filter(siswa__kelas=kelas)
        
    if start_date:
        absensi_query = absensi_query.filter(pertemuan__tanggal__gte=start_date)
        
    if end_date:
        absensi_query = absensi_query.filter(pertemuan__tanggal__lte=end_date)
    
    # Calculate attendance statistics
    attendance_data = []
    for siswa in siswa_list:
        siswa_absensi = absensi_query.filter(siswa=siswa)
        total_pertemuan = siswa_absensi.count()
        hadir = siswa_absensi.filter(keterangan='hadir').count()
        sakit = siswa_absensi.filter(keterangan='sakit').count()
        izin = siswa_absensi.filter(keterangan='izin').count()
        alpha = siswa_absensi.filter(keterangan='alpha').count()
        
        persentase_hadir = (hadir / total_pertemuan * 100) if total_pertemuan > 0 else 0
        
        attendance_data.append({
            'siswa': siswa,
            'total_pertemuan': total_pertemuan,
            'hadir': hadir,
            'sakit': sakit,
            'izin': izin,
            'alpha': alpha,
            'persentase_hadir': round(persentase_hadir, 2)
        })
    
    # Sort by attendance percentage (descending)
    attendance_data.sort(key=lambda x: x['persentase_hadir'], reverse=True)
    
    # Calculate attendance statistics
    good_attendance_count = len([d for d in attendance_data if d['persentase_hadir'] >= 80])
    medium_attendance_count = len([d for d in attendance_data if 60 <= d['persentase_hadir'] < 80])
    poor_attendance_count = len([d for d in attendance_data if d['persentase_hadir'] < 60])
    
    context = {
        'attendance_data': attendance_data,
        'good_attendance_count': good_attendance_count,
        'medium_attendance_count': medium_attendance_count,
        'poor_attendance_count': poor_attendance_count,
        'eskul_list': Eskul.objects.all(),
        'kelas_list': sorted(set(Siswa.objects.values_list('kelas', flat=True))),
        'filters': {
            'eskul_id': eskul_id,
            'start_date': start_date,
            'end_date': end_date,
            'kelas': kelas
        }
    }
    
    return render(request, 'admin/attendance_report.html', context)

@login_required
def admin_pertemuan_report_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Akses ditolak. Anda bukan admin.')
        return redirect('dashboard')
    
    # Get filter parameters
    pelatih_id = request.GET.get('pelatih')
    eskul_id = request.GET.get('eskul')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base queryset
    pertemuan_list = Pertemuan.objects.select_related('eskul', 'pelatih').prefetch_related('foto_list', 'absensi_list')
    
    # Apply filters
    if pelatih_id:
        pertemuan_list = pertemuan_list.filter(pelatih_id=pelatih_id)
    
    if eskul_id:
        pertemuan_list = pertemuan_list.filter(eskul_id=eskul_id)
        
    if start_date:
        pertemuan_list = pertemuan_list.filter(tanggal__gte=start_date)
        
    if end_date:
        pertemuan_list = pertemuan_list.filter(tanggal__lte=end_date)
    
    pertemuan_list = pertemuan_list.order_by('-tanggal')
    
    # Calculate statistics for each pertemuan
    pertemuan_data = []
    for pertemuan in pertemuan_list:
        absensi_stats = pertemuan.absensi_list.aggregate(
            total=Count('id'),
            hadir=Count('id', filter=Q(keterangan='hadir')),
            sakit=Count('id', filter=Q(keterangan='sakit')),
            izin=Count('id', filter=Q(keterangan='izin')),
            alpha=Count('id', filter=Q(keterangan='alpha'))
        )
        
        persentase_hadir = (absensi_stats['hadir'] / absensi_stats['total'] * 100) if absensi_stats['total'] > 0 else 0
        
        pertemuan_data.append({
            'pertemuan': pertemuan,
            'stats': absensi_stats,
            'persentase_hadir': round(persentase_hadir, 2),
            'foto_count': pertemuan.foto_list.count()
        })
    
    # Calculate aggregate statistics
    total_foto_count = sum([data['foto_count'] for data in pertemuan_data])
    rata_rata_kehadiran = sum([data['persentase_hadir'] for data in pertemuan_data]) / len(pertemuan_data) if pertemuan_data else 0
    
    context = {
        'pertemuan_data': pertemuan_data,
        'total_foto_count': total_foto_count,
        'rata_rata_kehadiran': rata_rata_kehadiran,
        'pelatih_list': CustomUser.objects.filter(role='pelatih'),
        'eskul_list': Eskul.objects.all(),
        'filters': {
            'pelatih_id': pelatih_id,
            'eskul_id': eskul_id,
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return render(request, 'admin/pertemuan_report.html', context)

@login_required
def export_attendance_excel(request):
    if request.user.role != 'admin':
        return HttpResponse('Akses ditolak', status=403)
    
    # Get same filter parameters
    eskul_id = request.GET.get('eskul')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    kelas = request.GET.get('kelas')
    
    # Apply same filters as in report view
    siswa_list = Siswa.objects.filter(is_active=True).select_related('eskul')
    absensi_query = Absensi.objects.select_related('siswa', 'pertemuan')
    
    if eskul_id:
        siswa_list = siswa_list.filter(eskul_id=eskul_id)
        absensi_query = absensi_query.filter(siswa__eskul_id=eskul_id)
    
    if kelas:
        siswa_list = siswa_list.filter(kelas=kelas)
        absensi_query = absensi_query.filter(siswa__kelas=kelas)
        
    if start_date:
        absensi_query = absensi_query.filter(pertemuan__tanggal__gte=start_date)
        
    if end_date:
        absensi_query = absensi_query.filter(pertemuan__tanggal__lte=end_date)
    
    # Prepare data for Excel
    data = []
    for siswa in siswa_list:
        siswa_absensi = absensi_query.filter(siswa=siswa)
        total_pertemuan = siswa_absensi.count()
        hadir = siswa_absensi.filter(keterangan='hadir').count()
        sakit = siswa_absensi.filter(keterangan='sakit').count()
        izin = siswa_absensi.filter(keterangan='izin').count()
        alpha = siswa_absensi.filter(keterangan='alpha').count()
        
        persentase_hadir = (hadir / total_pertemuan * 100) if total_pertemuan > 0 else 0
        
        data.append({
            'Nama Siswa': siswa.nama_siswa,
            'Kelas': siswa.kelas,
            'Eskul': siswa.eskul.nama_eskul,
            'Pelatih': siswa.eskul.pelatih.nama_lengkap,
            'Total Pertemuan': total_pertemuan,
            'Hadir': hadir,
            'Sakit': sakit,
            'Izin': izin,
            'Alpha': alpha,
            'Persentase Kehadiran (%)': round(persentase_hadir, 2)
        })
    
    # Create Excel file
    df = pd.DataFrame(data)
    
    # Create HTTP response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'laporan_kehadiran_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Write to Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Laporan Kehadiran', index=False)
    
    return response

@login_required
def export_pertemuan_excel(request):
    if request.user.role != 'admin':
        return HttpResponse('Akses ditolak', status=403)
    
    # Get filter parameters
    pelatih_id = request.GET.get('pelatih')
    eskul_id = request.GET.get('eskul')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Apply filters
    pertemuan_list = Pertemuan.objects.select_related('eskul', 'pelatih').prefetch_related('absensi_list')
    
    if pelatih_id:
        pertemuan_list = pertemuan_list.filter(pelatih_id=pelatih_id)
    
    if eskul_id:
        pertemuan_list = pertemuan_list.filter(eskul_id=eskul_id)
        
    if start_date:
        pertemuan_list = pertemuan_list.filter(tanggal__gte=start_date)
        
    if end_date:
        pertemuan_list = pertemuan_list.filter(tanggal__lte=end_date)
    
    # Prepare data
    data = []
    for pertemuan in pertemuan_list:
        absensi_stats = pertemuan.absensi_list.aggregate(
            total=Count('id'),
            hadir=Count('id', filter=Q(keterangan='hadir')),
            sakit=Count('id', filter=Q(keterangan='sakit')),
            izin=Count('id', filter=Q(keterangan='izin')),
            alpha=Count('id', filter=Q(keterangan='alpha'))
        )
        
        persentase_hadir = (absensi_stats['hadir'] / absensi_stats['total'] * 100) if absensi_stats['total'] > 0 else 0
        
        data.append({
            'Tanggal': pertemuan.tanggal.strftime('%Y-%m-%d'),
            'Eskul': pertemuan.eskul.nama_eskul,
            'Pelatih': pertemuan.pelatih.nama_lengkap,
            'Materi Kegiatan': pertemuan.materi_kegiatan[:100] + '...' if len(pertemuan.materi_kegiatan) > 100 else pertemuan.materi_kegiatan,
            'Total Siswa': absensi_stats['total'],
            'Hadir': absensi_stats['hadir'],
            'Sakit': absensi_stats['sakit'],
            'Izin': absensi_stats['izin'],
            'Alpha': absensi_stats['alpha'],
            'Persentase Kehadiran (%)': round(persentase_hadir, 2),
            'Jumlah Foto': pertemuan.foto_list.count()
        })
    
    # Create Excel file
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'laporan_pertemuan_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Laporan Pertemuan', index=False)
    
    return response