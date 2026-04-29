from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),

    # Admin URLs
    path('admin-login/', views.admin_login, name='admin_login'),
    path('adminsite/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # Ensure these names match {% url %} tags in templates
    path('adminsite/add-page/', views.add_page, name='add_page'),
    path('adminsite/page/<int:page_id>/', views.view_custom_page, name='view_custom_page'),
    path('adminsite/apply-details/', views.apply_details, name='apply_details'),
    path('adminsite/remove-assignment/<int:request_id>/', views.remove_assignment, name='remove_assignment'),
    path('adminsite/reassign-request/<int:request_id>/', views.reassign_request, name='reassign_request'),
    path('adminsite/user-details/', views.user_details, name='user_details'),
    path('adminsite/edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('adminsite/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('adminsite/add-service/', views.add_service, name='add_service'),
    path('adminsite/edit-service/<int:service_id>/', views.edit_service, name='edit_service'),
    path('adminsite/delete-service/<int:service_id>/', views.delete_service, name='delete_service'),
    path('adminsite/assign-request/<int:request_id>/', views.assign_request, name='assign_request'),
    path('adminsite/update-status/<int:request_id>/', views.update_request_status, name='update_request_status'),
    path('download-all-docs/<int:req_id>/', views.download_all_docs, name='download_all_docs'),

    # User URLs
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user/request/<int:request_id>/', views.user_request_detail, name='user_request_detail'),
    path('user/apply/<int:service_id>/', views.apply_service, name='apply_service'),

    # Agent2 URLs
    path('agent2-login/', views.agent2_login, name='agent2_login'),
    path('agent2/dashboard/', views.agent2_dashboard, name='agent2_dashboard'),
    path('agent2/new-requests/', views.agent2_new_requests, name='agent2_new_requests'),
    path('agent2/in-progress/', views.agent2_in_progress, name='agent2_in_progress'),
    path('agent2/completed/', views.agent2_completed, name='agent2_completed'),
    path('agent2/request/<int:request_id>/', views.agent2_request_detail, name='agent2_request_detail'),
    path('agent2/forward/<int:request_id>/', views.agent2_forward, name='agent2_forward'),
    path('agent2/service/', views.agent2_service, name='agent2_service'), # Ensure this line is present
    path('agent2/apply/<int:service_id>/', views.agent2_apply, name='agent2_apply'),
    path('agent2/upload/', views.agent2_upload, name='agent2_upload'),
    path('agent2/apply-details/', views.agent2_apply_details, name='agent2_apply_details'),
    path('agent2/complete-details/', views.agent2_complete_details, name='agent2_complete_details'),

    # Agent1 URLs
    path('agent1-login/', views.agent1_login, name='agent1_login'),
    path('agent1/dashboard/', views.agent1_dashboard, name='agent1_dashboard'),
    path('agent1/new-requests/', views.agent1_new_requests, name='agent1_new_requests'),
    path('agent1/assigned-requests/', views.agent1_assigned_requests, name='agent1_assigned_requests'),
    path('agent1/in-progress/', views.agent1_in_progress, name='agent1_in_progress'),
    path('agent1/completed/', views.agent1_completed, name='agent1_completed'),
    path('agent1/request/<int:request_id>/', views.agent1_request_detail, name='agent1_request_detail'),
    path('agent1/complete/<int:request_id>/', views.agent1_complete, name='agent1_complete'),
    path('agent1/download-report/<int:request_id>/', views.agent1_download_report, name='agent1_download_report'),
    path('agent1/take-request/<int:request_id>/', views.take_request, name='take_request'),
    
    # Agent1 Apply Details & Actions
    path('agent1/apply-details/', views.agent1_apply_details, name='agent1_apply_details'),
    path('agent1/remove-assignment/<int:request_id>/', views.agent1_remove_assignment, name='agent1_remove_assignment'),
    path('agent1/assign-request/<int:request_id>/', views.agent1_assign_request, name='agent1_assign_request'),
    
    # Admin Actions
    path('admin/assign-request/<int:request_id>/', views.admin_assign_request, name='admin_assign_request'),
    path('admin/agent-workload/', views.admin_agent_workload, name='admin_agent_workload'),
]