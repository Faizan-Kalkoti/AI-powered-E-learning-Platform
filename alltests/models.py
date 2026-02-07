from django.db import models
from accounts.models import Student, Teacher
from courses.models import Course, Course_members
from sections.models import Section, Section_completed
from modules.models import Module
from progress.models import CompletedModules, RevisionSections, TestResults
from coursetests.models import Test_space

from datetime import date


# Create your models here.

# 1. for Levels available
class LevelsAvailable(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='levels_available')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='levels_allowed')
    levels= [('Easy','Easy'), ('Medium','Medium'), ('Hard','Hard'), ('Expert','Expert')] 
    level = models.CharField(max_length=10 ,choices=levels)

    class Meta:
        unique_together = ('student', 'course', 'level')

# 2. for test results detail storage
class TestResultsDetail(models.Model):
    student =  models.ForeignKey(Student, on_delete=models.CASCADE, related_name='result_data')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='all_test_result')
    testtype = models.CharField(max_length=100, default='levelup')
    testname = models.CharField(max_length=100)
    question = models.ForeignKey(Test_space, on_delete=models.CASCADE, related_name='all_test_results')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='all_test_results')
    result_choice = [('r','r'),('w','w'),('na','na')]
    answer = models.CharField(max_length=2, choices=result_choice)
    date_given = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course', 'testname', 'date_given', 'question')


# 3. for attempted tests (to ensure it is not given again)
class AttemptedTest(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attempted_tests')
    testname = models.CharField(max_length=100)
    testtype = models.CharField(max_length=100, default='levelup')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attempted_tests')
    date_attempted = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course', 'testname', 'date_attempted')


class PeriodicTestActive(models.Model):
    student =  models.ForeignKey(Student, on_delete=models.CASCADE, related_name='periodic_tests_available')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='periodic_tests_available')
    testname = models.CharField(max_length=100)
    timegenerated = models.DateField(default=date.today)

    def __str__ (self):
        return str(f"Periodic testname: {self.testname} - for student: {self.student}")
    
    class Meta:
        unique_together = ('student', 'course', 'testname')

class MissedPeriodicTests(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='periodic_tests_missed')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='periodic_tests_missed')
    testname = models.CharField(max_length=100)
    timemissed = models.DateField(default=date.today)

    def __str__ (self):
        return str(f"Periodic test missed: {self.testname} - for student: {self.student}")
    
    class Meta:
        unique_together = ('student', 'course', 'testname')


