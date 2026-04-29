import zipfile
import io
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.core.files.storage import default_storage
from django.urls import reverse
from django.db.models import Q
from functools import wraps
from .forms import ServiceRequestForm
from .models import User, Service, ServiceRequest, Page

def role_required(allowed_roles):
    """Decorator to restrict access based on user role."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Ensure user is authenticated
            if not request.user.is_authenticated:
                return redirect(reverse('login') + '?next=' + request.path)
            
            # Check if the user has the required role, or is staff/superuser for ADMIN paths
            is_permitted = request.user.role in allowed_roles
            if 'ADMIN' in allowed_roles and (request.user.is_staff or request.user.is_superuser):
                is_permitted = True

            if not is_permitted:
                messages.error(request, "You do not have the necessary permissions to access this page.")
                
                # Redirect users to their specific dashboard based on their role
                if request.user.role == 'ADMIN':
                    return redirect('admin_dashboard')
                elif request.user.role == 'AGENT1':
                    return redirect('agent1_dashboard')
                elif request.user.role == 'AGENT2':
                    return redirect('agent2_dashboard')
                else:
                    return redirect('user_dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def user_login(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'login')

        if action == 'register':
            # Handle registration
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            role = request.POST.get('role', 'USER')

            if username and password and email:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.first_name = first_name
                user.last_name = last_name
                user.role = role
                user.save()
                login(request, user)
                messages.success(request, f'Welcome aboard, {user.username}! Your account has been created.')
                return redirect('services')
            else:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'user-login.html', {'show_register': True})
        else:
            # Handle login
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                # Redirect admin users to Django admin
                if user.role == 'ADMIN':
                    return redirect('admin_dashboard')
                else:
                    return redirect('services')
            else:
                messages.error(request, 'Invalid credentials')

    # GET request or failed login
    return render(request, 'user-login.html')

def user_logout(request):
    logout(request)
    return redirect('/')

def register(request):
    # Redirect to combined login/register page
    return redirect('login')

# Admin Views
@login_required
@role_required(['ADMIN'])
def admin_dashboard(request):
    """
    View for the main Admin Dashboard.
    Fetches statistics and lists for services and requests.
    """
    services = Service.objects.all().order_by('-id')
    all_requests = ServiceRequest.objects.all().order_by('-created_at')
    pages = Page.objects.all()
    
    # Search functionality for services
    search_query = request.GET.get('search_services')
    if search_query:
        services = services.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    context = {
        'services': services,
        'requests': all_requests[:10],  # Show latest 10 requests
        'total_services': services.count(),
        'total_requests': all_requests.count(),
        'total_users': User.objects.count(),
        'pending_count': all_requests.filter(status='Pending').count(),
        'completed_count': all_requests.filter(status='Completed').count(),
        'search_query_services': search_query, # Pass back for input value
        'pages': pages,
    }
    return render(request, 'admin-site/admin-dashboard.html', context)


@login_required
@role_required(['ADMIN'])
def add_page(request):
    """View to create a new dynamic page."""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        if title and description:
            Page.objects.create(title=title, description=description)
            messages.success(request, f"Page '{title}' created successfully.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Both title and description are required.")
    
    pages = Page.objects.all()
    return render(request, 'admin-site/add_page.html', {'pages': pages})

@login_required
@role_required(['ADMIN', 'USER', 'AGENT1', 'AGENT2'])
def view_custom_page(request, page_id):
    """View to display a dynamically created page."""
    page = get_object_or_404(Page, id=page_id)
    pages = Page.objects.all()
    # Fetch services assigned to this specific page
    services = Service.objects.filter(page=page).order_by('-id')

    # Search functionality for services on this page
    search_query = request.GET.get('search_services')
    if search_query:
        services = services.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    # Determine template based on user role to extend correct base layout
    template_name = 'admin-site/dynamic_page.html'
    if request.user.role == 'AGENT1':
        template_name = 'agent1-site/dynamic_page.html'

    return render(request, template_name, {
        'page': page, 
        'pages': pages,
        'services': services,
        'search_query_services': search_query, # Pass back for input value
    })

@login_required
@role_required(['ADMIN', 'AGENT1'])
def apply_details(request):
    """
    Show requests based on role and filters:
    - For ADMIN: Show based on filter_type (all, pending, assigned, unassigned, completed)
    - For AGENT1: Show only unassigned requests (assigned_to = NULL)
    """
    pages = Page.objects.all()
    agents = User.objects.filter(role__in=['AGENT1', 'AGENT2'])

    filter_type = request.GET.get('filter_type', 'all')
    
    # Start with an optimized base queryset
    all_requests = ServiceRequest.objects.select_related('user', 'service', 'assigned_to').order_by('-created_at')

    # Apply filtering based on type
    if filter_type == 'completed':
        all_requests = all_requests.filter(status='Completed')
    elif filter_type == 'pending':
        all_requests = all_requests.filter(status='Pending')
    elif filter_type == 'assigned':
        all_requests = all_requests.filter(assigned_to__isnull=False)
    elif filter_type == 'unassigned':
        all_requests = all_requests.filter(assigned_to__isnull=True)
    elif request.user.role != 'ADMIN' and filter_type == 'all':
        # Default behavior for non-admins if no specific filter is selected
        all_requests = all_requests.filter(assigned_to__isnull=True)

    # Apply filters
    status_filter = request.GET.get('status')
    service_filter = request.GET.get('service')
    search_query = request.GET.get('search')
    agent_filter = request.GET.get('agent')  # For admin to filter by assigned agent

    if status_filter:
        all_requests = all_requests.filter(status=status_filter)
    if service_filter:
        all_requests = all_requests.filter(service_id=service_filter)
    if search_query:
        all_requests = all_requests.filter(
            Q(full_name__icontains=search_query) |
            Q(mobile__icontains=search_query) |
            Q(aadhaar_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    if agent_filter and request.user.role == 'ADMIN':
        all_requests = all_requests.filter(assigned_to_id=agent_filter)

    # Get all services for filter dropdown
    services = Service.objects.all()

    # Choose template based on user role to maintain UI consistency
    template_name = 'admin-site/apply_details.html'
    if request.user.role == 'AGENT1':
        template_name = 'agent1-site/apply_details.html'

    context = {
        'pages': pages,
        'requests': all_requests,
        'agents': agents,
        'services': services,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'search_query': search_query,
        'agent_filter': agent_filter,
        'filter_type': filter_type,
    }
    return render(request, template_name, context)


@login_required
@role_required(['ADMIN'])
def remove_assignment(request, request_id):
    """
    Remove assignment from request (set assigned_to = NULL, status = Pending).
    Only for ADMIN.
    """
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    if request.method == 'POST':
        service_request.assigned_to = None
        service_request.status = 'Pending'
        service_request.save()
        messages.success(request, f"Request #{request_id} has been unassigned and moved to Pending.")
        return redirect(request.META.get('HTTP_REFERER', 'apply_details'))
    
    return redirect(request.META.get('HTTP_REFERER', 'apply_details'))


@login_required
@role_required(['ADMIN'])
def reassign_request(request, request_id):
    """
    Reassign request to another Agent1.
    Only for ADMIN.
    """
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        message = request.POST.get('message', '')
        
        if agent_id:
            try:
                agent = User.objects.get(id=agent_id, role='AGENT1')
                service_request.assigned_to = agent
                service_request.status = 'Under Review'
                if message:
                    service_request.remarks = message
                service_request.save()
                messages.success(request, f"Request #{request_id} has been assigned to {agent.username}.")
            except User.DoesNotExist:
                messages.error(request, "Selected agent not found.")
        else:
            messages.error(request, "Please select an agent.")
        
        return redirect('apply_details')
    
    # GET request: Show assign form (shouldn't happen normally)
    return redirect('apply_details')


@login_required
@role_required(['ADMIN'])
def user_details(request):
    """View to manage users and handle manual user creation."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role', 'USER')

        if not (username and email and password and confirm_password):
            messages.error(request, 'Please fill all required fields.')
            return redirect('user_details')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('user_details')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('user_details')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email address already registered.')
            return redirect('user_details')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role
        # Ensure the 'mobile' field is defined in your User model in models.py
        if hasattr(user, 'mobile'):
            user.mobile = mobile
        user.save()

        messages.success(request, f'Account for {username} created successfully as {role}.')
        return redirect('user_details')

    role_filter = request.GET.get('role')
    if role_filter:
        users = User.objects.filter(role=role_filter).order_by('-id')
    else:
        users = User.objects.all().order_by('-id')

    return render(request, 'admin-site/user_handling.html', {'users': users})

