from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

from django.db.models import Count
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.urls import reverse
from django.views.generic import ListView, DeleteView, UpdateView

from courses.models import Course
from sections.models import Section, Available_sections
from coursetests.models import Test_space, Pretest_result, Startcourse
from progress.models import TestFeedback, TestResults, RevisionSections
from alltests.models import LevelsAvailable, TestResultsDetail

# For result calculation
from coursetests.pre_test_result_calculation import FindAndStoreRevisionSections


# For Gen Ai gemini model 
import pathlib
import textwrap 
from datetime import date
from collections import Counter


import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown
import misaka


""" This is how the views are arranged here
1. to first test page view
2. to main create test page
3. to submit the created questions before
4. to display the questions in a list (and filter them as well)
5. to update the questions induvidually
6. to delete the questions induvidually"""
 


# Create your views here.
#1. View to go to Test course - section selection page
@login_required
def create_test_1(request, course_slug):
    course = get_object_or_404(Course, slug = course_slug)
    return render(request, 'tests/create_test_1.html', {'course':course})

#2. View to go to Test creation Javascript page
@login_required
def create_test_2(request, course_slug):
    course = get_object_or_404(Course, slug = course_slug)
    section_selected = request.POST.get('selected_section')
    section = get_object_or_404(Section, slug = section_selected)
    return render(request, 'tests/create_test_2.html', {'course':course, 'section': section})


#3. View for creating the questions through RestAPIs
class Create_questions(LoginRequiredMixin, APIView):
    def post(self, request, *args, **kwargs):
        data = request.data

        for item in data:
            question = item.get('question')
            options_a = item.get('optionA')
            options_b = item.get('optionB')
            options_c = item.get('optionC')
            options_d = item.get('optionD')
            answer = item.get('correctAns', 'A')
            
            course_slug = kwargs.get('course_slug')
            section_slug = kwargs.get('section_slug')

            course_i = get_object_or_404(Course, slug=course_slug)
            section_i = get_object_or_404(Section, slug=section_slug)
            teacher_i = request.user.teacher
            level = section_i.Difficulty.lower()

            test_space_instance = Test_space.objects.create(
                question=question,
                options_a=options_a,
                options_b=options_b,
                options_c=options_c,
                options_d=options_d,
                answer=answer,
                level=level,
                course=course_i,
                section=section_i,
                teacher=teacher_i)
            
            print(test_space_instance)
        return Response("Data successfully processed", status=status.HTTP_201_CREATED)



#4. Views for listing the questions created
class ListQuestions(LoginRequiredMixin, ListView):
    template_name = 'tests/question_list.html'
    model = Test_space
    context_object_name = 'questions'
    paginate_by = 5

    # To filter the question records by course - section - level
    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug', None)
        course1 = get_object_or_404(Course, slug = course_slug)
        queryset = Test_space.objects.filter(course=course1)
        # section_slug = self.request.GET.get('section', None)
        # level_filter = self.request.GET.get('level',None)
        level_filter = self.kwargs.get('level', None)
        section_slug = self.kwargs.get('section_slug', None)

        if level_filter:
            queryset = queryset.filter(level=level_filter)
        if section_slug:
            section_filter = get_object_or_404(Section, slug=section_slug)
            queryset = queryset.filter(section=section_filter)        
        return queryset

    # This is for passing the course object as well
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_slug = self.kwargs.get('course_slug', None)
        course = get_object_or_404(Course, slug = course_slug)
        context["course"] = course

        queryset = self.object_list
        count = queryset.count()
        context['count'] = count
        return context
    

#5. UpdateQuestion
class UpdateQuestion(LoginRequiredMixin, UpdateView):
    template_name="tests/update_question.html"
    model = Test_space
    fields = ['question', 'options_a', 'options_b', 'options_c', 'options_d', 'answer', 'level']

    def get_success_url(self):
        course_slug = self.kwargs.get('course_slug')
        return reverse('coursetests:listquestions', kwargs={'course_slug': course_slug})
    

