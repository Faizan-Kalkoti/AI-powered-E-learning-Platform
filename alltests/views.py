from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from alltests.models import LevelsAvailable, AttemptedTest, TestResultsDetail
from courses.models import Course, Course_members
from sections.models import Section, Available_sections, Section_completed
from accounts.models import Student, Teacher
from coursetests.models import Test_space
from progress.models import TestResults, TestFeedback, RevisionSections, CourseCompleted
from alltests.course_test import (GetTestType, GenerateQuestionsForExpertLevelTest, GenerateQuestionsForPeriodicTest,
                                  GenerateQuestionsForMediumLevelTest, GenerateQuestionsForHardLevelTest,
                                  GenerateQuestionsForCourseCompletionTest)

from alltests.result_functions import (GenerateFeedback, FindAndStoreRevisionSection, MakeLevelsAvailable)
from alltests.models import PeriodicTestActive, MissedPeriodicTests

from IPython.display import display
from IPython.display import Markdown
import misaka

import pathlib
import textwrap 
from datetime import date
from collections import Counter
import google.generativeai as genai

from django.core.exceptions import ObjectDoesNotExist



# views for 1. Test_view_1 (pre_Test)-> Test_view_2 (main_questions_test_page) -> Test_view_3 (to store the result in db) -> Test_View_4 (to_)


# 1. view to show the page before the tests
@login_required
def PreTestPage(request, course_slug, test_slug):
    course1 = get_object_or_404(Course,slug=course_slug)
    reason = None
    if hasattr(request.user, 'student'):
        student1 = get_object_or_404(Student, user=request.user)
        if Course_members.objects.filter(course=course1, student=student1).exists():
            return render(request, 'alltests/pre_test_page.html', {'course':course1, 'testtype':test_slug})
        else:
            reason = "You are not a part of this course!"
            return render(request, 'alltests/test_not_allowed.html', {'course':course1, 'reason':reason})      
    else:
        reason = 'You are not a student!'
        return render(request, 'alltests/test_not_allowed.html', {'course':course1, 'reason':reason})
    





# (2) View to go to the main test page
# view to go for pre_requisite test page (main test page)
@login_required
def MainTestPage(request, course_slug, testtypename):
    course = get_object_or_404(Course, slug = course_slug)
    student1 = get_object_or_404(Student, user=request.user)

    questions = Test_space.objects.filter(course=course)
    testtype = None
    reason = None
    testquestions = None
    # To get the test type
    testtype = GetTestType(course, student1, testtypename)

    # Ensure there are at least 20 records available
    if questions.count() <=20:
        reason = "Less than minimum required questions are present in the course!"
        return render(request,'alltests/error_test_page.html', context={'course':course, 'reason':reason})

    if testtype==None:
        reason = "You have not completed the required modules"
        return render(request,'alltests/error_test_page.html', context={'course':course, 'reason':reason})
    
    elif testtype=='medium_level_test':
        testquestions =  GenerateQuestionsForMediumLevelTest(course)
    elif testtype=='hard_level_test':
        testquestions = GenerateQuestionsForHardLevelTest(course)
    elif testtype=='expert_level_test':
        testquestions = GenerateQuestionsForExpertLevelTest(course)
    elif testtype=='periodic_test':
        if PeriodicTestActive.objects.filter(student=student1, course=course).exists():
            current_periodic_test = PeriodicTestActive.objects.filter(student=student1, course=course).first()
            periodic_test_name = current_periodic_test.testname
            testquestions = GenerateQuestionsForPeriodicTest(student1 ,course)
        else:
            reason = "You don't have any active periodic tests!"
            return render(request, 'alltests/error_test_page.html', context={'course':course, 'reason':reason} )
    elif testtype=='complete_course_test':
        testquestions = GenerateQuestionsForCourseCompletionTest(course)

    print(testtype, "line 94")
    if testquestions == None:
        print("error while fetching questions")
        reason = "No questions were selected! while retrieving the questions"
        return render(request,'alltests/error_test_page.html', context={'course':course, 'reason':reason})
  

    if hasattr(request.user, 'student'):
        try:
            # here we check if the student is tryingn to give the test again (Same type only not name)
            if AttemptedTest.objects.filter(student=request.user.student, course=course, testtype=testtypename).exists():
                start_test = AttemptedTest.objects.filter(student=request.user.student, course=course, testtype=testtypename).first() 
                if start_test.date_attempted==date.today():
                    reason = 'You can Attempt only One test a day!'
                    return render(request, 'alltests/error_test_page.html', context={'course':course, 'reason':reason})
                
            start_test = AttemptedTest.objects.create(student=request.user.student, course=course, testtype=testtypename, testname=testtype) 
        except Exception as e:
             reason = "some error occured!"
             print(str(e)) 
             return render(request, 'alltests/error_test_page.html', context={'course':course, 'reason':reason})    

    # Check if the request is an AJAX request
    if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        question_list = []
        for question in testquestions:
            question_data = {
                "question": question.question_text,
                "options": [question.option_a, question.option_b, question.option_c, question.option_d]
            }
            question_list.append(question_data)
        return JsonResponse({"questions": question_list})
    
    if testtypename == "periodic_test":
       testtype= periodic_test_name
       if testquestions != None and current_periodic_test != None:
           current_periodic_test.delete()
    return render(request,'alltests/all_tests.html', {'course':course, 'questions':testquestions, "give_test": start_test, 'testtype':testtypename, 'testname':testtype})





