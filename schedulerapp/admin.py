from django.contrib import admin
from schedulerapp.models import (DailyModulesCompleted,  DeadlineCalculated, 
                                 WeeklyCalculatedDailyModulesCompleted)



admin.site.register(WeeklyCalculatedDailyModulesCompleted)
# admin.site.register(DailyModulesCompleted)
admin.site.register(DeadlineCalculated)
# admin.site.register(PeriodicTests)
# admin.site.register(PeriodicTestQuestions)



# Register your models here.
class DailyModulesCompletedAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'date', 'daily_modules_completed', 'total_modules_completed_till_yesterday')
    search_fields = ('student__name', 'course__name')  # Adjust based on actual field names in related models
    list_filter = ('date', 'student', 'course')

admin.site.register(DailyModulesCompleted, DailyModulesCompletedAdmin)
