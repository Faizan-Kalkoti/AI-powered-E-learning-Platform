from django.contrib import admin
from alltests.models import AttemptedTest, TestResultsDetail
from alltests.models import LevelsAvailable, PeriodicTestActive, MissedPeriodicTests


# Register your models here.
admin.site.register(AttemptedTest)
admin.site.register(TestResultsDetail)
admin.site.register(LevelsAvailable)
admin.site.register(PeriodicTestActive)
admin.site.register(MissedPeriodicTests)