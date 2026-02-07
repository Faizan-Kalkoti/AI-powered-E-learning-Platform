from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin
from braces.views import SelectRelatedMixin
from django.urls import reverse
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.contrib.auth.decorators import login_required

from django.views.generic import (CreateView, RedirectView, UpdateView,
                                  ListView, DeleteView, DetailView)

# For importing model data
from courses.models import Course, Course_members
from accounts.models import Teacher, Student
from modules.models import Module, Module_completed
from coursetests.models import Startcourse
from progress.models import (DeadlineGiven,TestFeedback, RevisionSections, 
                             JoinCoursePassword, CompletedModules, CourseCompleted)
from sections.models import Section, Section_completed, Available_sections
from alltests.models import LevelsAvailable, AttemptedTest, PeriodicTestActive, MissedPeriodicTests
from schedulerapp.models import WeeklyCalculatedDailyModulesCompleted, DeadlineCalculated

# for pagination
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import HttpResponse
from datetime import datetime, time
from django.http import Http404

from IPython.display import display
from IPython.display import Markdown
import misaka

from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page
from django.core.cache import cache


# Caching in course app
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

# Celery task testing
# from schedulerapp.tasks import test_func

# For custom filters
from django import template

register = template.Library()

@register.filter(name='abs')
def abs_filter(value):
    """Returns the absolute value of the given number."""
    try:
        return abs(value)
    except (TypeError, ValueError):
        print("error")
        return value



# Create your views here.
# CourseForm (used while creating the course)
# UpdateForm (used while updating the course)
# 1. CreateCourse
# 2. Join Course (for students) - Custom views
# 3. Leave Course (for students) - Custom views // 'not necessary here'
# 4. Delete Course (for Teachers)
# 5. List out all the courses (made by the teacher)
# 6. Detail of a course.

class CourseForm(forms.ModelForm):
    course_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 50})
    )
    class Meta:
        model = Course
        fields = ('course_name', 'course_description', 'course_img', 'age_group')
        labels = {
            'course_name': 'Course Name',
            'course_description': 'Course Description',
            'course_img': 'Course Image',
            'age_group': 'Age Group',
        }

class UpdateForm(forms.ModelForm):
    course_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 50})
    )
    class Meta:
        model = Course
        fields = ('course_name', 'course_description', 'course_img', 'age_group', 'iscomplete')
        labels = {
            'course_name': 'Course Name',
            'course_description': 'Course Description',
            'course_img': 'Course Image',
            'age_group': 'Age Group',
            'iscomplete': 'Status',
        }


class CreateCourse(LoginRequiredMixin, CreateView):
    form_class = CourseForm
    model = Course
    template_name = 'courses/course_form.html'

    def form_valid(self, form):
        # Retrieve the logged-in user's teacher profile
        teacher_profile = self.request.user.teacher  # Assuming 'teacher' is the related name
        form.instance.made_by_teacher = self.request.user.teacher

        slug = form.instance.slug
        count = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f"{form.instance.slug}-{count}"
            count += 1
            form.instance.slug = slug
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('courses:allcourseslist')
    



