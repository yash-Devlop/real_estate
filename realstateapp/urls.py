from django.urls import path
from realstateapp import views

urlpatterns = [
    # Main site templates
    path('', views.index, name='index'),
    path('contact/', views.contact, name='contact'),
    path('properties/', views.properties, name='properties'),
    path('property/<uuid:property_id>/', views.apartment_detail_view, name='apartment_detail'),
    path('signup/', views.user_signup, name='signup'),
    path('api/send_otp_email/', views.send_email_otp, name='send_otp'),
    path('login/', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='logout'),

    # Admin templates
    path('admin/dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('admin/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/add-category/', views.admin_add_category, name='add_category'),
    path('admin/add-property/', views.admin_add_property, name='add_property'),
    path('admin/add-sub-category/', views.admin_add_sub_category, name='add_sub_category'),
    path('admin/all-property/', views.admin_all_property, name='all_property'),
    path('admin/banner-management/', views.admin_banner_management, name='banner_management'),
    path('admin/bookings/', views.admin_booking, name='bookings'),
    path('admin/change-password/', views.admin_change_password, name='change_password'),
    path('admin/contact-inquiry/', views.admin_contact_inquiry, name='contact_inquiry'),
    path('admin/dashboard/', views.admin_dashboard, name='dashboard'),
    path('scheduled-visits/', views.scheduled_visits_view, name='scheduled_visits'),
    path('approve-visit/<uuid:visit_id>/', views.approve_visit, name='approve_visit'),
    path('update-visit/', views.update_visit, name='update_visit'),
    path('apartments/edit/<uuid:property_id>/', views.edit_apartment_view, name='edit_apartment'),
    path('apartments/brochure-image/delete/<int:image_id>/', views.delete_brochure_image, name='delete_brochure_image'),
    
    #extra button paths
    path('admin/delete-property/<uuid:property_id>/', views.delete_apartment, name='delete_apartment'),
    path('admin/update-status/', views.update_apartment_status, name='update_apartment_status'),
    path('admin/book-apartment/', views.book_apartment_view, name='book_apartment'),
    path('admin/delete-property/<uuid:property_id>/', views.delete_apartment_view, name='delete_property'),

    #chart data
    path('admin/bookings-monthly-data/', views.bookings_monthly_data, name='bookings_monthly_data'),
    path('admin/monthly-summary/', views.monthly_summary_view, name='monthly_summary'),

]