#6. DeleteQuestion
class DeleteQuestion(LoginRequiredMixin, DeleteView):
    template_name = 'tests/delete_question.html'
    model = Test_space

    def get_success_url(self):
        course_slug = self.kwargs.get('course_slug')
        return reverse('coursetests:listquestions', kwargs={'course_slug': course_slug})


# view to go for pre_requisite_1 page (initial option page)
def Pre_option_template(request, course_slug):
    course = get_object_or_404(Course, slug = course_slug)
    return render(request, 'tests/pre_requisite1.html', {'course':course})


# view to go for pre_requisite test page (main test page)
def Pre_test(request, course_slug):
    course = get_object_or_404(Course, slug = course_slug)
    questions = Test_space.objects.filter(course=course)
    pre_questions = questions.filter(level='easy')
    # Ensure there are at least 15 records available
    random_questions = None
    if pre_questions.count() >= 15:
        random_questions = pre_questions.order_by('?')[:15]
        # print(random_questions)
    else:
        print("Not enough records to select 15 randomly.")
        return render(request,'tests/no_questions.html', context={'course':course})

    if hasattr(request.user, 'student'):
        try:
            start_course = Startcourse.objects.filter(student=request.user.student, course=course).first()
        except ObjectDoesNotExist:
            start_course = None
        give_test = 'no'
        if start_course is not None:
            if start_course.has_given == 'No':
                start_course.has_given = 'Yes'
                start_course.save()
                give_test = 'yes'
        else:
            start_course= Startcourse.objects.create(student=request.user.student, course=course, has_given='Yes')
            give_test = 'yes'                

    # Check if the request is an AJAX request
    if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        question_list = []
        for question in random_questions:
            question_data = {
                "question": question.question_text,
                "options": [question.option_a, question.option_b, question.option_c, question.option_d]
            }
            question_list.append(question_data)
        return JsonResponse({"questions": question_list})

    return render(request,'tests/pre_requisite2.html', {'course':course, 'questions':random_questions, "give_test": give_test})


