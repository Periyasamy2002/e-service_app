from django.contrib import admin
from .models import User, Service, ServiceRequest, Page, ContactMessage

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    search_fields = ('username', 'email')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'charges', 'page', 'created_at')
    list_filter = ('page',)
    search_fields = ('name', 'description')

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'service', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'service', 'assigned_to')
    search_fields = ('full_name', 'mobile', 'email')
    readonly_fields = ('created_at', 'updated_at')
    readonly_fields = ('created_at',)

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')