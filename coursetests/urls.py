from django.urls import path
from coursetests import views

app_name ="coursetests"

urlpatterns = [
    path('create-test1/<slug:course_slug>/', views.create_test_1, name="createtest1"),
    path('create-test-questions-2/<slug:course_slug>/', views.create_test_2, name='createtest2'),
    # List questions with filters
    path('list-all-questions/of/<slug:course_slug>/', views.ListQuestions.as_view(), name="listquestions"),
    path('filtered-questions-section/of/<slug:course_slug>/with/<slug:section_slug>/', views.ListQuestions.as_view(), name='listquestions_section'),
    path('filtered-questions-level/of/<slug:course_slug>/with/<str:level>/', views.ListQuestions.as_view(), name='listquestions_level'),

    path('update-question/of/<int:pk>/in/<slug:course_slug>/', views.UpdateQuestion.as_view(), name="updatequestion"),
    path('delete-question/of/<int:pk>/in/<slug:course_slug>/', views.DeleteQuestion.as_view(), name='deletequestion'),

    # URL path for rest api questions below
    path('send-questions/<slug:course_slug>/of/<slug:section_slug>/', views.Create_questions.as_view(), name="sendquestions"),

    # URL for prerequisite tests
    path('choose-pre-test/of/<slug:course_slug>/', views.Pre_option_template, name="pretestoption"),
    path('pre-requisite-test/for/<slug:course_slug>/', views.Pre_test, name="pretest"),
    path('pre-requisite-test-result/for/<slug:course_slug>/', views.Pre_result, name="pretestresult"),
    path('test-result-submission/', views.StoreResult.as_view(), name="storeresult"),
]
 