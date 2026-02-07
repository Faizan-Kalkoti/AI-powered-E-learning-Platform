from django.urls import path
from alltests import views
from django.conf import settings

app_name='alltests'

urlpatterns = [
    path('choose-pre-test/of/<slug:course_slug>/of-tests/<str:test_slug>/', views.PreTestPage, name="pretestpage"),
    path('main-test/of/<slug:course_slug>/of-tests/<str:testtypename>/', views.MainTestPage, name="maintest"),
    path('storeresult-api/', views.StoreResult.as_view(), name="storeresult"),
    path('show-all-results/<slug:course_slug>/', views.DisplayAllResults , name="showallresults"),
    path('show-maintest-result/of/<slug:course_slug>/<str:testtype>/and/<str:testname>/', views.DisplayResult, name="maintestresult"),
]
