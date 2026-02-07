from django.contrib import admin
from progress.models import (DeadlineGiven, RevisionSections, ModuleVideos, JoinCoursePassword,
                            TestFeedback, TestResults, CourseCompleted, CompletedModules)



class DeadlineGivenAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'deadline', 'date_started', 'deadline_finished')
    fields = ('student', 'course', 'deadline', 'date_started', 'deadline_finished')
    search_fields = ('student__name', 'course__name')
    list_filter = ('deadline', 'deadline_finished')

# Register your models here.
# admin.site.register(DeadlineGiven)
admin.site.register(DeadlineGiven, DeadlineGivenAdmin)
admin.site.register(RevisionSections)
admin.site.register(ModuleVideos)
admin.site.register(TestFeedback)
admin.site.register(TestResults)
admin.site.register(CourseCompleted)
admin.site.register(CompletedModules)
admin.site.register(JoinCoursePassword)