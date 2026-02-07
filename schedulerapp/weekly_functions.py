from schedulerapp.models import (DailyModulesCompleted, DeadlineCalculated,
                                 WeeklyCalculatedDailyModulesCompleted)
from accounts.models import Student
from courses.models import Course
from coursetests.models import Startcourse, Test_space
from alltests.models import PeriodicTestActive, MissedPeriodicTests, TestResults
from progress.models import DeadlineGiven, CompletedModules, CourseCompleted

from django.shortcuts import get_object_or_404
from modules.models import Module

import joblib
import pandas as pd
from datetime import date, timedelta
import math


def CalculateDeadline(curr_student, curr_course, dp, avgmc):

    # If no deadline record exist for this person
    # if not DeadlineCalculated.objects.filter(student=curr_student, course=curr_course).exists():
        print("within deadline function")
        deadline = None
        predicted_days_required = None
        deadline_model = joblib.load('deadline_model.sav')
        total_modules = None
        tmc = None
        mleft = 0


        total_modules = Module.objects.filter(belong_to_course=curr_course).count()
        tmc = CompletedModules.objects.filter(course_belongs=curr_course, student=curr_student).count()

        mleft = total_modules - tmc

        new_data = pd.DataFrame({
            "Days Passed": [dp],
            "Modules Left": [mleft],
            "Total Modules Completed": [tmc],
            "Average Modules Per Day": [avgmc]
            })
        
        predicted_days_required = deadline_model.predict(new_data)

        # Default check limit  
        if not avgmc ==0 or tmc == 0 or dp == 0:
            pred1 = math.ceil(int(mleft) /int(avgmc))
            pred2 = math.ceil(int(mleft)/ (int(tmc)/int(dp)))
            prediction = (pred1+pred2) /2

            # print("predicted: ", predicted_days_required[0])
            prediction1= round(prediction)
            # print("calculated: ", prediction1)
            prediction2 = predicted_days_required[0]

            deadlineobj = get_object_or_404(DeadlineGiven, student=curr_student, course=curr_course)
            date_started = deadlineobj.date_started
            
            if abs(prediction - prediction2) >2:
                deadline = date.today() + timedelta(days=prediction1)
            else:
                deadline = date.today() + timedelta(days=prediction2)

            # Create record after calculating
            if not DeadlineCalculated.objects.filter(student=curr_student, course=curr_course).exists():
                DeadlineCalculated.objects.create(student=curr_student, course=curr_course, deadline=deadline)
            else:
                prev_deadline = DeadlineCalculated.objects.filter(student=curr_student, course=curr_course).first()
                prev_deadline.deadline = deadline
                prev_deadline.save()
        else:
            print(f"{curr_student} - deadline not inserted because not enough data!")
        


def CalculateAverageModulesPerDay(curr_student, curr_course):
    
        # Check if the student has taken the course within a week
        try:
            if DeadlineGiven.objects.filter(student=curr_student, course = curr_course).exists():
                deadlineobj = DeadlineGiven.objects.filter(student=curr_student, course = curr_course).first()
                date_started = deadlineobj.date_started
                curr_date = date.today() 
                time_elapsed = curr_date - date_started
                print("Days passed: ", time_elapsed.days)

                # If more then a week has happened only then progress
                if int(time_elapsed.days) >= 7:
                    number_of_rec = DailyModulesCompleted.objects.filter(student=curr_student, course=curr_course).count()
                    last_rec = DailyModulesCompleted.objects.filter(student=curr_student, course=curr_course).order_by("-date").first()
                    total = last_rec.total_modules_completed_till_yesterday
                    if total == 0:
                        average =0
                    else:
                        if number_of_rec == 0:
                            average = total
                        else:
                            average = total/number_of_rec

                    # To check if there are any existing records for student-course
                    WeeklyCalculatedDailyModulesCompleted.objects.create(student=curr_student, course= curr_course,
                                                    total_avg_modules_pd = average, average_modules_pd= average)
                    # else: (not necessary)
                    print(f"For student: {curr_student} - course: {curr_course} - average: {average}") 

                    # Calculate deadline
                    # Only if the course is not completed
                    if not CourseCompleted.objects.filter(student=curr_student, course=curr_course).exists():
                        CalculateDeadline(curr_student, curr_course, int(time_elapsed.days), average)
                else:
                    print("A week did not happen from when the course was taken!") 
        except Exception as e:
            print(f"Exception occured in the loop of the function - CalculateAverageModulesPerDay - {str(e)}")




                       
def GeneratePeriodicTests(curr_student, curr_course):

    missed = None

    # If no active periodic tests for the user for the course
    if not PeriodicTestActive.objects.filter(student=curr_student, course=curr_course).exists():
        CheckPeriodictests(curr_student, curr_course)

    # If there are tests that exist even after the end of the week then 
    # move them to the Missed test and add new record to the "Periodic test active table"
    else:
        missed = PeriodicTestActive.objects.filter(student=curr_student, course=curr_course).first()    
        # updated missed test table if the periodictestactive table still  has the record
        MissedPeriodicTests.objects.create(student=curr_student, course=curr_course, testname= missed.testname)
        # Delete missed periodic tests from "perdictestsactive" table
        missed.delete()
        # call this function to check for existing records and create periodic tests
        CheckPeriodictests(curr_student, curr_course)
        




def CheckPeriodictests(curr_student, curr_course):
    curr_date = None
    date_started = None
    testresults_count = None

    missed_tests_count = None
    deadlineobj = None

    if not MissedPeriodicTests.objects.filter(student=curr_student, course=curr_course).exists():
        # If the time taken from the course taken is more than a week
      if DeadlineGiven.objects.filter(student=curr_student, course = curr_course).exists():
        curr_date = date.today()
        deadlineobj = DeadlineGiven.objects.filter(student=curr_student, course = curr_course).first()
        date_started = deadlineobj.date_started
        time_diff = curr_date - date_started
         
        if int(time_diff.days)>=7:
            if not TestResults.objects.filter(student=curr_student, course=curr_course, test_name__startswith='periodic_test').exists():
                PeriodicTestActive.objects.create(student=curr_student, course=curr_course,
                                                testname="periodic_test 1")
            else:
                testresults_count = TestResults.objects.filter(student=curr_student, course=curr_course, test_name__startswith='periodic_test').count()
                print(f"{curr_student}: test result count: - {testresults_count}")
                student_testname = "periodic_test "+str(testresults_count+1)
                PeriodicTestActive.objects.create(student=curr_student, course=curr_course,
                                                testname=student_testname)
    else:
        if not TestResults.objects.filter(student=curr_student, course=curr_course, test_name__startswith='periodic_test').exists():
            missed_tests_count = MissedPeriodicTests.objects.filter(student=curr_student, course=curr_course).count()
            student_testname = "periodic_test "+str(missed_tests_count+1)
            PeriodicTestActive.objects.create(student=curr_student, course=curr_course,
                                                testname=student_testname)
        else:
            testresults_count = TestResults.objects.filter(student=curr_student, course=curr_course, test_name__startswith='periodic_test').count()
            missed_tests_count = MissedPeriodicTests.objects.filter(student=curr_student, course=curr_course).count()
            total_count = missed_tests_count + testresults_count
            student_testname = "periodic_test "+str(total_count+1)
            print(f"{curr_student}: test result count: - {testresults_count}")
            PeriodicTestActive.objects.create(student=curr_student, course=curr_course,
                                                testname=student_testname)

