from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('AGENT1', 'Agent1'),
        ('AGENT2', 'Agent2'),
        ('USER', 'User'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')
    mobile = models.CharField(max_length=15, blank=True, null=True)

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Service charges amount")
    documents_required = models.TextField(blank=True, help_text="List of required documents")
    tutorial_link = models.URLField(blank=True, help_text="YouTube or tutorial video link")
    apply_link = models.URLField(blank=True, help_text="Link to apply for this service")
    page = models.ForeignKey('Page', on_delete=models.SET_NULL, null=True, blank=True, related_name='services', help_text="Assign to a specific page")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Page(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Under Review', 'Under Review'),
        ('In Progress', 'In Progress'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True)
    dob = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    aadhaar_number = models.CharField(max_length=12, blank=True)
    photo = models.FileField(upload_to='requests/photos/', null=True, blank=True)
    aadhaar_card = models.FileField(upload_to='requests/aadhaar/', null=True, blank=True)
    pan_card = models.FileField(upload_to='requests/pan/', null=True, blank=True)
    signature = models.FileField(upload_to='requests/signatures/', null=True, blank=True)
    address_proof = models.FileField(upload_to='requests/address_proof/', null=True, blank=True)
    description = models.TextField(blank=True)
    completed_file = models.FileField(upload_to='requests/completed/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.service.name} - {self.status}"
