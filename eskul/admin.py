from django.contrib import admin
from .models import Eskul, Siswa, Pertemuan, Absensi, FotoKegiatan

@admin.register(Eskul)
class EskulAdmin(admin.ModelAdmin):
    list_display = ('nama_eskul', 'pelatih', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('nama_eskul', 'pelatih__nama_lengkap')

@admin.register(Siswa)
class SiswaAdmin(admin.ModelAdmin):
    list_display = ('nama_siswa', 'kelas', 'eskul', 'is_active', 'created_at')
    list_filter = ('kelas', 'eskul', 'is_active')
    search_fields = ('nama_siswa', 'kelas')

@admin.register(Pertemuan)
class PertemuanAdmin(admin.ModelAdmin):
    list_display = ('eskul', 'tanggal', 'pelatih', 'created_at')
    list_filter = ('tanggal', 'eskul', 'pelatih')
    search_fields = ('eskul__nama_eskul', 'materi_kegiatan')
    date_hierarchy = 'tanggal'

@admin.register(FotoKegiatan)
class FotoKegiatanAdmin(admin.ModelAdmin):
    list_display = ('pertemuan', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at', 'pertemuan__eskul')
    search_fields = ('caption', 'pertemuan__eskul__nama_eskul')

@admin.register(Absensi)
class AbsensiAdmin(admin.ModelAdmin):
    list_display = ('siswa', 'pertemuan', 'keterangan', 'hadir')
    list_filter = ('keterangan', 'hadir', 'pertemuan__tanggal')
    search_fields = ('siswa__nama_siswa', 'pertemuan__eskul__nama_eskul')
