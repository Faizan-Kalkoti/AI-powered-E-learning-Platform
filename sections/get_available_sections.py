from alltests.models import LevelsAvailable
from courses.models import Course
from sections.models import Section, Available_sections

def GetAvailableSections(course1, curr_section, sectionlevel):
    coursestudentlist = course1.student.all()
    for student1 in coursestudentlist:
        if LevelsAvailable.objects.filter(course=course1, student = student1).exists():
            if sectionlevel == "Easy":
                if LevelsAvailable.objects.filter(course=course1, student = student1, level="Easy").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)
                elif LevelsAvailable.objects.filter(course=course1, student = student1, level="Medium").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)
                elif LevelsAvailable.objects.filter(course=course1, student = student1, level="Hard").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)
                elif LevelsAvailable.objects.filter(course=course1, student = student1, level="Expert").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)
                     
            elif sectionlevel == "Medium":
                if LevelsAvailable.objects.filter(course=course1, student = student1, level="Medium").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)
                elif LevelsAvailable.objects.filter(course=course1, student = student1, level="Hard").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)
                elif LevelsAvailable.objects.filter(course=course1, student = student1, level="Expert").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)

            elif sectionlevel == "Hard":
                if LevelsAvailable.objects.filter(course=course1, student = student1, level="Hard").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)
                elif LevelsAvailable.objects.filter(course=course1, student = student1, level="Expert").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)

            elif sectionlevel == "Expert":
                if LevelsAvailable.objects.filter(course=course1, student = student1, level="Expert").exists():
                     Available_sections.objects.create(section=curr_section, student=student1)