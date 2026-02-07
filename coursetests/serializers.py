from rest_framework import serializers
from .models import Test_space
from courses.models import Course
from accounts.models import Teacher
from sections.models import Section

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

class TestSpaceSerializer(serializers.ModelSerializer):
    course = CourseSerializer()
    section = SectionSerializer()
    teacher = TeacherSerializer()

    class Meta:
        model = Test_space
        fields = '__all__'