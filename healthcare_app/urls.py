from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('appointment/', views.book_appointment, name='book_appointment'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointment/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    
    # -- Patient Management --
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/create/', views.patient_create, name='patient_create'),
    
    # -- Auth --
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='healthcare_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('doctor/register/', views.doctor_register, name='doctor_register'),
    path('doctor/login/', auth_views.LoginView.as_view(template_name='healthcare_app/doctor_login.html'), name='doctor_login'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointment/done/<int:appointment_id>/', views.mark_checkup_done, name='mark_checkup_done'),
    path('doctor/clear_completed/', views.clear_completed_checkups, name='clear_completed_checkups'),


    path('', views.index, name='home'),
    path('lab_tests/', views.lab_tests, name='lab_tests'),
    path('lab_tests/book/<int:test_id>/', views.book_lab_test, name='book_lab_test'),
    path('buy_medicine/', views.buy_medicine, name='buy_medicine'),
    path('health_articles/', views.health_articles, name='health_articles'),
    path('articles/<int:article_id>/', views.article_detail, name='article_detail'),
    path('order_details/', views.order_details, name='order_details'),
    path('doctor_list/', views.doctor_list, name='doctor_list'),
    path('medicine/order/<int:medicine_id>/', views.order_medicine, name='order_medicine'),
    path('medicine/order/cancel/<int:order_id>/', views.cancel_medicine_order, name='cancel_medicine_order'),
    path('medicine/order/clear/', views.clear_order_entries, name='clear_order_entries'),
    path('external_health_articles/', views.fetch_trending_articles_gnews, name='external_health_articles'),
    path('patients/edit/<int:patient_id>/', views.patient_edit, name='patient_edit'),
    path('patients/delete/<int:patient_id>/', views.patient_delete, name='patient_delete'),
    path('profile/', views.patient_profile, name='patient_profile'),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),
    path('appointments/clear_completed/', views.clear_completed_appointments, name='clear_completed_appointments'),
    
]
