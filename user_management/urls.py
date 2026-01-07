from django.urls import path,include
from .views import *

urlpatterns = [
    path('logout/', user_logout, name='logout'),
    path('user_registration/', user_registration, name='user_registration'),
    path('user_list/', user_list, name='user_list'),
    path('user_edit/<pk>/', user_edit, name='user_edit'),
    path('user_view/<pk>/', user_view, name='user_view'),
    path('user_delete/<pk>/', user_delete, name='user_delete'),
    path('roles/', roles, name='roles'),
    path('roles_create/', roles_create, name='roles_create'),
    path('roles_edit/<pk>/', roles_edit, name='roles_edit'),
    path('roles_delete/<pk>/', roles_delete, name='roles_delete'),
    path('permission/<pk>/', permission, name='permission'),
    path('function_setup/', function_setup, name='function_setup'),
     #======================Multi Tenent URLs=======================
    path('company_list/', company_list, name='company_list'),
    path('company/<int:pk>/', company_detail, name='company_detail'),
    path('company_create/', company_create, name='company_create'),
    path('company_update/<int:pk>/', company_update, name='company_update'),
    path('company_delete/<int:pk>/', company_delete, name='company_delete'),
    path('company_create_admin/', company_create_admin, name='company_create_admin'),


    path('select_company/',select_company,name='select_company'),

    path('select_supplier_store/<int:pk>/',select_supplier_store,name='select_supplier_store'),
    path('select_distributor_branches/<int:pk>/',select_distributor_branches,name='select_distributor_branches'),
    path('select_customer_store/<int:pk>/',select_customer_store,name='select_customer_store'),

    path('feedback_create/', feedback_create, name='feedback_create'),
    path('feedback_list/', feedback_list, name='feedback_list'),

]