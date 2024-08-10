from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense_list, name='expense_list'),
    path('<expense_id>/update/', views.expense_update, name='expense_update'),
    path('<expense_id>/delete/', views.expense_delete, name='expense_delete'),
    path('<expense_id>/clone/', views.expense_clone, name='expense_clone'),
    path('summary/', views.summary, name='expense_summary'),
]