# View to accept the data from the test and store it in the models
class StoreResult(LoginRequiredMixin, APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        current_student = request.user.student
        try:

            for record in data:
                record_id = record.get('qID')
                record_ans = record.get('ans')
                record_type = record.get('testtype')
                record_name = record.get('testname')
                
                curr_question = Test_space.objects.get(id=record_id)
                current_ans = 'w'
                
                if curr_question.answer == record_ans:
                    current_ans = 'r' 
                elif curr_question.answer != record_ans: 
                    current_ans = 'w' 
                    
                # Create the record in the dbms at the end
                rec = TestResultsDetail.objects.create(student=current_student, course=curr_question.course, section=curr_question.section,
                                                   question=curr_question, answer=current_ans, testtype=record_type, testname=record_name)
        except Exception as e:
            print("exception while inerting the data - ",str(e))
                # print(rec.answer, rec.question)
        return Response("Data successfully processed", status=status.HTTP_201_CREATED)
    


# view for displaying all the past result data
def DisplayAllResults(request, course_slug):
    course1 = get_object_or_404(Course, slug=course_slug)
    student_results = None
    student_attempted_tests = None
    missed_tests = None

    try:
        if TestResults.objects.filter(student=request.user.student, course=course1).exists():
            student_results = TestResults.objects.filter(student=request.user.student, course=course1)
            if AttemptedTest.objects.filter(course=course1,student=request.user.student).exists():
                student_attempted_tests = AttemptedTest.objects.filter(course=course1,student=request.user.student)
                if MissedPeriodicTests.objects.filter(course=course1, student=request.user.student).exists():
                    missed_tests = MissedPeriodicTests.objects.filter(course=course1, student=request.user.student)
    except Exception as e:
        print("An exception occured!", str(e))
    return render(request, 'alltests/past_test_results.html', {'course': course1, 'student_results': student_results, 
                                                               'attempted_tests':student_attempted_tests,
                                                               'missed_tests':missed_tests})





# View For calculating result and displaying it
def DisplayResult(request, course_slug, testtype, testname):
    test_result = None
    result_status = None
    feedback = None
    make_level_available = None  # To get the level (to unlock)
    revision_section = None
    score = 0
    message = "This is the result page"
    result_record = None
    right_answer_questions,wrong_answer_questions = None, None
    no_of_right_answers, no_of_wrong_answers, no_of_unattempted_answers = None, None, None

    try:
        course1 = get_object_or_404(Course, slug=course_slug)
        student1 = get_object_or_404(Student, user=request.user)
        if TestResultsDetail.objects.filter(course=course1, student=request.user.student, date_given=date.today(), testtype=testtype, testname=testname).exists():
            print("todays test records found!")
            test_result = TestResultsDetail.objects.filter(course=course1, student=request.user.student, date_given=date.today(), testtype=testtype, testname=testname)
            right_answer_questions = test_result.filter(answer='r')
            wrong_answer_questions = test_result.filter(answer='w')
            no_of_right_answers = test_result.filter(answer='r').count()
            no_of_wrong_answers = test_result.filter(answer='w').count()
            no_of_unattempted_answers = 20-no_of_right_answers-no_of_wrong_answers

            # IF passed
            if no_of_right_answers>=13:
                # 1. To create a record in TestResults model
                result_status = 'pass'
                result_record = TestResults.objects.create(test_name=testname, course=course1, student=request.user.student, 
                                            status='pass', score=no_of_right_answers, total_marks=20, on_time=True)
                
                # 2. To make the levels available
                if testtype =='levelup':
                    make_level_available = MakeLevelsAvailable(student1, course1, testtype)

                # 3. To generate the feedback
                if no_of_wrong_answers>0:
                    feedback = GenerateFeedback(student1, course1, result_status, no_of_right_answers, no_of_wrong_answers, wrong_answer_questions, result_record)
                else: 
                    feedback = "No feedback - Since No wrong answers in the attempted questions!"

                # 4. To Make sections available
                if testtype == 'levelup' and make_level_available is not None and make_level_available !='completecourse':
                        if Section.objects.filter(belong_to_course=course1, Difficulty=make_level_available).exists():
                            sections_to_make_available = Section.objects.filter(belong_to_course=course1, Difficulty=make_level_available)
                            for section1 in sections_to_make_available:
                                if not Available_sections.objects.filter(section=section1, student=request.user.student).exists():
                                    section = Available_sections.objects.create(section=section1, student=request.user.student)   
                                    print("Made section available: ", section)   
                        else:
                            print("error while making sections available!") 
            # IF failed                                                                     
            else:
                # 1. To create a record in TestResults model
                result_status = 'fail'
                result_record = TestResults.objects.create(test_name=testname, course=course1, student=request.user.student, status='fail', score=no_of_right_answers,
                                            total_marks=20, on_time=True)
                
                # 2. To generate feedback 
                if no_of_wrong_answers>0:
                    feedback = GenerateFeedback(student1, course1, result_status, no_of_right_answers, no_of_wrong_answers, wrong_answer_questions, result_record)
                else: 
                    feedback = "No feedback - Since No wrong answers in the attempted questions!"

                # 3. To recommend revision sections
                if wrong_answer_questions.count()>4:
                    revision_section = FindAndStoreRevisionSection(student1, course1, wrong_answer_questions)  
                    # We also uncheck the sections and modules that are a part of the revision section

            # IF testtype is "course completed"
            if testtype == 'coursecompleted' or make_level_available=='completecourse':
                if result_status == 'pass':
                    if not CourseCompleted.objects.filter(student=student1, course=course1).exists():
                        CourseCompleted.objects.create(student=student1, course=course1)
                        print("You have completed the course")
                        message = "Contratulations, You have successfully completed the course!"
                else:
                    message = "You have failed the Course completion test, please Revise and try again tomorrow!"
                testtype = 'coursecompleted'   

                
            # To calculate the score
            score = int((no_of_right_answers/20) * 100)

            # check if the result has been updated for the current test 
            # (if it has then delete the records from the TestResultsdetail table)
            if result_record is not None:
                test_result.delete()
            

            return render(request, 'alltests/results_page.html', {'feedback':feedback, 'level_made_available':make_level_available, 
                                                                'result_status': result_status, 'right_count': no_of_right_answers ,
                                                                'wrong_count':no_of_wrong_answers, 'unattermpted':no_of_unattempted_answers,
                                                                'testtype':testtype, 'revision_section': revision_section, 'score':score,
                                                                'message':message, 'course':course1})

    except Exception as e:
        print("exception in DisplayResult() method!", str(e))
        message = "Server Side Error Occurred!"
        return render(request, 'alltests/unauthorized_page.html')
    
    return render(request, 'alltests/results_page.html', {'feedback':feedback, 'level_made_available':make_level_available, 
                                                                'result_status': result_status, 'right_count': no_of_right_answers ,
                                                                'wrong_count':no_of_wrong_answers, 'unattermpted':no_of_unattempted_answers,
                                                                'testtype':testtype, 'revision_section': revision_section, 'score':score,
                                                                'message':message, 'course':course1})

    # 1. Calculate the result (pass/fail & score)
    # 2. Check the type of test it was (store it in a variable)
    # 3. Update the result in TestResults model
    # 4. If passed perform the following functions
    #       - Make the next level available (based on type of test)
    #       - generate feedback content (api) 
    #         (condition: if we have atleast single wrong question)
    #       - Make sections available
    # 5. If failed :
    #       - generate feedback on wrong questions/missed questions
    #       - to recommend revision section
    #       - To uncheck the section modules that have been completed (that belongs to revision section)
    # 6. Caculate the score % etc.. and display it to the template in a graph
    # 7. pass the level being unlocked if (levelup type test - > so that we can display image)
    # 8. Implement error handling as well



# 1. also add levels-available content when storing the result or starting the course (in startcourse/ pre_requisite tests)
# 2. also we need to add available levels when giving the tests for level up
# 3. We also need to pass available levels to the course_detail page for use (in context)

# def ShowCourseTest(request, courseslug):
#     course1 = get_object_or_404(Course, slug=courseslug)
#     levels_available_to_student = None
#     try:
#         if LevelsAvailable.objects.filter(course=course1, student=request.user.student).exists():
#             levels_available_to_student = LevelsAvailable.objects.filter(course=course1, student=request.user.student)
            

#     except Exception as e:
#         print(str(e))
#         return render(request, 'test_not_allowed.html')




# # View to submit and calculate the test result
# def CourseTestSubmit(request, courseslug):

#     return render(request,)
