from django.urls import path
from . import views

app_name = 'todo'

urlpatterns = [
    path('health/', views.get_health),
    path('', views.general_todo),
    path('size/', views.get_total_todo),
    path('content/', views.get_todo_data),
]
