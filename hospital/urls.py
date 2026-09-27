from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Patients
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/register/', views.patient_register_view, name='patient_register'),
    path('patients/<str:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('patients/<str:patient_id>/print/', views.patient_print_history_view, name='patient_print_history'),
    
    # Vaccination
    path('patients/<str:patient_id>/vaccinate/', views.vaccination_record_view, name='vaccination_record'),
    path('vaccination/today/', views.today_program_view, name='today_program'),

    # Sessions
    path('sessions/', views.session_list_view, name='session_list'),
    path('sessions/create/', views.session_create_view, name='session_create'),
    path('sessions/<int:session_id>/change-date/', views.session_edit_date_view, name='session_change_date'),

    # Reports
    path('reports/daily-session/', views.daily_session_report_view, name='daily_session_report'),

    # Administration
    path('admin-panel/settings/', views.hospital_settings_view, name='hospital_settings'),
    path('admin-panel/users/', views.user_management_view, name='user_management'),
    path('admin-panel/audit-log/', views.audit_log_view, name='audit_log'),
    path('admin-panel/system-health/', views.system_health_view, name='system_health'),
]
