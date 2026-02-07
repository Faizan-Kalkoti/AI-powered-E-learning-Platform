from django.urls import path
from modules import views

app_name='modules'

urlpatterns =[
   path('create-module/<slug:course_slug>/<slug:section_slug>/',views.CreateModule.as_view(), name='createmodule'), 
   path('detail-module/<slug:course_slug>/<slug:section_slug>/<slug:slug>/', views.DetailModule.as_view(), name='detailmodule'),
   path('update-module/<slug:course_slug>/modules/<slug:slug>/', views.UpdateModule.as_view(), name='updatemodule'),
   path('delete-module/<slug:course_slug>/modules/<slug:slug>/', views.DeleteModule.as_view(), name='deletemodule'),
   path('complete-modules/<slug:module_slug>/', views.CompleteModule, name="completemodule"),
]
