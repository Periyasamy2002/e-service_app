# DEVELOPER INTEGRATION GUIDE

## Overview
This guide explains how to integrate the new service card component and features into different parts of the application.

---

## 1. REUSABLE SERVICE CARDS COMPONENT

### Location
`services/templates/components/service_cards.html`

### How to Use

**In any template (agent pages, user dashboard, etc.):**

```django
{% load static %}

<!-- Include the component -->
{% include 'components/service_cards.html' with services=services %}
```

### Required Context Variable
Your view must pass `services` to the template:

```python
from .models import Service

def your_view(request):
    services = Service.objects.all()
    return render(request, 'your_template.html', {
        'services': services
    })
```

### Optional Filtering
You can pass filtered services:

```python
# Only services assigned to a specific page
services = Service.objects.filter(page__id=page_id)

# Or all services
services = Service.objects.all()

# Or services for a specific agent
services = Service.objects.filter(page__assigned_to=request.user)
```

---

## 2. AGENT PAGES - SERVICE DISPLAY

### For Agent1 Dashboard

**File:** `services/templates/agent1-site/base-agent1.html`

Add this to show available services:

```django
{% block services_section %}
<div style="margin: 30px 0;">
    <h2>Available Services for Processing</h2>
    {% include 'components/service_cards.html' with services=services %}
</div>
{% endblock %}
```

**In views.py (agent1 view):**

```python
@login_required
def agent1_dashboard(request):
    # Get services assigned to this agent
    services = Service.objects.all()
    
    context = {
        'services': services,
        'assigned_requests': ServiceRequest.objects.filter(
            assigned_to=request.user
        ),
    }
    return render(request, 'agent1-site/dashboard.html', context)
```

---

## 3. USER DASHBOARD - SERVICE TRACKING

### File:** `services/templates/user-site/dashboard.html`

Show services user has applied for:

```django
<div class="dashboard-section">
    <h2>Your Applied Services</h2>
    {% include 'components/service_cards.html' with services=user_services %}
</div>
```

**In views.py:**

```python
@login_required
def user_dashboard(request):
    # Get services user has applied for
    applied_services = Service.objects.filter(
        servicerequest__user=request.user
    ).distinct()
    
    context = {
        'user_services': applied_services,
        'requests': ServiceRequest.objects.filter(user=request.user),
    }
    return render(request, 'user-site/dashboard.html', context)
```

---

## 4. CUSTOM PAGES - SERVICE ASSIGNMENT

### How It Works

When creating a page, you can assign services to it:

**In admin form:**
```
Page Name: "Driving License Services"
Services assigned: Driving License Test, Renewal, DL Issues
```

**To fetch services for a page:**

```python
def view_custom_page(request, page_id):
    page = get_object_or_404(Page, id=page_id)
    services = Service.objects.filter(page=page)
    
    return render(request, 'dynamic_page.html', {
        'page': page,
        'services': services,
    })
```

**In template:**
```django
<h1>{{ page.title }}</h1>
<p>{{ page.description }}</p>

{% include 'components/service_cards.html' with services=services %}
```

---

## 5. SEARCH & FILTER IMPLEMENTATION

### Add Search to Service Page

**In views.py:**

```python
def services(request):
    services = Service.objects.all()
    
    # Search functionality
    query = request.GET.get('search')
    if query:
        services = services.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Filter by page
    page_id = request.GET.get('page_id')
    if page_id:
        services = services.filter(page_id=page_id)
    
    # Filter by price range
    max_price = request.GET.get('max_price')
    if max_price:
        services = services.filter(charges__lte=float(max_price))
    
    context = {
        'services': services,
        'pages': Page.objects.all(),
    }
    return render(request, 'serivce.html', context)
```

**In template:**

```django
<div class="filters">
    <form method="get">
        <input type="text" name="search" placeholder="Search services...">
        <select name="page_id">
            <option value="">All Pages</option>
            {% for page in pages %}
            <option value="{{ page.id }}">{{ page.title }}</option>
            {% endfor %}
        </select>
        <input type="number" name="max_price" placeholder="Max Price">
        <button type="submit">Search</button>
    </form>
</div>

{% include 'components/service_cards.html' with services=services %}
```

---

## 6. EXTERNAL LINK BEHAVIOR

### How Apply & Tutorial Links Work

**Apply Link:**
- If `service.apply_link` is set → Opens external URL in new tab
- If not set + user logged in → Uses internal apply form
- If not set + user not logged in → Shows login prompt

**Tutorial Link:**
- Always opens in new tab
- Only shows button if link is provided
- Great for YouTube, Vimeo, or other video platforms

**Implementation:**

```django
<!-- In service cards -->
{% if service.apply_link %}
    <a href="{{ service.apply_link }}" target="_blank" class="service-btn">
        📝 Apply
    </a>
{% elif user.is_authenticated %}
    <a href="{% url 'apply_service' service.id %}" class="service-btn">
        📝 Apply
    </a>
{% else %}
    <button class="service-btn" onclick="alert('Please login')">
        📝 Apply
    </button>
{% endif %}
```

