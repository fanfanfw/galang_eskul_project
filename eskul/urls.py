from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    
    # Admin URLs
    path('admin/students/', views.admin_manage_students_view, name='admin_manage_students'),
    path('admin/students/import/', views.admin_import_students_view, name='admin_import_students'),
    path('admin/students/delete/<int:student_id>/', views.admin_delete_student_view, name='admin_delete_student'),
    
    # Admin Reports
    path('admin/reports/attendance/', views.admin_attendance_report_view, name='admin_attendance_report'),
    path('admin/reports/pertemuan/', views.admin_pertemuan_report_view, name='admin_pertemuan_report'),
    path('admin/export/attendance/', views.export_attendance_excel, name='export_attendance_excel'),
    path('admin/export/pertemuan/', views.export_pertemuan_excel, name='export_pertemuan_excel'),
    
    # Pelatih URLs
    path('pelatih/pertemuan/create/', views.pelatih_create_pertemuan_view, name='pelatih_create_pertemuan'),
    path('pelatih/pertemuan/history/', views.pelatih_history_pertemuan_view, name='pelatih_history_pertemuan'),
]