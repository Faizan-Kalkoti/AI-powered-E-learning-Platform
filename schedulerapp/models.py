from django.db import models
from accounts.models import Teacher, Student
from courses.models import Course
from coursetests.models import Test_space
import datetime



class DailyModulesCompleted(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="daily_modules")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="daily_modules")
    date = models.DateField(default=datetime.date.today)
    daily_modules_completed = models.IntegerField(default=0)
    total_modules_completed_till_yesterday = models.IntegerField(default=0)

    def __str__(self):
        return f" mod/days = {self.daily_modules_completed} for course {self.course.course_name}. "
    
    class Meta:
        unique_together = ("student", "course", "date")


class WeeklyCalculatedDailyModulesCompleted(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="avg_daily_modules")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="avg_daily_modules")
    date = models.DateField(auto_now_add=True)
    total_avg_modules_pd = models.IntegerField(default=0)
    average_modules_pd = models.IntegerField(default=0)

    def __str__(self):
        return f"average modules per day calculated weekly by averaging  - {str(self.total_avg_modules_pd)}"
    
    class Meta:
        unique_together = ("student", "course", "date")


class DeadlineCalculated(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="deadlines")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="deadlines")
    date_generated = models.DateField(auto_now_add=True)
    deadline = models.DateField()

    def __str__(self):
        return f"deadline - {str(self.deadline)} for student {str(self.student)}"
    
    class Meta:
        unique_together = ("student", "course")










# --------------------- Not needed for now ------------------------
# 
# class PeriodicTests(models.Model):
#     id = models.AutoField(primary_key=True)
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="periodic_tests")
#     course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="periodic_tests")
#     periodic_test_number = models.IntegerField(default=1)
#     date = models.DateField(auto_now_add=True)
#     given = models.BooleanField(default=False)

#     def __str__(self):
#         return f"periodic tests no - {str(self.periodic_test_number)} for user {str(self.student)}"
    
#     class Meta:
#         unique_together = ("student", "course", "date")


# class PeriodicTestQuestions(models.Model):
#     id = models.AutoField(primary_key=True)
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="periodic_tests_questions")
#     course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="periodic_tests_questions")
#     question = models.ForeignKey(Test_space,on_delete=models.CASCADE, related_name="pre_course_question")
#     test_no = models.ForeignKey(PeriodicTests,on_delete=models.CASCADE, related_name="test_questions")
#     date = models.DateField(auto_now_add=True)

#     def __str__(self):
#         return f"Preiodic test question - {str(self.question.question)}"
    
#     class Meta:
#         unique_together = ("student", "course", "question", "test_no")