@login_required
@role_required(['ADMIN'])
def edit_user(request, user_id):
    """View to edit an existing user's details."""
    user_to_edit = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user_to_edit.username = request.POST.get('username')
        user_to_edit.email = request.POST.get('email')
        user_to_edit.role = request.POST.get('role')
        user_to_edit.mobile = request.POST.get('mobile')
        
        # Optional password update
        password = request.POST.get('password')
        if password:
            user_to_edit.set_password(password)
            
        user_to_edit.save()
        messages.success(request, f'User {user_to_edit.username} updated successfully.')
        return redirect('user_details')
    
    pages = Page.objects.all()
    return render(request, 'admin-site/edit_user.html', {
        'user_to_edit': user_to_edit,
        'pages': pages
    })

@login_required
@role_required(['ADMIN'])
def delete_user(request, user_id):
    """View to delete a user account."""
    user_to_delete = get_object_or_404(User, id=user_id)
    username = user_to_delete.username
    user_to_delete.delete()
    messages.success(request, f'User {username} has been removed.')
    return redirect('user_details')

@login_required
@role_required(['ADMIN'])
def add_service(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        charges = request.POST.get('charges') or 0.00
        documents = request.POST.get('documents_required')
        tutorial = request.POST.get('tutorial_link')
        apply_link = request.POST.get('apply_link')
        page_id = request.POST.get('page')

        if name and description:
            page = Page.objects.filter(id=page_id).first() if page_id else None
            Service.objects.create(
                name=name, description=description, charges=charges,
                documents_required=documents, tutorial_link=tutorial,
                apply_link=apply_link, page=page
            )
            messages.success(request, 'New service added successfully.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Both name and description are required.')
    
    pages = Page.objects.all()
    
    # Get page_id from GET parameters for pre-selection
    preselect_page_id = request.GET.get('page_id') 
    
    return render(request, 'admin-site/add_service.html', {
        'pages': pages, 
        'title': 'Add Service',
        'preselect_page_id': preselect_page_id # Pass to template
    })

@login_required
@role_required(['ADMIN'])
def edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    
    preselect_page_id = request.GET.get('page_id') # For consistency, though less common for edit

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        charges = request.POST.get('charges') or 0.00
        documents = request.POST.get('documents_required')
        tutorial = request.POST.get('tutorial_link')
        apply_link = request.POST.get('apply_link')
        page_id = request.POST.get('page')

        if name and description:
            service.name = name
            service.description = description
            service.charges = charges
            service.documents_required = documents
            service.tutorial_link = tutorial
            service.apply_link = apply_link
            service.page = Page.objects.filter(id=page_id).first() if page_id else None
            service.save()
            messages.success(request, 'Service details updated successfully.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Both name and description are required.')
            
    pages = Page.objects.all() # Fetch all pages for the dropdown
    return render(request, 'admin-site/add_service.html', {
        'service': service, 
        'pages': pages, 
        'title': 'Edit Service',
        'preselect_page_id': preselect_page_id,
    })

@login_required
@role_required(['ADMIN'])
def delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    service.delete()
    messages.success(request, 'Service has been removed.')
    return redirect('admin_dashboard')

@login_required
@role_required(['ADMIN'])
def assign_request(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        if agent_id:
            agent = get_object_or_404(User, id=agent_id, role__in=['AGENT1', 'AGENT2'])
            service_request.assigned_to = agent
            service_request.status = 'Under Review'
            service_request.save()
            messages.success(request, f'Application successfully assigned to Agent: {agent.username}.')
        else:
            messages.error(request, 'Please select an agent.')
    return redirect('apply_details')

# User Views
@login_required
@role_required(['USER'])
def user_dashboard(request):
    # Fetch all services for the "Available Services" section
    all_services = Service.objects.all().order_by('-id')
    # Fetch all requests submitted by the current user
    my_requests = ServiceRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user-site/dashboard.html', {'services': all_services, 'my_requests': my_requests})

@login_required
@role_required(['USER'])
def user_request_detail(request, request_id):
    """Display user's service request details with download option for completed file"""
    service_request = get_object_or_404(ServiceRequest, id=request_id, user=request.user)
    return render(request, 'details.html', {'request': service_request})

@login_required
@role_required(['USER'])
def apply_service(request, service_id):
    """User apply for a service with dynamic document uploads."""
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        # ========== DEBUG ==========
        print("=" * 50)
        print("DEBUG: === USER APPLY SERVICE SUBMISSION ===")
        print(f"DEBUG: All POST keys: {list(request.POST.keys())}")
        print(f"DEBUG: All FILES keys: {list(request.FILES.keys())}")
        print("=" * 50)
        
        errors = []
        
        # Validate required text fields
        full_name = request.POST.get('full_name', '').strip()
        dob = request.POST.get('dob', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        aadhaar_number = request.POST.get('aadhaar_number', '').strip()
        address = request.POST.get('address', '').strip()
        
        if not full_name:
            errors.append('Full Name is required')
        if not dob:
            errors.append('Date of Birth is required')
        if not email:
            errors.append('Email is required')
        if not mobile or len(mobile) != 10 or not mobile.isdigit():
            errors.append('Mobile must be 10 digits')
        if not aadhaar_number or len(aadhaar_number.replace(' ', '')) != 12:
            errors.append('Aadhaar number must be 12 digits')
        if not address:
            errors.append('Address is required')
        
        # ========== KEY STEP: Get selected documents from checkbox ==========
        doc_selected = request.POST.getlist('doc_selected')
        print(f"DEBUG: Selected documents (from checkbox): {doc_selected}")
        
        if not doc_selected:
            errors.append('Please select at least one document')
        
        # Verify each selected document has an uploaded file
        uploaded_files = []
        for doc_id in doc_selected:
            file_obj = request.FILES.get(doc_id)
            if file_obj:
                uploaded_files.append((doc_id, file_obj))
                print(f"DEBUG: File found for '{doc_id}': {file_obj.name}")
            else:
                errors.append(f'Please upload file for: {doc_id}')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'user-site/apply.html', {'service': service})
        
        # ========== Save ServiceRequest ==========
        try:
            service_request = ServiceRequest()
            service_request.user = request.user
            service_request.service = service
            service_request.full_name = full_name
            service_request.dob = dob
            service_request.email = email
            service_request.mobile = mobile
            service_request.aadhaar_number = aadhaar_number.replace(' ', '')
            service_request.address = address
            service_request.description = request.POST.get('description', '')
            service_request.status = 'Pending'
            
            service_request.save()
            print(f"DEBUG: Request saved with ID: {service_request.id}")
            
            # ========== Save STANDARD document fields ==========
            # Map all possible slugified document names to model fields
            standard_fields_map = {
                'photo': 'photo',
                'photograph': 'photo',
                'aadhaar': 'aadhaar_card',
                'aadhaar_card': 'aadhaar_card',
                'aadhaar_number': 'aadhaar_card',
                'pan': 'pan_card',
                'pan_card': 'pan_card',
                'pan_number': 'pan_card',
                'signature': 'signature',
                'address': 'address_proof',
                'address_proof': 'address_proof',
                'residence_proof': 'address_proof',
            }
            
            # Save standard fields based on what's in request.FILES
            for form_name, model_field in standard_fields_map.items():
                file_obj = request.FILES.get(form_name)
                if file_obj:
                    setattr(service_request, model_field, file_obj)
                    print(f"DEBUG: Saved standard field {model_field}: {file_obj.name}")
            
            service_request.save()
            
            # ========== Save DYNAMIC documents to JSONField ==========
            dynamic_docs = {}
            
            for doc_id, file_obj in uploaded_files:
                # Create unique filename to avoid conflicts
                import os
                from django.utils import timezone
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                original_name = file_obj.name
                ext = os.path.splitext(original_name)[1]
                new_filename = f"{doc_id}_{timestamp}{ext}"
                
                # Save to media directory
                doc_folder = f'requests/dynamic/{service_request.id}/'
                file_path = f'{doc_folder}{new_filename}'
                saved_path = default_storage.save(file_path, file_obj)
                
                # Store in dynamic_documents JSON
                dynamic_docs[doc_id] = saved_path
                print(f"DEBUG: Saved dynamic doc '{doc_id}' -> {saved_path}")
            
            # Update with dynamic documents
            service_request.dynamic_documents = dynamic_docs
            service_request.save()
            
            print(f"DEBUG: ✅ Success! Request #{service_request.id}")
            print(f"DEBUG: Dynamic documents saved: {dynamic_docs}")
            print("=" * 50)
            
            messages.success(request, f'Application for {service.name} submitted successfully!')
            return redirect('user_dashboard')
            
        except Exception as e:
            print(f"ERROR: Exception during save: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'user-site/apply.html', {'service': service})

# Agent2 Views

# Public services view
def services(request):
    all_services = Service.objects.all().order_by('-id')
    pages = Page.objects.all() # For potential page filter or just context

    # Search functionality for public services
    search_query = request.GET.get('search_services')
    if search_query:
        all_services = all_services.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    # Filter by page
    page_filter_id = request.GET.get('page_filter')
    if page_filter_id:
        all_services = all_services.filter(page_id=page_filter_id)

    return render(request, 'service.html', {'services': all_services, 'pages': pages, 'search_query_services': search_query, 'page_filter_id': page_filter_id})

def get_agent2_sidebar_counts(user):
    """Helper to get task counts for the Agent2 sidebar."""
    agent_base = ServiceRequest.objects.filter(user=user)
    return {
        'all': agent_base.count(),
        'pending': agent_base.filter(status='Pending').count(),
        'in_progress': agent_base.filter(status='In Progress').count(),
        'completed': agent_base.filter(status='Completed').count(),
    }

@login_required
@role_required(['AGENT2'])
def agent2_dashboard(request):
    """
    Agent2 main dashboard with status, service, and search filtering.
    """
    agent_base = ServiceRequest.objects.filter(user=request.user)
    all_assigned = agent_base.order_by('-created_at')

    # Filters
    status_filter = request.GET.get('status')
    service_filter = request.GET.get('service')
    search_query = request.GET.get('search')
    category_filter = request.GET.get('category')

    if search_query:
        all_assigned = all_assigned.filter(
            Q(full_name__icontains=search_query) | 
            Q(aadhaar_number__icontains=search_query) |
            Q(mobile__icontains=search_query)
        )

    if status_filter:
        all_assigned = all_assigned.filter(status=status_filter)
    if service_filter:
        all_assigned = all_assigned.filter(service_id=service_filter)
    if category_filter:
        all_assigned = all_assigned.filter(service__page_id=category_filter)

    pages = Page.objects.all()
    available_services = Service.objects.all()
    
    context = {
        'requests': all_assigned,
        'pages': pages,
        'services': available_services,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'sidebar_counts': get_agent2_sidebar_counts(request.user),
    }
    return render(request, 'agent2-site/base-agent2.html', context)

@login_required
@role_required(['AGENT2'])
def agent2_new_requests(request):
    """Redirect to dashboard filtered for Pending requests."""
    return redirect(reverse('agent2_dashboard') + '?status=Pending')

@login_required
@role_required(['AGENT2'])
def agent2_in_progress(request):
    """Redirect to dashboard filtered for In Progress requests."""
    return redirect(reverse('agent2_dashboard') + '?status=In+Progress')

@login_required
@role_required(['AGENT2'])
def agent2_completed(request):
    """Redirect to dashboard filtered for Completed requests."""
    return redirect(reverse('agent2_dashboard') + '?status=Completed')

@login_required
@role_required(['AGENT2'])
def agent2_request_detail(request, request_id):
    """Agent2 detail view. Uses 'req' to avoid shadowing the request object."""
    # Only allow access to the current user's own submitted requests
    service_request = get_object_or_404(ServiceRequest, id=request_id, user=request.user)
    
    if request.method == 'POST' and 'edit_details' in request.POST:
        # Handle inline edit from Agent 2
        service_request.full_name = request.POST.get('full_name', service_request.full_name)
        service_request.dob = request.POST.get('dob', service_request.dob)
        service_request.mobile = request.POST.get('mobile', service_request.mobile)
        service_request.email = request.POST.get('email', service_request.email)
        service_request.aadhaar_number = request.POST.get('aadhaar_number', service_request.aadhaar_number)
        service_request.address = request.POST.get('address', service_request.address)
        service_request.save()
        messages.success(request, "Application details updated successfully.")
        return redirect('agent2_request_detail', request_id=request_id)

    pages = Page.objects.all()
    
    context = {
        'req': service_request,
        'pages': pages,
        'edit_mode': request.GET.get('edit') == '1',
        'sidebar_counts': get_agent2_sidebar_counts(request.user),
    }
    return render(request, 'agent2-site/agent2_tasks.html', context)

@login_required
@role_required(['AGENT2'])
def agent2_service(request):
    """Agent2 view for services list, mirroring the user service page."""
    all_services = Service.objects.all().order_by('-id')
    pages = Page.objects.all()

    # Search functionality
    search_query = request.GET.get('search_services')
    if search_query:
        all_services = all_services.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    # Filter by page
    page_filter_id = request.GET.get('page_filter')
    if page_filter_id:
        all_services = all_services.filter(page_id=page_filter_id)

    context = {
        'services': all_services,
        'pages': pages,
        'search_query_services': search_query,
        'page_filter_id': page_filter_id,
        'sidebar_counts': get_agent2_sidebar_counts(request.user),
    }
    return render(request, 'agent2-site/service.html', context)

@login_required
@role_required(['AGENT2'])
def agent2_apply(request, service_id):
    """Agent2 view to apply for a service with dynamic document uploads."""
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        # ========== DEBUG ==========
        print("=" * 50)
        print("DEBUG: === AGENT2 APPLY SUBMISSION ===")
        print(f"DEBUG: All POST keys: {list(request.POST.keys())}")
        print(f"DEBUG: All FILES keys: {list(request.FILES.keys())}")
        print("=" * 50)
        
        errors = []
        
        # Validate required text fields
        full_name = request.POST.get('full_name', '').strip()
        dob = request.POST.get('dob', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        aadhaar_number = request.POST.get('aadhaar_number', '').strip()
        address = request.POST.get('address', '').strip()
        
        if not full_name:
            errors.append('Full Name is required')
        if not dob:
            errors.append('Date of Birth is required')
        if not email:
            errors.append('Email is required')
        if not mobile or len(mobile) != 10 or not mobile.isdigit():
            errors.append('Mobile must be 10 digits')
        if not aadhaar_number or len(aadhaar_number.replace(' ', '')) != 12:
            errors.append('Aadhaar number must be 12 digits')
        if not address:
            errors.append('Address is required')
        
        # ========== KEY STEP: Get selected documents from checkbox ==========
        doc_selected = request.POST.getlist('doc_selected')
        print(f"DEBUG: Selected documents (from checkbox): {doc_selected}")
        
        if not doc_selected:
            errors.append('Please select at least one document')
        
        # Verify each selected document has an uploaded file
        uploaded_files = []
        for doc_id in doc_selected:
            file_obj = request.FILES.get(doc_id)
            if file_obj:
                uploaded_files.append((doc_id, file_obj))
                print(f"DEBUG: File found for '{doc_id}': {file_obj.name}")
            else:
                errors.append(f'Please upload file for: {doc_id}')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'agent2-site/apply.html', {'service': service})
        
        # ========== Save ServiceRequest ==========
        try:
            service_request = ServiceRequest()
            service_request.user = request.user
            service_request.service = service
            service_request.full_name = full_name
            service_request.dob = dob
            service_request.email = email
            service_request.mobile = mobile
            service_request.aadhaar_number = aadhaar_number.replace(' ', '')
            service_request.address = address
            service_request.description = request.POST.get('description', '')
            service_request.status = 'Pending'
            
            service_request.save()
            print(f"DEBUG: Request saved with ID: {service_request.id}")
            
            # ========== Save STANDARD document fields ==========
            # Map all possible slugified document names to model fields
            standard_fields_map = {
                'photo': 'photo',
                'photograph': 'photo',
                'aadhaar': 'aadhaar_card',
                'aadhaar_card': 'aadhaar_card',
                'aadhaar_number': 'aadhaar_card',
                'pan': 'pan_card',
                'pan_card': 'pan_card',
                'pan_number': 'pan_card',
                'signature': 'signature',
                'address': 'address_proof',
                'address_proof': 'address_proof',
                'residence_proof': 'address_proof',
            }
            
            # Save standard fields based on what's in request.FILES
            for form_name, model_field in standard_fields_map.items():
                file_obj = request.FILES.get(form_name)
                if file_obj:
                    setattr(service_request, model_field, file_obj)
                    print(f"DEBUG: Saved standard field {model_field}: {file_obj.name}")
            
            service_request.save()
            
            # ========== Save DYNAMIC documents to JSONField ==========
            dynamic_docs = {}
            
            for doc_id, file_obj in uploaded_files:
                # Create unique filename to avoid conflicts
                import os
                from django.utils import timezone
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                original_name = file_obj.name
                ext = os.path.splitext(original_name)[1]
                new_filename = f"{doc_id}_{timestamp}{ext}"
                
                # Save to media directory
                doc_folder = f'requests/dynamic/{service_request.id}/'
                file_path = f'{doc_folder}{new_filename}'
                saved_path = default_storage.save(file_path, file_obj)
                
                # Store in dynamic_documents JSON
                dynamic_docs[doc_id] = saved_path
                print(f"DEBUG: Saved dynamic doc '{doc_id}' -> {saved_path}")
            
            # Update with dynamic documents
            service_request.dynamic_documents = dynamic_docs
            service_request.save()
            
            print(f"DEBUG: ✅ Success! Request #{service_request.id}")
            print(f"DEBUG: Dynamic documents saved: {dynamic_docs}")
            print("=" * 50)
            
            messages.success(request, f'Application for {service.name} submitted successfully!')
            return redirect('agent2_dashboard')
            
        except Exception as e:
            print(f"ERROR: Exception during save: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'agent2-site/apply.html', {'service': service})

@login_required
@role_required(['AGENT2'])
def agent2_forward(request, request_id):
    """Agent2 forwards request to Agent1"""
    # Ensure they can only forward their own request
    service_request = get_object_or_404(ServiceRequest, id=request_id, user=request.user)

    agent1 = User.objects.filter(role='AGENT1').first()
    
    if agent1:
        service_request.assigned_to = agent1
        service_request.status = 'Under Review'
        service_request.save()
        messages.success(request, f'Request forwarded to Agent1 successfully.')
    else:
        messages.error(request, 'No Agent1 available to forward this request.')
    
    return redirect('agent2_dashboard')

@login_required
@role_required(['AGENT2'])
def agent2_upload(request):
    """Agent2 upload documents/files view"""
    pages = Page.objects.all()
    
    context = {
        'pages': pages,
        'sidebar_counts': get_agent2_sidebar_counts(request.user),
    }
    return render(request, 'agent2-site/agent2_upload.html', context)

@login_required
@role_required(['AGENT2'])
def agent2_apply_details(request):
    """
    Agent2 Apply Details - Shows ONLY the logged-in user's applications.
    
    CRITICAL: Only display requests where user = request.user
    """
    
    # ===== HANDLE POST (SAVE EDIT) =====
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        # SECURITY: Double-check user=request.user to prevent editing other users' data
        service_request = get_object_or_404(
            ServiceRequest, 
            id=req_id, 
            user=request.user  # ✅ Only allow editing own requests
        )

        service_request.full_name = request.POST.get('full_name')
        service_request.mobile = request.POST.get('mobile')
        service_request.aadhaar_number = request.POST.get('aadhaar_number')
        service_request.email = request.POST.get('email')
        service_request.status = request.POST.get('status')
        service_request.remarks = request.POST.get('remarks')

        service_request.save()

        messages.success(request, "✅ Details updated successfully!")
        return redirect('agent2_apply_details')


    # ===== GET REQUEST - FETCH AND FILTER DATA =====
    # 🔥 START WITH ONLY THE LOGGED-IN USER'S REQUESTS
    user_requests = ServiceRequest.objects.filter(user=request.user).order_by('-created_at')
    
    pages = Page.objects.all()
    available_services = Service.objects.all()

    # Get filter parameters from GET request
    status_filter = request.GET.get('status')
    service_filter = request.GET.get('service')
    search_query = request.GET.get('search')
    category_filter = request.GET.get('category')

    # ===== APPLY FILTERS (Always starting from user-filtered queryset) =====
    filtered_requests = user_requests  # Start with user-filtered base
    
    # Search filter
    if search_query:
        filtered_requests = filtered_requests.filter(
            Q(full_name__icontains=search_query) | 
            Q(aadhaar_number__icontains=search_query) |
            Q(mobile__icontains=search_query)
        )

    # Status filter - default to pending/in-progress/under-review if not specified
    if status_filter:
        filtered_requests = filtered_requests.filter(status=status_filter)
    else:
        filtered_requests = filtered_requests.filter(
            status__in=['Pending', 'In Progress', 'Under Review']
        )

    # Service filter
    if service_filter:
        filtered_requests = filtered_requests.filter(service_id=service_filter)
    
    # Category/Page filter
    if category_filter:
        filtered_requests = filtered_requests.filter(service__page_id=category_filter)

    context = {
        'requests': filtered_requests,  # ✅ Only logged-in user's filtered requests
        'pages': pages,
        'services': available_services,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'sidebar_counts': get_agent2_sidebar_counts(request.user),
    }

    return render(request, 'agent2-site/agent2_apply_details.html', context)

@login_required
@role_required(['AGENT2'])
def agent2_complete_details(request):
    """
    Agent2 Complete Details - Shows all completed applications.
    """
    all_requests = ServiceRequest.objects.filter(
        user=request.user, 
        status='Completed'
    ).order_by('-created_at')
    pages = Page.objects.all()
    available_services = Service.objects.all()
    
    # Filters
    service_filter = request.GET.get('service')
    search_query = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if search_query:
        all_requests = all_requests.filter(
            Q(full_name__icontains=search_query) | 
            Q(aadhaar_number__icontains=search_query) |
            Q(mobile__icontains=search_query)
        )

    if service_filter:
        all_requests = all_requests.filter(service_id=service_filter)
    
    if date_from:
        all_requests = all_requests.filter(created_at__date__gte=date_from)
    if date_to:
        all_requests = all_requests.filter(created_at__date__lte=date_to)

    context = {
        'requests': all_requests,
        'pages': pages,
        'services': available_services,
        'service_filter': service_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'sidebar_counts': get_agent2_sidebar_counts(request.user),
    }
    return render(request, 'agent2-site/agent2_complete_details.html', context)

def agent2_login(request):
    """Agent2 login page"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'role') and request.user.role == 'AGENT2':
            return redirect('agent2_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if hasattr(user, 'role') and user.role == 'AGENT2':
                login(request, user)
                messages.success(request, f'Agent 2 Portal Accessed. Welcome, {user.username}.')
                
                # Handle redirection
                next_url = request.POST.get('next') or request.GET.get('next') or 'agent2_dashboard'
                return redirect(next_url)
            else:
                messages.error(request, 'Access Denied: This portal is for Agent2 only.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'agent2-site/agent2-login.html')


# Agent1 Views
@login_required
@role_required(['AGENT1'])
def agent1_dashboard(request):
    """Agent1 main dashboard with status and service filtering."""
    # Base queryset for the assigned agent
    all_assigned = ServiceRequest.objects.filter(assigned_to=request.user).order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status')
    service_filter = request.GET.get('service')

    if status_filter:
        all_assigned = all_assigned.filter(status=status_filter)
    if service_filter:
        all_assigned = all_assigned.filter(service_id=service_filter)

    pages = Page.objects.all()
    available_services = Service.objects.all()
    
    context = {
        'requests': all_assigned,
        'pages': pages,
        'services': available_services,
        'status_filter': status_filter,
        'service_filter': service_filter,
    }
    return render(request, 'agent1-site/base-agent1.html', context)

@login_required
@role_required(['AGENT1'])
def agent1_new_requests(request):
    """Agent1 view for new requests"""
    requests = ServiceRequest.objects.filter(
        assigned_to=request.user, 
        status='Under Review'
    ).order_by('-created_at')
    pages = Page.objects.all()
    
    context = {
        'requests': requests,
        'pages': pages,
    }
    return render(request, 'agent1-site/new_requests.html', context)

@login_required
@role_required(['AGENT1'])
def agent1_assigned_requests(request):
    """Agent1 view for all assigned requests"""
    requests = ServiceRequest.objects.filter(
        assigned_to=request.user
    ).order_by('-created_at')
    pages = Page.objects.all()
    
    context = {
        'requests': requests,
        'pages': pages,
    }
    return render(request, 'agent1-site/assigned_requests.html', context)

@login_required
@role_required(['AGENT1'])
def agent1_in_progress(request):
    """Agent1 view for in-progress requests"""
    requests = ServiceRequest.objects.filter(
        assigned_to=request.user,
        status='In Progress'
    ).order_by('-created_at')
    pages = Page.objects.all()
    
    context = {
        'requests': requests,
        'pages': pages,
    }
    return render(request, 'agent1-site/in_progress.html', context)

@login_required
@role_required(['AGENT1'])
def agent1_completed(request):
    """Agent1 view for completed requests"""
    requests = ServiceRequest.objects.filter(
        assigned_to=request.user,
        status='Completed'
    ).order_by('-created_at')
    pages = Page.objects.all()
    
    context = {
        'requests': requests,
        'pages': pages,
    }
    return render(request, 'agent1-site/completed.html', context)

@login_required
@role_required(['AGENT1'])
def agent1_request_detail(request, request_id):
    """Agent1 view for specific request details. Allows status change, remarks, and document upload."""
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to=request.user)
    
    if request.method == 'POST':
        # Handle status change
        new_status = request.POST.get('status')
        if new_status and new_status in dict(ServiceRequest.STATUS_CHOICES):
            service_request.status = new_status
        
        # Handle remarks
        remarks = request.POST.get('remarks', '')
        if remarks:
            service_request.remarks = remarks
        
        # Handle completed file upload
        completed_file = request.FILES.get('completed_file')
        if completed_file:
            service_request.completed_file = completed_file
        
        service_request.save()
        messages.success(request, f"Request #{request_id} updated successfully.")
        return redirect('agent1_request_detail', request_id=request_id)
    else:
        # GET request: Transition status when Agent 1 begins processing (first view)
        if service_request.status == 'Under Review':
            service_request.status = 'In Progress'
            service_request.save()
            messages.info(request, f"Application #{request_id} has been moved to 'In Progress'.")

    pages = Page.objects.all()
    status_choices = ServiceRequest.STATUS_CHOICES
    
    context = {
        'request': service_request,
        'pages': pages,
        'status_choices': status_choices,
    }
    return render(request, 'agent1-site/user_details.html', context)

@login_required
@role_required(['AGENT1'])
def agent1_download_report(request, request_id):
    """Generates a text report containing all applicant details for download."""
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to=request.user)
    
    report_data = [
        f"REPORT FOR REQUEST #{service_request.id}",
        f"Service: {service_request.service.name}",
        f"Current Status: {service_request.status}",
        f"Applicant: {service_request.full_name}",
        f"Aadhaar: {service_request.aadhaar_number}",
        f"Mobile: {service_request.mobile}",
        f"Email: {service_request.email}",
        f"Address: {service_request.address}",
        f"Created At: {service_request.created_at}",
        f"Description: {service_request.description}",
        f"Remarks: {service_request.remarks or 'N/A'}"
    ]
    
    response = HttpResponse("\n".join(report_data), content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="Request_Report_{service_request.id}.txt"'
    return response

@login_required
@role_required(['AGENT1'])
def agent1_complete(request, request_id):
    """Agent1 marks a request as complete"""
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to=request.user)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        completed_file = request.FILES.get('completed_file')
        service_request.status = 'Completed'
        service_request.remarks = remarks
        if completed_file:
            service_request.completed_file = completed_file
        service_request.save()
        messages.success(request, 'Request marked as completed.')
        return redirect('agent1_dashboard')
    
    return render(request, 'agent1-site/user_details.html', {'request': service_request})

@login_required
@role_required(['AGENT1'])
def take_request(request, request_id):
    """
    Agent1 takes (claims) an unassigned request.
    Sets assigned_to = logged-in agent and status = 'Under Review'
    """
    if request.method == 'POST':
        service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to__isnull=True)
        
        # Get description from form (optional)
        description = request.POST.get('description', '')
        
        # Assign to current agent
        service_request.assigned_to = request.user
        service_request.status = 'Under Review'
        if description:
            service_request.remarks = description
        service_request.save()
        
        messages.success(request, f'Request #{request_id} has been assigned to you. Status: Under Review')
        return redirect('apply_details')
    
    return redirect('apply_details')

@login_required
@role_required(['ADMIN', 'AGENT1'])
def update_request_status(request, request_id):
    """Allows Admin or assigned Agent to update status and upload final file."""
    service_request = get_object_or_404(ServiceRequest, id=request_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        remarks = request.POST.get('remarks')
        completed_file = request.FILES.get('completed_file')
        
        if status:
            service_request.status = status
            
        if remarks is not None:
            service_request.remarks = remarks
            
        if completed_file:
            service_request.completed_file = completed_file
            
        service_request.save()
        messages.success(request, f"Request #{request_id} updated successfully.")
        
        return redirect(request.META.get('HTTP_REFERER', 'apply_details'))

    pages = Page.objects.all()
    return render(request, 'admin-site/update_request.html', {
        'req': service_request,
        'pages': pages
    })


# admin site login complate enter login admin dash bord
def admin_login(request):
    # Redirect if already logged in as admin
    if request.user.is_authenticated:
        if request.user.is_staff or (hasattr(request.user, 'role') and request.user.role == 'ADMIN'):
            return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Checking for Admin Role or Staff Status
            is_admin = user.is_staff or (hasattr(user, 'role') and user.role == 'ADMIN')
            
            if is_admin:
                login(request, user)
                messages.success(request, f'Access Granted. Welcome, {user.username}.')
                
                # Check for 'next' parameter in POST or GET to redirect back to intended page
                next_url = request.POST.get('next') or request.GET.get('next') or 'admin_dashboard'
                return redirect(next_url)
            else:
                messages.error(request, 'Access Denied: This portal is for Administrators only.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'admin-site/adminsite-login.html')

def agent1_login(request):
    """Agent1 login page"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'role') and request.user.role == 'AGENT1':
            return redirect('agent1_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if hasattr(user, 'role') and user.role == 'AGENT1':
                login(request, user)
                messages.success(request, f'Agent 1 Authentication Successful. Welcome, {user.username}.')
                
                next_url = request.POST.get('next') or request.GET.get('next') or 'agent1_dashboard'
                return redirect(next_url)
            else:
                messages.error(request, 'Access Denied: This portal is for Agent 1 only.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'agent1-site/agent1-login.html')

@login_required
@role_required(['ADMIN', 'AGENT1', 'AGENT2'])
def download_all_docs(request, req_id):
    """Packages all uploaded documents for a request into a ZIP file."""
    req = get_object_or_404(ServiceRequest, id=req_id)
    
    # Create an in-memory ZIP file
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        # 1. Add Fixed Model Fields (Standard Documents)
        fields = [req.photo, req.aadhaar_card, req.pan_card, req.signature, req.address_proof]
        
        for field in fields:
            if field: # Checks if a file is actually assigned
                try:
                    if os.path.exists(field.path):
                        zip_file.write(field.path, arcname=os.path.basename(field.path))
                except (ValueError, FileNotFoundError):
                    continue

        # 2. Add Dynamic Documents from JSON field
        if req.dynamic_documents:
            for doc_name, doc_path in req.dynamic_documents.items():
                full_path = os.path.join(settings.MEDIA_ROOT, doc_path)
                if os.path.exists(full_path):
                    # Maintain extension but use doc_name for clarity inside the ZIP
                    ext = os.path.splitext(doc_path)[1]
                    zip_file.write(full_path, arcname=f"{doc_name}{ext}")

    # Prepare the response
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    safe_name = req.full_name.replace(' ', '_') if req.full_name else 'Applicant'
    zip_name = f"Documents_{safe_name}_{req.id}.zip"
    response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
    return response


# ===== AGENT1 APPLY DETAILS WITH FILTERING =====
@login_required
@role_required(['AGENT1'])
def agent1_apply_details(request):
    """
    Agent1 Apply Details page with filtering options:
    - All: Show all requests (pending + completed)
    - Completed: Show only completed requests
    - Pending: Show only pending requests
    - Assigned: Show only requests assigned to this Agent1
    - History: Show completed requests assigned to this Agent1
    """
    pages = Page.objects.all()
    available_services = Service.objects.all()
    all_agents = User.objects.filter(role='AGENT1').exclude(id=request.user.id)
    
    # Get filter type from URL
    filter_type = request.GET.get('filter_type', 'all')
    
    # Base query building based on filter_type
    if filter_type == 'completed':
        # Show only completed requests
        requests_list = ServiceRequest.objects.filter(status='Completed').order_by('-created_at')
    elif filter_type == 'pending':
        # Show only pending requests
        requests_list = ServiceRequest.objects.filter(status='Pending').order_by('-created_at')
    elif filter_type == 'unassigned':
        # Show only unassigned requests
        requests_list = ServiceRequest.objects.filter(assigned_to__isnull=True).order_by('-created_at')
    elif filter_type == 'assigned':
        # Show only requests assigned to this Agent1
        requests_list = ServiceRequest.objects.filter(assigned_to=request.user).order_by('-created_at')
    elif filter_type == 'history':
        # Show completed requests that were assigned to this Agent1
        requests_list = ServiceRequest.objects.filter(
            assigned_to=request.user, 
            status='Completed'
        ).order_by('-created_at')
    else:  # 'all'
        # Show all requests
        requests_list = ServiceRequest.objects.all().order_by('-created_at')
    
    # Apply additional filters
    status_filter = request.GET.get('status')
    service_filter = request.GET.get('service')
    search_query = request.GET.get('search')
    
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    if service_filter:
        requests_list = requests_list.filter(service_id=service_filter)
    if search_query:
        requests_list = requests_list.filter(
            Q(full_name__icontains=search_query) |
            Q(mobile__icontains=search_query) |
            Q(aadhaar_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    context = {
        'pages': pages,
        'requests': requests_list,
        'agents': all_agents,
        'services': available_services,
        'filter_type': filter_type,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'search_query': search_query,
    }
    return render(request, 'agent1-site/apply_details.html', context)


@login_required
@role_required(['AGENT1'])
def agent1_remove_assignment(request, request_id):
    """
    Agent1 removes a request from their assignment.
    - Sets assigned_to = NULL
    - Sets status = 'Pending'
    - Request goes back to general queue
    """
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to=request.user)
    
    if request.method == 'POST':
        service_request.assigned_to = None
        service_request.status = 'Pending'
        service_request.save()
        messages.success(request, f"Request #{request_id} has been removed from your queue and moved to Pending.")
        return redirect('agent1_apply_details', filter_type='assigned')
    
    return redirect('agent1_apply_details', filter_type='assigned')


@login_required
@role_required(['AGENT1'])
def agent1_assign_request(request, request_id):
    """
    Agent1 reassigns a request to another Agent1.
    - Shows modal form with Agent1 dropdown
    - Sets assigned_to = selected agent
    - Adds message to remarks
    - Status = 'Under Review'
    """
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to=request.user)
    
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        message = request.POST.get('message', '')
        
        if agent_id:
            try:
                # Verify the selected agent is AGENT1 and not the current user
                target_agent = User.objects.get(id=agent_id, role='AGENT1')
                if target_agent.id == request.user.id:
                    messages.error(request, "Cannot assign to yourself.")
                    return redirect('agent1_apply_details', filter_type='assigned')
                
                # Reassign the request
                service_request.assigned_to = target_agent
                service_request.status = 'Under Review'
                
                # Save message in remarks (append to existing remarks)
                if message:
                    if service_request.remarks:
                        service_request.remarks += f"\n--- Transferred by {request.user.username} ---\n{message}"
                    else:
                        service_request.remarks = f"--- Transferred by {request.user.username} ---\n{message}"
                
                service_request.save()
                messages.success(request, f"Request #{request_id} has been assigned to {target_agent.username}.")
                return redirect('agent1_apply_details', filter_type='assigned')
                
            except User.DoesNotExist:
                messages.error(request, "Selected agent not found.")
                return redirect('agent1_apply_details', filter_type='assigned')
        else:
            messages.error(request, "Please select an agent.")
            return redirect('agent1_apply_details', filter_type='assigned')
    
    # GET request - redirect (shouldn't happen normally as form is in template)
    return redirect('agent1_apply_details', filter_type='assigned')


# ===== ADMIN-SPECIFIC FUNCTIONS =====
@login_required
@role_required(['ADMIN'])
def admin_assign_request(request, request_id):
    """
    Admin assigns a request to any Agent1/Agent2.
    POST: assign request
    """
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        message = request.POST.get('message', '')
        
        if agent_id:
            try:
                target_agent = User.objects.get(id=agent_id, role__in=['AGENT1', 'AGENT2'])
                
                # Save previous assignment info if exists
                prev_agent = service_request.assigned_to
                service_request.assigned_to = target_agent
                service_request.status = 'Under Review'
                
                # Save message in remarks (append with transfer info)
                if message:
                    transfer_info = f"\n--- Assigned by Admin ({request.user.username}) ---\n{message}"
                    if prev_agent:
                        transfer_info = f"\n--- Reassigned by Admin from {prev_agent.username} ---\n{message}"
                    
                    if service_request.remarks:
                        service_request.remarks += transfer_info
                    else:
                        service_request.remarks = transfer_info
                
                service_request.save()
                messages.success(request, f"Request #{request_id} assigned to {target_agent.username} ({target_agent.role}).")
                return redirect(request.META.get('HTTP_REFERER', 'apply_details'))
                
            except User.DoesNotExist:
                messages.error(request, "Selected agent not found.")
        else:
            messages.error(request, "Please select an agent.")
    
    return redirect(request.META.get('HTTP_REFERER', 'apply_details'))


@login_required
@role_required(['ADMIN'])
def admin_agent_workload(request):
    """
    Admin dashboard showing agent workload and performance.
    - Total requests per agent
    - Assigned vs Completed
    - Status breakdown
    - Agent activity overview
    """
    pages = Page.objects.all()
    all_agents = User.objects.filter(role__in=['AGENT1', 'AGENT2'])
    
    # Build agent workload data
    agent_data = []
    for agent in all_agents:
        agent_requests = ServiceRequest.objects.filter(assigned_to=agent)
        
        agent_stats = {
            'agent': agent,
            'role': agent.role,
            'total_assigned': agent_requests.count(),
            'pending': agent_requests.filter(status='Pending').count(),
            'under_review': agent_requests.filter(status='Under Review').count(),
            'in_progress': agent_requests.filter(status='In Progress').count(),
            'completed': agent_requests.filter(status='Completed').count(),
            'approved': agent_requests.filter(status='Approved').count(),
            'rejected': agent_requests.filter(status='Rejected').count(),
            'completion_rate': round((agent_requests.filter(status='Completed').count() / agent_requests.count() * 100), 1) if agent_requests.count() > 0 else 0,
        }
        agent_data.append(agent_stats)
    
    # Calculate overall stats
    total_assigned_all = ServiceRequest.objects.filter(assigned_to__isnull=False).count()
    total_unassigned = ServiceRequest.objects.filter(assigned_to__isnull=True).count()
    total_completed_all = ServiceRequest.objects.filter(status='Completed').count()
    
    context = {
        'pages': pages,
        'agent_data': agent_data,
        'total_agents': all_agents.count(),
        'total_assigned': total_assigned_all,
        'total_unassigned': total_unassigned,
        'total_completed': total_completed_all,
    }
    return render(request, 'admin-site/agent_workload.html', context)