from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Membuat akun admin default jika belum ada'
    
    def handle(self, *args, **options):
        try:
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@eskul.com',
                password='Scr@pp3r',
                nama_lengkap='Administrator',
                role='admin',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Akun admin berhasil dibuat: {admin_user.username}')
            )
        except IntegrityError:
            self.stdout.write(
                self.style.WARNING('Akun admin sudah ada')
            )