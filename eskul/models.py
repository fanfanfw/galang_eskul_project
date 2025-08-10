from django.db import models
from django.conf import settings

class Eskul(models.Model):
    nama_eskul = models.CharField(max_length=100)
    deskripsi = models.TextField()
    pelatih = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, limit_choices_to={'role': 'pelatih'}, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nama_eskul

class Siswa(models.Model):
    nama_siswa = models.CharField(max_length=100)
    kelas = models.CharField(max_length=10)
    eskul = models.ForeignKey(Eskul, on_delete=models.CASCADE, related_name='siswa_list')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['nama_siswa', 'kelas']
        
    def __str__(self):
        return f"{self.nama_siswa} - {self.kelas}"

class Pertemuan(models.Model):
    eskul = models.ForeignKey(Eskul, on_delete=models.CASCADE, related_name='pertemuan_list')
    tanggal = models.DateField()
    materi_kegiatan = models.TextField()
    pelatih = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-tanggal']
        unique_together = ['eskul', 'tanggal']
    
    def __str__(self):
        return f"{self.eskul.nama_eskul} - {self.tanggal}"

class FotoKegiatan(models.Model):
    pertemuan = models.ForeignKey(Pertemuan, on_delete=models.CASCADE, related_name='foto_list')
    foto = models.ImageField(upload_to='kegiatan/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Foto {self.pertemuan} - {self.uploaded_at.strftime('%H:%M')}"

class Absensi(models.Model):
    pertemuan = models.ForeignKey(Pertemuan, on_delete=models.CASCADE, related_name='absensi_list')
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE)
    hadir = models.BooleanField(default=False)
    keterangan = models.CharField(max_length=20, choices=[
        ('hadir', 'Hadir'),
        ('sakit', 'Sakit'),
        ('izin', 'Izin'),
        ('alpha', 'Alpha'),
    ], default='alpha')
    
    class Meta:
        unique_together = ['pertemuan', 'siswa']
    
    def __str__(self):
        return f"{self.siswa.nama_siswa} - {self.pertemuan.tanggal} - {self.keterangan}"
