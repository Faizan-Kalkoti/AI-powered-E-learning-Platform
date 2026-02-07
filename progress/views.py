from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError

# db imports here
from courses.models import Course, Course_members
from sections.models import Section, Available_sections
from accounts.models import Student, Teacher
from progress.models import DeadlineGiven, RevisionSections
from coursetests.models import Startcourse
from alltests.models import LevelsAvailable


# Create your views here.

# 1. View for Setting deadline when starting the course
def SetDeadline(request, slug):
    mycourse = get_object_or_404(Course, slug=slug)
    student = get_object_or_404(Student, name = request.user.username)

    if request.method == 'POST':
        deadline_given =  request.POST.get('inputDate')
        try:
          DeadlineGiven.objects.create(student=student, course=mycourse, deadline=deadline_given, deadline_finished=False)       
        except IntegrityError as e:
           print("already records exists for same student and course")
        
        if not Startcourse.objects.filter(student=student, course=mycourse, has_given='No').exists():
           Startcourse.objects.create(student=student, course=mycourse, has_given='No')
        # Now to make the sections available
        get_sections = Section.objects.filter(Difficulty='Easy' , belong_to_course=mycourse)
        if not LevelsAvailable.objects.filter(student = student, course=mycourse).exists():
            LevelsAvailable.objects.create(student = student, course=mycourse, level="Easy")
        else:
           print("there is already a level available existing, did u forget to delete from admin or something?")
        for a1 in get_sections:
          try:
            Available_sections.objects.create(student=student,section=a1)
          except Exception as e:
            print("oops..", str(e)) 
        return redirect('courses:singlecourse',slug=slug)
        
    
    context = {'slug': slug} 
    return render(request, 'courses/course_detail.html', context)






# View to set deadline after we give the test
def SetDeadlineAfterTest(request, slug):
    mycourse = get_object_or_404(Course, slug=slug)
    student = get_object_or_404(Student, name = request.user.username)

    if request.method == 'POST':
        deadline_given =  request.POST.get('inputDate')
        try:
           DeadlineGiven.objects.create(student=student, course=mycourse, deadline=deadline_given, deadline_finished=False)
           Startcourse.objects.create(student=student, course=mycourse, has_given='Yes')
        except IntegrityError as e:
           print("Integrity Exception - There is a same record in the db")

        return redirect('courses:singlecourse',slug=slug)
    
    context = {'slug': slug} 
    return render(request, 'courses/course_detail.html', context)
   



