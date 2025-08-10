from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # User Management
    path('create-user/', views.create_user, name='create_user'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    # Eskul Management
    path('manage-eskul/', views.manage_eskul, name='manage_eskul'),
    path('create-eskul/', views.create_eskul, name='create_eskul'),
    path('edit-eskul/<int:eskul_id>/', views.edit_eskul, name='edit_eskul'),
    path('delete-eskul/<int:eskul_id>/', views.delete_eskul, name='delete_eskul'),
    path('assign-pelatih/<int:eskul_id>/', views.assign_pelatih, name='assign_pelatih'),
]