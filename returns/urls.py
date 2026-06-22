from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('devoluciones/', views.returns_dashboard, name='returns_dashboard'),
    path('reporte/', views.report_dashboard, name='report_dashboard'),
    path('usuarios/', views.users_dashboard, name='users_dashboard'),
    path('usuarios/<int:pk>/editar/', views.user_edit, name='user_edit'),
    path('usuarios/<int:pk>/eliminar/', views.user_delete, name='user_delete'),
    path('apelaciones/', views.appeals_dashboard, name='appeals_dashboard'),
    path('apelaciones/nueva/', views.appeal_create, name='appeal_create'),
    path('apelaciones/<int:pk>/', views.appeal_detail, name='appeal_detail'),
    path('apelaciones/<int:pk>/status/', views.appeal_update_status, name='appeal_update_status'),
    path('apelaciones/<int:pk>/editar/', views.appeal_edit, name='appeal_edit'),
    path('apelaciones/<int:pk>/eliminar/', views.appeal_delete, name='appeal_delete'),
    path('nueva/', views.return_create, name='return_create'),
    path('productos/buscar-ean/', views.product_lookup_by_ean, name='product_lookup_by_ean'),
    path('<int:pk>/', views.return_detail, name='return_detail'),
    path('<int:pk>/editar/', views.return_edit, name='return_edit'),
    path('<int:pk>/eliminar/', views.return_delete, name='return_delete'),
]
