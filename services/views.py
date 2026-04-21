from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.db.models import Q
from functools import wraps
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

def services(request):
    services = Service.objects.all()
    return render(request, 'service.html', {'services': services})

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
    all_requests = ServiceRequest.objects.all().order_by('-created_at')
    pages = Page.objects.all()
    agents = User.objects.filter(role='AGENT1')

    # Choose template based on user role to maintain UI consistency
    template_name = 'admin-site/apply_details.html'
    if request.user.role == 'AGENT1':
        template_name = 'agent1-site/apply_details.html'

    return render(request, template_name, {'pages': pages, 'requests': all_requests, 'agents': agents})


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
            agent = get_object_or_404(User, id=agent_id, role='AGENT1')
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
    service_request = get_object_or_404(ServiceRequest, id=request_id, user=request.user)
    return render(request, 'details.html', {'request': service_request})

@login_required
@role_required(['USER'])
def apply_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        dob = request.POST.get('dob')
        email = request.POST.get('email')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        aadhaar = request.POST.get('aadhaar')
        description = request.POST.get('description', '')
        photo = request.FILES.get('photo')
        aadhaar_card = request.FILES.get('aadhaar_card')
        pan_card = request.FILES.get('pan_card')
        signature = request.FILES.get('signature')
        address_proof = request.FILES.get('address_proof')

        if not (full_name and dob and email and mobile and aadhaar):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'user-site/apply.html', {'service': service})

        ServiceRequest.objects.create(
            user=request.user,
            service=service,
            full_name=full_name,
            dob=dob,
            email=email,
            address=address,
            mobile=mobile,
            aadhaar_number=aadhaar,
            photo=photo,
            aadhaar_card=aadhaar_card,
            pan_card=pan_card,
            signature=signature,
            address_proof=address_proof,
            description=description
        )
        messages.success(request, 'Your request has been submitted and is under review.')
        return redirect('user_dashboard')

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

@login_required
@role_required(['AGENT2'])
def agent2_dashboard(request):
    """
    Agent2 main dashboard with status, service, and search filtering.
    """
    all_assigned = ServiceRequest.objects.filter(
        assigned_to=request.user
    ).order_by('-created_at')

    # Filters
    status_filter = request.GET.get('status')
    service_filter = request.GET.get('service')
    search_query = request.GET.get('search')

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

    pages = Page.objects.all()
    available_services = Service.objects.all()
    
    context = {
        'requests': all_assigned,
        'pages': pages,
        'services': available_services,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'search_query': search_query,
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
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to=request.user)
    pages = Page.objects.all()
    
    context = {
        'req': service_request,
        'pages': pages,
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
    }
    return render(request, 'agent2-site/service.html', context)

@login_required
@role_required(['AGENT2'])
def agent2_apply(request, service_id):
    """Agent2 view to apply for a service, using the agent2-specific apply template."""
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        dob = request.POST.get('dob')
        email = request.POST.get('email')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        aadhaar = request.POST.get('aadhaar')
        description = request.POST.get('description', '')
        
        photo = request.FILES.get('photo')
        aadhaar_card = request.FILES.get('aadhaar_card')
        pan_card = request.FILES.get('pan_card')
        signature = request.FILES.get('signature')
        address_proof = request.FILES.get('address_proof')

        if not (full_name and dob and email and mobile and aadhaar):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'agent2-site/apply.html', {'service': service})

        ServiceRequest.objects.create(
            user=request.user,
            service=service,
            full_name=full_name,
            dob=dob,
            email=email,
            address=address,
            mobile=mobile,
            aadhaar_number=aadhaar,
            photo=photo,
            aadhaar_card=aadhaar_card,
            pan_card=pan_card,
            signature=signature,
            address_proof=address_proof,
            description=description
        )
        messages.success(request, 'Application submitted successfully.')
        return redirect('agent2_dashboard')

    return render(request, 'agent2-site/apply.html', {'service': service})

@login_required
@role_required(['AGENT2'])
def agent2_forward(request, request_id):
    """Agent2 forwards request to Agent1"""
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to=request.user)
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
    }
    return render(request, 'agent2-site/agent2_upload.html', context)

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
    """Agent1 view for specific request details. Moves status to 'In Progress' on first view."""
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_to=request.user)
    
    # Transition status when Agent 1 begins processing
    if service_request.status == 'Under Review':
        service_request.status = 'In Progress'
        service_request.save()
        messages.info(request, f"Application #{request_id} has been moved to 'In Progress'.")

    pages = Page.objects.all()
    
    context = {
        'request': service_request,
        'pages': pages,
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