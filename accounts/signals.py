from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    if sender.name == 'accounts':
        try:
            if not User.objects.filter(username='admin').exists():
                admin_user = User.objects.create_user(
                    username='admin',
                    email='admin@eskul.com',
                    password='Scr@pp3r',
                    nama_lengkap='Administrator',
                    role='admin',
                    is_staff=True,
                    is_superuser=True
                )
                print(f'Akun admin default berhasil dibuat: {admin_user.username}')
        except IntegrityError:
            print('Akun admin sudah ada')