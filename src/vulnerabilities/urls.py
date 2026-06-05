from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('', views.dashboard, name='dashboard'),
    path('report/', views.VulnerabilityCreateView.as_view(), name='report_vulnerability'),
    path('vulnerability/<int:pk>/', views.VulnerabilityDetailView.as_view(), name='vulnerability_detail'),
    path('vulnerability/<int:pk>/manage/', views.VulnerabilityUpdateView.as_view(), name='manage_vulnerability'),
    path('vulnerability/<int:pk>/complete/', views.VulnerabilityCompleteView.as_view(), name='complete_task'),
    
    # User Management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_add'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/profile/<int:pk>/', views.UserPublicProfileView.as_view(), name='public_profile'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),

    # Team Management
    path('teams/', views.TeamListView.as_view(), name='team_list'),
    path('teams/add/', views.TeamCreateView.as_view(), name='team_add'),
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('teams/<int:pk>/edit/', views.TeamUpdateView.as_view(), name='team_edit'),
    path('teams/<int:pk>/delete/', views.TeamDeleteView.as_view(), name='team_delete'),
]
