from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('pelatih', 'Pelatih'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='pelatih')
    nama_lengkap = models.CharField(max_length=100)
    no_telepon = models.CharField(max_length=15, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    foto_profil = models.ImageField(upload_to='profil/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nama_lengkap} ({self.get_role_display()})"
