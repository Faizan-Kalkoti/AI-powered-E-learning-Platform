from django.db import models
from django.core.validators import MinLengthValidator

from courses.models import Course, Course_members
from sections.models import Section
from accounts.models import Student, Teacher
from modules.models import Module_completed, Module





# 1. For course completed by students
class CourseCompleted(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='has_completed_course')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='completed_students')
    completed_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.student.name

    class Meta:
        unique_together = ("student", "course")


# 2. For Recording the deadline given by the user
class DeadlineGiven(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_deadlines')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_deadlines')
    deadline = models.DateField()
    date_started = models.DateField(auto_now_add=True)
    deadline_finished = models.BooleanField()

    def __str__(self):
        return str(self.deadline)
    
    class Meta:
        unique_together = ("student", "course")
    

# 3. For revision sections recommendation after tests
class RevisionSections(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_revision_sections')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_revision_sections')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='revision_sections')
    revision_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.section.section_name)
    
    class Meta:
        unique_together = ("student", "course" , "section")


# 4. For Modules links
class ModuleVideos(models.Model):
    id = models.AutoField(primary_key=True)
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='video_module_records')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='video_modules_course')
    module_video = models.URLField(max_length=500)
    
    def __str__(self):
        return self.module.module_name
    
# For module completion original
class CompletedModules(models.Model):
    id = models.AutoField(primary_key=True)
    complete_module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='completed')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_models')
    course_belongs = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules_completed')
    in_section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='modules_completed')
    date_completed = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.complete_module.module_name


# 5. ALL Test Results
class TestResults(models.Model):
    id = models.AutoField(primary_key=True)
    test_name = models.CharField(max_length=300)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_test_results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_test_results')
    status = models.CharField(choices=(('pass', 'pass'), ('fail', 'fail')), max_length=4)
    for_date = models.DateField(auto_now_add=True)
    score = models.IntegerField()
    total_marks = models.IntegerField(default=20)
    on_time = models.BooleanField()

    def __str__(self):
        return self.test_name


# 6. Feedback Sections
class TestFeedback(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='feedback_students')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_feedbacks')
    testname = models.ForeignKey(TestResults, on_delete=models.CASCADE, related_name='test_feedback')
    feedback = models.TextField()
    feedback_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.course.course_name
    
    class Meta:
        unique_together = ("student", "course")

# 7. For Joining Course Password
class JoinCoursePassword(models.Model):
    id = models.AutoField(primary_key=True)
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='password_for_course')
    password = models.CharField(max_length=15, validators=[MinLengthValidator(6)], unique=True)
    
    def __str__(self):
        return f"Password for course: {self.course.course_name}"
    





