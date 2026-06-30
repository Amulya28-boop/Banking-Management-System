from django.urls import path
from . import views

urlpatterns = [

    # ================= HOME =================
    path('', views.homepage, name='homepage'),
    path('dashboard/', views.dashboard, name='dashboard'),  

    # ================= AUTH =================
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.user_signup, name='signup'),

    # ================= CUSTOMER =================
    path('customers/', views.customer_list, name='customer_list'),
    path('add-customer/', views.add_customer, name='add_customer'),
    path('edit-customer/<int:customer_id>/', views.edit_customer, name='edit_customer'),
    path('delete-customer/<int:customer_id>/', views.delete_customer, name='delete_customer'),

    # ================= TRANSACTIONS =================
    path('deposit/<int:customer_id>/', views.deposit, name='deposit'),
    path('withdraw/<int:customer_id>/', views.withdraw, name='withdraw'),
    path('transfer/<int:customer_id>/', views.transfer, name='transfer'),
    path('history/<int:customer_id>/', views.transaction_history, name='transaction_history'),

    # ================= PDF =================
    path('statement/<int:customer_id>/', views.download_statement, name='download_statement'),

    # ================= ANALYTICS =================
    path('monthly-transactions/', views.monthly_transactions, name='monthly_transactions'),

    # ================= ABOUT =================
    path('about/', views.about, name='about'),

    path('monthly-dashboard/', views.monthly_transactions, name='monthly_dashboard'),

    path('customer/<int:customer_id>/', views.customer_profile, name='customer_profile'),

  
]