---

## 7. STYLING CUSTOMIZATION

### Component Styles

The service cards component includes built-in CSS. To customize:

**Override in your template:**

```django
<style>
    /* Change card background */
    .service-card {
        background: #your-color;
    }
    
    /* Change header gradient */
    .service-header {
        background: linear-gradient(135deg, #color1 0%, #color2 100%);
    }
    
    /* Change button color */
    .service-btn {
        background: #your-button-color;
    }
</style>

{% include 'components/service_cards.html' with services=services %}
```

---

## 8. DATA STRUCTURE

### Service Object Properties

```python
service.id                      # Auto-generated ID
service.name                    # Service name (e.g., "Passport")
service.description             # Full description text
service.charges                 # Decimal (e.g., 500.00)
service.documents_required      # Multi-line text
service.tutorial_link           # URL (e.g., youtube.com/...)
service.apply_link              # URL (e.g., external form)
service.page                    # Reference to Page object
service.page.title              # Page name (if assigned)
service.page.id                 # Page ID (if assigned)
service.created_at              # DateTime of creation
```

### Example Usage in Template

```django
{{ service.name }}                          <!-- "Passport" -->
{{ service.charges }}                       <!-- "500.00" -->
{{ service.documents_required|linebreaks }} <!-- Formatted text -->
{{ service.page.title }}                    <!-- "Travel Services" -->
{{ service.created_at|date:"Y-m-d" }}      <!-- "2026-04-20" -->
```

---

## 9. DATABASE QUERIES

### Common Queries

```python
from .models import Service, Page

# All services
services = Service.objects.all()

# Services for a specific page
services = Service.objects.filter(page__id=page_id)

# Services with charges
services = Service.objects.filter(charges__gt=0)

# Services with tutorial
services = Service.objects.filter(tutorial_link__isnull=False)

# Recent services
services = Service.objects.order_by('-created_at')[:10]

# Services with external apply link
services = Service.objects.filter(apply_link__isnull=False)

# Count services by page
from django.db.models import Count
page_stats = Page.objects.annotate(service_count=Count('services'))
```

---

## 10. PERFORMANCE TIPS

### Optimize Queries

```python
# Use select_related for foreign keys
services = Service.objects.select_related('page').all()

# Use prefetch_related for reverse relations
pages = Page.objects.prefetch_related('services').all()

# Limit results for dashboard
services = Service.objects.all()[:6]  # Only show 6

# Cache frequently accessed data
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache for 5 minutes
def services_list(request):
    services = Service.objects.all()
    return render(request, 'serivce.html', {'services': services})
```

---

## 11. ADMIN CUSTOMIZATION

### Admin Interface (services/admin.py)

```python
from django.contrib import admin
from .models import Service, Page

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'charges', 'page', 'created_at']
    list_filter = ['page', 'charges', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description')
        }),
        ('Details', {
            'fields': ('charges', 'documents_required', 'page')
        }),
        ('Links', {
            'fields': ('tutorial_link', 'apply_link')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    readonly_fields = ['created_at']
```

---

## 12. TESTING

### Test Cases

```python
from django.test import TestCase
from .models import Service, Page

class ServiceTestCase(TestCase):
    def setUp(self):
        self.page = Page.objects.create(
            title="Test Page",
            description="Test Description"
        )
        self.service = Service.objects.create(
            name="Test Service",
            description="Test",
            charges=500,
            page=self.page
        )
    
    def test_service_creation(self):
        self.assertEqual(self.service.name, "Test Service")
        self.assertEqual(self.service.charges, 500)
    
    def test_service_page_assignment(self):
        self.assertEqual(self.service.page.title, "Test Page")
    
    def test_service_display(self):
        response = self.client.get('/services/')
        self.assertContains(response, 'Test Service')
```

---

## 🎓 COMPLETE WORKFLOW EXAMPLE

### Creating a Multi-Service Page

**1. Create Page:**
```
Title: "Travel & Immigration"
Description: "Services for travel and visa assistance"
```

**2. Create Services for this Page:**
- Passport Service (₹500)
- Visa Assistance (₹1000)
- Travel Insurance (₹300)

**3. Create View:**
```python
def travel_services(request):
    page = get_object_or_404(Page, title="Travel & Immigration")
    services = page.services.all()
    
    return render(request, 'travel_page.html', {
        'page': page,
        'services': services,
    })
```

**4. Create Template:**
```django
<h1>{{ page.title }}</h1>
<p>{{ page.description }}</p>

{% include 'components/service_cards.html' with services=services %}
```

**5. Result:** Beautiful service cards displayed for Travel page!

---

## 📞 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Services not showing | Check if passed to template context |
| Cards display wrong | Verify CSS is not overridden |
| Apply button broken | Check apply_link URL format |
| Tutorial button missing | Ensure tutorial_link is set in admin |
| Page not assigned | Use dropdown in Add Service form |
| Database error | Run `python manage.py migrate` |

---

**Last Updated:** April 20, 2026
**Version:** 1.0
**Status:** Production Ready ✅
