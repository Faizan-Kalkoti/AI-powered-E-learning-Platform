from celery import shared_task
from schedulerapp.models import DailyModulesCompleted
from accounts.models import Student
from courses.models import Course
from progress.models import CompletedModules
from modules.models import Module

import datetime
from django.db import IntegrityError
from schedulerapp.weekly_functions import CalculateAverageModulesPerDay, GeneratePeriodicTests

# @shared_task(bind=True)

@shared_task
def daily_task():

    # Daily Scheduler for each student
    total_modules_completed = None
    student_list = None
    course_list = None
    todays_modules = 0
    prev = None
    course_completed = False

    try:
        student_list = Student.objects.all()
        for curr_student in student_list:
            course_list = Course.objects.filter(student=curr_student)
            if course_list.exists():
                for curr_course in course_list:

                    # check if the course is completed and record is updated in this model
                    if DailyModulesCompleted.objects.filter(student=curr_student, course=curr_course).exists():
                        last_rec = DailyModulesCompleted.objects.filter(student=curr_student, course=curr_course).order_by('-date').first()
                        total_modules_in_course = Module.objects.filter(belong_to_course=curr_course).count()
                        if last_rec.total_modules_completed_till_yesterday == total_modules_in_course:
                            course_completed = True

                    # If course is not completed then perform the following operations
                    if course_completed == False:
                        if CompletedModules.objects.filter(course_belongs=curr_course, student=curr_student).exists():
                            total_modules_completed = CompletedModules.objects.filter(course_belongs=curr_course, student=curr_student).count()
                        else:
                            total_modules_completed = 0

                        # if today is the first day of the course
                        try: 
                            if not DailyModulesCompleted.objects.filter(student=curr_student, course=curr_course).exists():
                                DailyModulesCompleted.objects.create(student=curr_student, course=curr_course, daily_modules_completed=total_modules_completed, 
                                                                    total_modules_completed_till_yesterday=total_modules_completed)
                                todays_modules = total_modules_completed
                            else:
                                prev = DailyModulesCompleted.objects.filter(student=curr_student, course=curr_course).order_by('-date').first()
                                todays_modules = total_modules_completed - (prev.total_modules_completed_till_yesterday)

                                # If today we completed any module
                                if todays_modules <=0:
                                    DailyModulesCompleted.objects.create(student=curr_student, course=curr_course, daily_modules_completed=0, 
                                                                        total_modules_completed_till_yesterday=prev.total_modules_completed_till_yesterday)
                                else:
                                    DailyModulesCompleted.objects.create(student=curr_student, course=curr_course, daily_modules_completed=todays_modules,
                                                                        total_modules_completed_till_yesterday= todays_modules+ prev.total_modules_completed_till_yesterday)
                        except IntegrityError:
                            print("integrity error occured! More then one record inserted per day!")      
                        print(f"student: {curr_student} has {curr_course} completed - {todays_modules} modules")

                    course_completed = False
                    # End of loop
            print("---")

    except Exception as e:
        print("An exception occured in daily_task - ", str(e))

    return "Done"


@shared_task
def weekly_task():
    
    print("This is weekly task executing!")

    curr_course = None
    curr_student = None
    course_list = None

    student_list = Student.objects.all()
    for curr_student in student_list:
        course_list = Course.objects.filter(student=curr_student)
        if course_list.exists():
            for curr_course in course_list:
                try:
                    # For calculating the average modules per week..
                    CalculateAverageModulesPerDay(curr_student, curr_course)
                except Exception as e:
                    print("Exception in Average MOdules Calculation function!" + str(e))

                try:
                    # To generate periodic tests
                    GeneratePeriodicTests(curr_student, curr_course)
                except Exception as e:
                    print(f"Exception in Generating Periodic test function: {e}")

    return "Weekly Task Done"




        
    # 2. To discard periodic tests (that have been unattempted - next week after updating status in db table)
    # 3. To calculate the weekly average in "WeeklyCalculatedDailyModulesCompleted" model
    # 4. To calculate The deadline and update it for those whose weekly data is present
    # 5. Handle edge cases, where for: -
    #    - 1 week no modules have been completed
    #    - The person has just joined the course (not even one week has passed)
    