class SingleCourse(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Access the slug of the current course
        context['current_course_slug'] = self.object.slug
        course1 = Course.objects.get(slug = self.object.slug)
        sections = course1.contains_sections.all()
        context['sections'] = sections
        teststatus= 'NO'

        start_course = None
        completed_sections = None

        # For deadline part
        get_deadline = None
        remaining_days = None
        total_days_str = None
        deadline_percentage = None

        # For feedback part
        course_feedback = None
        feedback_response_html = None

        # For modules part
        total_modules = Module.objects.filter(belong_to_course=course1).count()
        modules_in_course = Module.objects.filter(belong_to_course=course1)
        modules_completed = None
        modules_completed_by_student = None
        modules_completed_count = None
        module_percentage = None

        teacher1 = course1.made_by_teacher
        teacher_bio1 = teacher1.bio
        teacher_bio = teacher_bio1.replace('_',' ')

        available_levels = None
        available_levels_list = ['None', 'None', 'None', 'None']
        student_current_level = 'None'
        joincoursepwd = None
        
        # This is for getting count of sections in each levels for the course
        section_count = []

        # For Revision section part
        revision_section = None

        # For course completion
        completecourse = None
        date_completed = None
        timetakentocompletecourse = None

        # For predicted deadline
        pred_deadline = None   # For deadline predicted by ML model
        average_speed = None   # For modules per day completion 
        date_started = None

        # For periodic tests
        available_periodic_tests = None
        no_missed_periodic_test = None

        if JoinCoursePassword.objects.filter(course=course1).exists():
            joincoursepwd = JoinCoursePassword.objects.filter(course=course1).first().password
        
        if hasattr(self.request.user, 'student'):
           section_get = course1.contains_sections.filter(available_to_student=self.request.user.student)
           section_exclude = course1.contains_sections.exclude(available_to_student=self.request.user.student)
           # For completed sections
           try:
               completed_sections = Section_completed.objects.filter(student=self.request.user.student, course=course1)
               start_course = Startcourse.objects.filter(student=self.request.user.student, course=course1).first()
               get_deadline = DeadlineGiven.objects.filter(student=self.request.user.student, course=course1).first()
               course_feedback = TestFeedback.objects.filter(student = self.request.user.student, course=course1).first()
               
               if course1.completed_students.filter(student=self.request.user.student).exists():
                   completecourse = "yes"
                   date_completed = course1.completed_students.filter(student=self.request.user.student).first().completed_date
                   timetakentocompletecourse = date_completed - get_deadline.date_started
                   timetakentocompletecourse = str(timetakentocompletecourse).split(" ")[0] # To retrieve the number from string


               # For finding out the levels available to the user and displaying it as a list of elements   
               if LevelsAvailable.objects.filter(student = self.request.user.student, course=course1).exists():
                   available_levels = LevelsAvailable.objects.filter(student = self.request.user.student, course=course1)
                   for lvl in available_levels:
                       if lvl.level=='Easy':
                           available_levels_list[0] = 'Easy'
                           student_current_level = 'Easy'
                       if lvl.level=='Medium':
                           available_levels_list[1] = 'Medium'
                           student_current_level = 'Medium'
                       if lvl.level=='Hard':
                           available_levels_list[2] = 'Hard'
                           student_current_level = 'Hard'
                       if lvl.level=='Expert':
                           available_levels_list[3] = 'Expert'
                           student_current_level = 'Expert'
                           
                   if available_levels.count()==3:
                        student_current_level = 'Hard'
                   elif available_levels.count()==4:
                       student_current_level ='Expert'
                   elif available_levels.count()==2:
                       student_current_level ='Medium'
                   elif available_levels.count()==1:
                       student_current_level = 'Easy'
              
               # For finding out Modules completed by the student in a course     
               modules_completed_by_student = CompletedModules.objects.filter(student=self.request.user.student, course_belongs=course1)
               modules_completed_count = modules_completed_by_student.count()

               # for revision section    
               revision_section = RevisionSections.objects.filter(student=self.request.user.student, course=course1).first()
               try:
                  module_percentage = (modules_completed_count/total_modules) * 100
               except Exception as e:
                  print(str(e))
                  module_percentage =0
               
           except ObjectDoesNotExist:
               start_course = None
               get_deadline = None
               course_feedback = None

           # For start course    
           if start_course is not None:
               test_st = start_course.has_given
               print(start_course.has_given)
               if test_st == 'Yes':
                   teststatus = 'YES'
               else:
                   teststatus = 'NO'
           else:
               teststatus = 'NO' 
            
           #For deadline
           if get_deadline is not None: 
               deadline_datetime = datetime.combine(get_deadline.deadline, time.min)
               # remaining_days = (get_deadline.deadline - datetime.now()).days
               remaining_days = (deadline_datetime - datetime.now()).days
               total_days = get_deadline.deadline - get_deadline.date_started
               total_days_str = str(total_days)  # Convert to string
               total_days_str = total_days_str.split(" ")[0]  
               try:
                  deadline_percentage = ((int(total_days_str)-remaining_days)/int(total_days_str))*100
               except Exception as e:
                  deadline_percentage = 0
           else:
               remaining_days = None
               total_days = None
               total_days_str = None

        else:
           section_get = None
           section_exclude = None

        # For Feedback 
        if course_feedback is not None:
             # Create a Markdown parser with the desired renderer and extensions
            renderer = misaka.HtmlRenderer()
            md = misaka.Markdown(renderer)
            # Parse the Markdown text and render it as HTML
            feedback_response_html = md(course_feedback.feedback)

        # For Modules
        if total_modules is None:
            total_modules =0   
            module_percentage = '0'
        if modules_completed_count is None:
            modules_completed_count = 0
            module_percentage ='0'

        try: 
            if hasattr(self.request.user, 'student'):
                # print("entered student")
                if DeadlineGiven.objects.filter(student=self.request.user.student, course=course1).exists():
                    date_started = DeadlineGiven.objects.filter(student=self.request.user.student, course=course1).first()

                if DeadlineCalculated.objects.filter(student=self.request.user.student, course=course1).exists():
                    # print("Entered pred")
                    pred_deadline = DeadlineCalculated.objects.filter(student=self.request.user.student, course=course1).order_by('-date_generated').first()
                else:
                    pred_deadline = None
                    # print("entered none")

                if WeeklyCalculatedDailyModulesCompleted.objects.filter(student=self.request.user.student, course = course1).exists():
                    average_speed = WeeklyCalculatedDailyModulesCompleted.objects.filter(student=self.request.user.student, 
                                                                       course = course1).order_by('-date').first()
                else:
                    average_speed = None

                # For periodic tests
                if PeriodicTestActive.objects.filter(student=self.request.user.student, course=course1).exists():
                    available_periodic_tests = PeriodicTestActive.objects.filter(student=self.request.user.student, course=course1).first()

                # For missed periodic tests
                if MissedPeriodicTests.objects.filter(student=self.request.user.student, course=course1).exists():
                    no_missed_periodic_test = MissedPeriodicTests.objects.filter(student=self.request.user.student, course=course1).count()

        except Exception as e:
            print("Exception while retrieving predicted deadline and speed: "+ str(e))
            
        # For level wise filter
        easy_level = None
        medium_level = None
        hard_level = None
        expert_level = None
        try:
          easy_level = section_get.filter(Difficulty='Easy')
          medium_level = section_get.filter(Difficulty='Medium')
          hard_level = section_get.filter(Difficulty='Hard')
          expert_level = section_get.filter(Difficulty='Expert')
        except Exception as e:
            print(str(e))

        print("this is the completed sections:", completed_sections)

        


        context['SectionsComplete'] = completed_sections
        context['available_sections'] = section_get
        context['excluded_sections'] = section_exclude
        context['teststatus'] = start_course

        context['easy_available_sections'] = easy_level
        context['medium_available_sections'] = medium_level
        context['hard_available_sections'] = hard_level
        context['advanced_available_sections'] = expert_level

        context['deadline'] = get_deadline
        context['remaining_days'] = remaining_days
        context['total_days'] = total_days_str 
        context['deadline_percentage'] = deadline_percentage 

        context['feedbackobj'] = course_feedback
        context['feedbackcontent'] = feedback_response_html

        context['modulesdone']=modules_completed_count
        context['totalmodules'] = total_modules   
        context['module_completion_percentage']  = int(module_percentage)
        context['module_completed'] = modules_completed_by_student
        
        context['revisionsection'] = revision_section
        context['coursecompleted'] = completecourse
        context['coursedatecompleted'] = date_completed
        context['timetocomplete'] = timetakentocompletecourse

        # For available levels
        context['levels_available'] = available_levels
        context['available_levels_list'] = available_levels_list
        context['current_level'] = student_current_level
        context['section_counts'] = section_count
        
        context['teacher'] = teacher1
        context['teacher_bio'] = teacher_bio
        context['join_course_password'] = joincoursepwd

        print(pred_deadline)
        context['pred_deadline'] = pred_deadline
        context['student_speed'] = average_speed
        context['date_started'] = date_started
        context['periodic_tests_available'] = available_periodic_tests
        context['no_missed_periodic_tests'] = no_missed_periodic_test
 
        return context
    



class ListCourse(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    paginate_by = 4

    def get_queryset(self):
        queryset = Course.objects.all()
        # test_func.delay()
        name= self.request.GET.get('name', None)
        print(name)
        try:
           teacher1 = self.request.user.teacher
        except (ObjectDoesNotExist, AttributeError):
           teacher1 = None

        # Cache key1
        cache_key  = str(name)
        qs = cache.get(cache_key)
        
        # checks if all elements are present in the list
        if not name:
            qs = cache.get('all_courses')

        if not qs:
            if name:
                queryset = queryset.filter(course_name__contains=name)
                cache.set(cache_key, queryset, timeout=CACHE_TTL)
            else:
                cache.set('all_courses', queryset, timeout=CACHE_TTL)
            queryset = queryset.filter(iscomplete=True)
            
            print("Cache miss - Querying database - (settings cache)")
        else:
            print("Cache hit")
            queryset = qs
            queryset = qs.filter(iscomplete=True)

        # if name:
        #     queryset = queryset.filter(course_name__contains=name)
        # queryset = queryset.filter(iscomplete=True)
        return queryset



class DeleteCourse(LoginRequiredMixin, DeleteView):
    template_name = 'courses/course_delete.html'
    model = Course
    success_url = reverse_lazy('courses:allcourseslist')

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(slug = self.kwargs['slug'])
    
    def delete(self, *args, **kwargs):
        messages.success(self.request, 'Courses Deleted!')
        return super().delete(*args, **kwargs)


# View to create the password for Each course by the teacher
@login_required
def CreateCoursePassword(request, slug):
    if request.method == "POST":
        course1 = get_object_or_404(Course,slug=slug)
        if Teacher.objects.filter(user=request.user).exists():
            teacher = Teacher.objects.filter(user=request.user).first()
            if course1.made_by_teacher == teacher:
                password = request.POST.get("set-password")
                try:
                    if not JoinCoursePassword.objects.filter(course=course1).exists():
                        JoinCoursePassword.objects.create(course=course1, password=password)
                    else:
                        print("Password for this course already exists!")
                        jncrs = JoinCoursePassword.objects.filter(course=course1).first()
                        jncrs.password = password
                        jncrs.save()
                        print("Updated password!")
                except Exception as e:
                    print("exception while creating the join course password: ", str(e))
            else:
                print("Teacher did not make this course!")
        else:
            print("Not a teacher!")
    return redirect(reverse("courses:singlecourse", kwargs={"slug": slug}))


# To delete the password for the course by the teacher
@login_required
def RemovePassword(request, slug):
    course1 = get_object_or_404(Course,slug=slug)

    if Teacher.objects.filter(user=request.user).exists():
            teacher = Teacher.objects.filter(user=request.user).first()
            if course1.made_by_teacher == teacher:
                if JoinCoursePassword.objects.filter(course=course1).exists():
                    jncr = JoinCoursePassword.objects.filter(course=course1).first()
                    jncr.delete()
                else:
                    print("already done!")

    return redirect(reverse("courses:singlecourse", kwargs={"slug": slug}))


# To join the course!
@login_required
def JoinCourse(request, slug):
    course = get_object_or_404(Course,slug=slug)
    student = get_object_or_404(Student, name = request.user.username)

    if JoinCoursePassword.objects.filter(course=course).exists():
        join_record = JoinCoursePassword.objects.filter(course=course).first()

        if request.method == "POST":
            user_password = request.POST.get("course-password")
            if user_password == join_record.password:
                try:
                    Course_members.objects.create(student=student,course=course)
                    print("course joined!")
                except IntegrityError as ef:
                    messages.warning(request,("Warning, already a member of {}".format(course.course_name)))
                    print("error occured in join-course funcition -", str(ef))
                else:
                    messages.success(request,"You are now a member of the {} group.".format(course.course_name))
    else:
        try:
            Course_members.objects.create(student=student,course=course)
            print("course joined!")
        except Exception as e:
            # messages.warning(request,("Warning, already a member of {}".format(course.course_name)))
            print("error occured in join-course funcition -", str(ef))
        else:
            messages.success(request,"You are now a member of the {} group.".format(course.course_name))

    return redirect(reverse("courses:singlecourse", kwargs={"slug": slug}))


class CourseCompleted(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args: Any, **kwargs):
        return reverse("courses:singlecourse",kwargs={"slug": self.kwargs.get("slug")})
    
    def get(self, request, *args, **kwargs):
        course = get_object_or_404(Course, slug=self.kwargs.get("slug"))
        course.iscomplete = True
        course.save()
        return super().get(request, *args, **kwargs)

class Courses_of_teacher(ListView):
    model = Course
    template_name = 'auth/teacher_dashboard.html'
    context_object_name = 'courses'

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Course.objects.all()
        try:
           teacher1 = self.request.user.teacher
        except (ObjectDoesNotExist, AttributeError):
           teacher1 = None
        print(teacher1)
        queryset = queryset.filter(made_by_teacher=teacher1)
        print(queryset)
        return queryset
    


# Student Dashboard
from progress.models import CourseCompleted as CourseCompleted2
class Student_Dashboard(LoginRequiredMixin, ListView):
    model=Course
    template_name='auth/student_dashboard.html'
    context_object_name='courses'

    def get_queryset(self):
        queryset = Course.objects.all()
        queryset = queryset.filter(student=self.request.user.student)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        coursecompleted_list = []
        coursecompleted = None

        if hasattr(self.request.user, 'student'):
            if CourseCompleted2.objects.filter(student=self.request.user.student).exists():
                coursecompleted = CourseCompleted2.objects.filter(student=self.request.user.student)
                for coursy in coursecompleted:
                    coursecompleted_list.append(coursy.course)

        # context['current_course_slug'] = self.object.slug
        context["course_completed_list"] = coursecompleted_list 
        return context
    
    def post(self, request, *args, **kwargs):
        # Access form data from request.POST
        form_image = self.request.POST.get('formimage')  
        # Assuming 'formimage' is the name attribute of your file input
        # Access file data from request.FILES
        uploaded_file = self.request.FILES.get('formimage')

        if uploaded_file:
            print(f'Uploaded File Name: {uploaded_file.name}')
            # self.request.user.student.profile_photo = uploaded_file
            user_profile = Student.objects.get(user=self.request.user)
            user_profile.profile_photo = uploaded_file
            user_profile.save()
        # Return a response or redirect
        return render(request, self.template_name, {'courses': self.get_queryset()})

    

class UpdateCourse(UpdateView):
    model = Course
    form_class = UpdateForm
    template_name = 'courses/update_course.html'
    success_url = reverse_lazy('courses:allcourseslist')
    




# class LeaveCourse(LoginRequiredMixin, RedirectView):
#     def get_redirect_url(self, *args, **kwargs):
#         return reverse("courses:single",kwargs={"slug": self.kwargs.get("slug")})

#     def get(self, request, *args, **kwargs):
#         try:
#             membership = Course_members.objects.filter(user=self.request.user,
#                                                     course__slug=self.kwargs.get("slug")).get()
#         except Course_members.DoesNotExist:
#             messages.warning( self.request,
#                               "You can't leave this course because you aren't in it." )
#         else:
#             membership.delete()
#             messages.success( self.request,
#                               "You have successfully left this course." )
            
#         return super().get(request, *args, **kwargs)