# View to accept the data from the test and store it in the models
class StoreResult(LoginRequiredMixin, APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        current_student = request.user.student

        for record in data:
            record_id = record.get('qID')
            record_ans = record.get('ans')

            curr_question = Test_space.objects.get(id=record_id)
            current_ans = 'W'
            current_ans = 'Correct' if curr_question.answer == record_ans else 'Wrong'
            
            # Create the record in the dbms at the end
            rec = Pretest_result.objects.create(student=current_student, question=curr_question, answer=current_ans)
            # print(rec.answer, rec.question)
        return Response("Data successfully processed", status=status.HTTP_201_CREATED)
    





# View to go to the results page
@login_required
def Pre_result(request, course_slug):
    course = get_object_or_404(Course, slug = course_slug)
    current_student = request.user.student
    pre_test_result  = Pretest_result.objects.filter(student=current_student)
    count_given = pre_test_result.count()
    right_ans = pre_test_result.filter(answer='Correct').count()  # Counting correct answers
    wrong_ans = pre_test_result.filter(answer='Wrong').count()
    result = None
    print("count:", count_given)
    print(right_ans)
    if right_ans >=11:
        result = 'pass'
    else: 
        result = 'fail'

    # To also make the sections available in those levels 
    if result == 'pass':      
        get_sections = Section.objects.filter(Difficulty='Easy', belong_to_course=course)
        get_sections2 = Section.objects.filter(Difficulty='Medium', belong_to_course=course)
        for a1 in get_sections:
          try:
            Available_sections.objects.create(student=current_student,section=a1)
          except IntegrityError as e:
            print("oops..")

        for a2 in get_sections2:
          try:
            Available_sections.objects.create(student=current_student,section=a2)
          except IntegrityError as e:
            print("oops..")  

        # To set the levels as per the results    
        if LevelsAvailable.objects.filter(student = current_student, course=course).exists():
            lvl_available = LevelsAvailable.objects.filter(student = current_student, course=course).count()
            if lvl_available==1:
                LevelsAvailable.objects.create(student=current_student, course=course, level='medium')
        else:
            LevelsAvailable.objects.create(student=current_student, course=course, level='easy')
            LevelsAvailable.objects.create(student=current_student, course=course, level='medium')

    else:
        get_sections = Section.objects.filter(Difficulty='Easy' , belong_to_course=course)
        for a1 in get_sections:
          try:
            Available_sections.objects.create(student=current_student,section=a1)
          except IntegrityError as e:
            print("oops..")     
        if not LevelsAvailable.objects.filter(student = current_student, course=course).exists():
            LevelsAvailable.objects.create(student=current_student, course=course, level='easy')          
   

    wrgsec_str =""
    wrglist_str =""
    for a in pre_test_result.filter(answer='Wrong'):
        wrgsec_str = wrgsec_str + a.question.section.section_name+", "
        wrglist_str = wrglist_str + a.question.question + ", "

    print("result", result, ", right ans: ", right_ans, ", wrong_ans: ", wrong_ans, ", wrgsec_str: ", wrgsec_str, "wrglist_str: ", wrglist_str)
    print("course: ", course.course_name)
    print('all the data is going correctly')

    # For feedback from api
    input_prompt_str = f""" Result of the test: {result}, marks: {right_ans} out of 15 questions and {wrong_ans} wrong answers.  
    for the course: {course.course_name}, sections name: {wrgsec_str} and the questions that were wrong are: {wrglist_str}
    for this first generate a Feedback to guide student to improve in these topics and then tell 
    them which materials to study (like the website name) and how much time to spend on which topic that will help them 
    get better at these topics for this course, After this given below output format:

    Topics to focus on :
    1. topic name1.. [time required in hrs and mins]
    2. topic name2.. [time required in hrs and mins]
    ...etc
    
    The resources to study from:
    topics name: website names or book names (no links)
    ....etc
    """ 
    feedback_response =""

    try:
      print(input_prompt_str)
      print("input prompt is also correct")

      genai.configure(api_key = "AIzaSyArwwwB0pHLnPSTAJsgS7kntXbDkh4XDFY")
      print("configured correctly")
      model = genai.GenerativeModel('gemini-pro')
      print("model goes correctly")
    
      response = model.generate_content(input_prompt_str)
      print("this is the respose \n ", response.prompt_feedback)
      feedback_response = ""
      feedback_response = feedback_response + response.text
    except Exception as e:
        feedback_response = "No feedback.. We face some problem in generating feedback!"

    # Result table in the model
    result_record= TestResults.objects.create(test_name='pretest', student=current_student,total_marks=15,
                                              course=course  ,status=result, score=right_ans, on_time=True)
    
    # Store a feedback in the model
    if not TestFeedback.objects.filter(student = current_student, course=course).exists():
        TestFeedback.objects.create(
        student=current_student, course=course,
        testname=result_record, feedback=feedback_response)
    else:
        feedback1 = TestFeedback.objects.get(student = current_student, course=course) 
        feedback1.testname=result_record 
        if feedback_response=="":
            print("No feedback")
        else:
            feedback1.feedback=feedback_response
        feedback1.save()



    # For Revision sections recommendation
    # We use this function to find the revision section 
    # And store data in the model
    FindAndStoreRevisionSections(current_student, course)

    # Create a Markdown parser with the desired renderer and extensions
    renderer = misaka.HtmlRenderer()
    md = misaka.Markdown(renderer)
    # Parse the Markdown text and render it as HTML
    feedback_response_html = md(feedback_response)
    
    score = int((right_ans/15)*100)
    return render(request, 'tests/pretest_result.html', {'result':result, 'score':score, 'wrong':wrong_ans, 
                                                         'feedback': feedback_response_html, 'attempted':count_given, 
                                                         'course':course, 'right': right_ans})