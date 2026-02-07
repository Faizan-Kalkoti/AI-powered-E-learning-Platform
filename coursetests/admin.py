from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .resources import TestSpaceResource
from . models import Test_space, Precourse_test, Pretest_result, Startcourse

class TestSpaceAdmin(ImportExportModelAdmin):
    resource_class = TestSpaceResource

    list_display = ('question', 'answer', 'level', 'course', 'section', 'teacher')
    list_filter = ('level', 'course', 'section', 'teacher')
    search_fields = ('question', 'course__name', 'section__name', 'teacher__name')

    fieldsets = (
        ('General Information', {
            'fields': ('question', 'options_a', 'options_b', 'options_c', 'options_d', 'answer', 'level')
        }),
        ('Relationships', {
            'fields': ('course', 'section', 'teacher')
        }),
    )

admin.site.register(Test_space, TestSpaceAdmin)

# admin.site.register(Test_space)
admin.site.register(Precourse_test)
admin.site.register(Pretest_result)
admin.site.register(Startcourse)

# Register your models here.
