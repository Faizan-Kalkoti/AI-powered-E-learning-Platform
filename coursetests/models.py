from django.db import models
from courses.models import Course
from sections.models import Section
from accounts.models import Student, Teacher


# Models we will require for scheduling tests and handling responses

# This is the base Test model 
class Test_space(models.Model):
    question = models.CharField(max_length = 250)                   #1
    options_a = models.CharField(max_length = 250)                  #2     
    options_b = models.CharField(max_length = 250)                  #3
    options_c = models.CharField(max_length = 250)                  #4
    options_d = models.CharField(max_length = 250)                  #5
   
    Answer_choices = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
        ('N', 'None') ]

    Level_it = [('easy','easy'),('meduim','medium'),
                ('hard','hard'),('expert','expert')]

    answer = models.CharField(default='N', choices = Answer_choices, max_length=200)           #6
    level = models.CharField(default = "easy", choices = Level_it, max_length=15)            #7

    course = models.ForeignKey(to=Course, on_delete = models.CASCADE)                         #8
    section = models.ForeignKey(to=Section, on_delete = models.CASCADE)                       #9
    teacher = models.ForeignKey(to=Teacher, on_delete = models.CASCADE)                       #10
    id = models.AutoField(primary_key=True)                                                   #11

    def __str__(self):
       return self.question



# Pre - Requisite Test model
# This is supposed to contain all the questions from easy and medium level 
# And given to the user when the user has started the course
class Precourse_test(models.Model):
    student = models.ForeignKey(to=Student, on_delete = models.CASCADE)
    question = models.ForeignKey(to=Test_space, on_delete = models.CASCADE, related_name="precourse_questions")
    course = models.ForeignKey(to =Course, on_delete = models.CASCADE)

    def __str__(self):
       return str(self.student)


# This is to ensure that pre-requisite test is only given at the start to make the sections available
class Startcourse(models.Model):
    student = models.ForeignKey(to=Student, on_delete =models.CASCADE)
    # pre_requisite = models.ForeignKey(to=Precourse_test, on_delete = models.CASCADE)
    course = models.ForeignKey(to=Course, on_delete = models.CASCADE, related_name = 'given_pretest')
    Test_status =[('Yes', 'YES'),('No', 'NO')]
    has_given = models.CharField(choices = Test_status, max_length = 10)

    def __str__(self):
       return self.has_given


# To record the result
class Pretest_result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(to=Test_space , on_delete=models.CASCADE, related_name = 'result')
    answer_status = [('Correct','C'),('Wrong','W')]
    answer = models.CharField(choices = answer_status, max_length = 14)

    def __str__(self):
       return str(self.student)





# # THis is the weekly test given by the user to the system 
# # To assess the users progress and learnabililty
# class Progress_test(models.Model):
#     pass
    