from django.urls import path, include
from progress import views
from django.conf import settings

app_name = 'progress'

urlpatterns = [
    path('set-deadline/<slug:slug>/', views.SetDeadline, name='setdeadline'),
    path('set-deadline/<slug:slug>/', views.SetDeadlineAfterTest, name='setdeadlineaftertest'),
    
]