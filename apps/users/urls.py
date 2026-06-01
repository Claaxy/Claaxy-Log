from django.urls import path

from apps.users import views

app_name = 'users'

urlpatterns = [
    path('', views.user_list, name='list'),
    path('<int:pk>/delete/', views.user_delete, name='delete'),
]
