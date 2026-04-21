from django.contrib import admin
from django.urls import path
from .models import User, Service, ServiceRequest, Page
from . import views

# Register your models here.

admin.site.register(User)
admin.site.register(Service)
admin.site.register(ServiceRequest)
admin.site.register(Page)

# Customize admin site appearance
admin.site.site_header = "E-Service Administration"
admin.site.site_title = "E-Service Admin"
admin.site.index_title = "Welcome to E-Service Admin Panel"
class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
        ]
        return custom_urls + urls

# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register models with custom admin
custom_admin_site.register(User)
custom_admin_site.register(Service)
custom_admin_site.register(ServiceRequest)
custom_admin_site.register(Page)
