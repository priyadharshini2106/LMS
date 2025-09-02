# Fully coded urls.py for library
print('library urls.py loaded')
from django.urls import path
from . import views

urlpatterns = [
     path('', views.library_dashboard, name='library_dashboard'),
    # Book URLs
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/edit/<int:pk>/', views.edit_book, name='edit_book'),

    # Book Issue URLs
    path('issues/', views.issue_list, name='issue_list'),
    path('issues/add/', views.issue_book, name='issue_book'),
    path('issues/return/<int:pk>/', views.return_book, name='return_book'),
]
