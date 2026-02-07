from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import Test_space
from accounts.models import Teacher 
from courses.models import Course
from sections.models import Section


class TestSpaceResource(resources.ModelResource):
    # Define a custom field for the related models (Course, Section, Teacher)
    course = fields.Field(
        column_name='course',
        attribute='course',
        widget=ForeignKeyWidget(Test_space, 'course')
    )
    section = fields.Field(
        column_name='section',
        attribute='section',
        widget=ForeignKeyWidget(Test_space, 'section')
    )
    teacher = fields.Field(
        column_name='teacher',
        attribute='teacher',
        widget=ForeignKeyWidget(Test_space, 'teacher')
    )

    class Meta:
        model = Test_space
        fields = ('id' ,'question', 'options_a', 'options_b', 'options_c', 'options_d', 'answer', 'level', 'course', 'section', 'teacher')
        