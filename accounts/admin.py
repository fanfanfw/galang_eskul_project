from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'nama_lengkap', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('username', 'nama_lengkap', 'email')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informasi Tambahan', {
            'fields': ('role', 'nama_lengkap', 'no_telepon', 'alamat', 'foto_profil')
        }),
    )
