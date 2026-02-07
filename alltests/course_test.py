from alltests.models import TestResultsDetail, LevelsAvailable
from courses.models import Course, Course_members
from progress.models import TestResults, TestFeedback, RevisionSections
from coursetests.models import Test_space
from sections.models import Section_completed
from alltests.models import PeriodicTestActive, MissedPeriodicTests

from django.db.models import Q

    

def GetTestType(course1, student_user, testname):
    testtype =  None
    if LevelsAvailable.objects.filter(student = student_user, course=course1).exists():
        level_available = LevelsAvailable.objects.filter(student = student_user, course=course1)
        available_levels_count = level_available.count()
        
        if testname=='levelup':
            if available_levels_count==1:
                testtype = 'medium_level_test'
            elif available_levels_count==2:
                testtype = 'hard_level_test'
            elif available_levels_count==3:
                testtype = 'expert_level_test'
            elif available_levels_count==4:
                testtype = 'complete_course_test'
            else:
                testtype = None

        # For checking if the test_name is 
        elif testname=='periodic_test':
            testtype ='periodic_test'
            
        elif testname=='coursecompleted':
            if available_levels_count==4:
                testtype = 'complete_course_test'
            else:
                testtype = None

        return testtype
    


def GenerateQuestionsForMediumLevelTest(mycourse):
    try:
        questions = Test_space.objects.filter(course=mycourse, level='easy').order_by('?')[:20]
        return questions
    except Exception as e:
        print("exception in MediumLevelTest function!")
        return None

def GenerateQuestionsForHardLevelTest(mycourse):
    try:
        questions = Test_space.objects.filter(Q(level='easy') | Q(level='medium'), course=mycourse).order_by('?')[:20]
        return questions
    except Exception as e:
        return None

def GenerateQuestionsForExpertLevelTest(mycourse):
    try:
        questions = Test_space.objects.filter(Q(level='easy') | Q(level='medium') | Q(level='hard'), course=mycourse).order_by('?')[:20]
        return questions
    except Exception as e:
        return None

def GenerateQuestionsForPeriodicTest(student1 ,mycourse):
    try:
        # For user progress and getting questions based on that: -
        sections_completed = None
        if Section_completed.objects.filter(student=student1, course= mycourse).exists():
            sections_completed = Section_completed.objects.filter(student=student1, course= mycourse).values_list('section_id', flat=True)
            try:
                questions = Test_space.objects.filter(section__id__in=sections_completed, course=mycourse).order_by('?')[:20]
            except Exception as e:
                print("exception in periodic test generation function - while creating questions")
                return None
        else:
            print("No sections completed!")
            return None
        
        # questions = Test_space.objects.filter(Q(level='easy') | Q(level='medium') | 
        # Q(level='hard') | Q(level='expert'), course=mycourse).order_by('?')[:20]
        return questions
    except Exception as e:
        print(f"exception occured: {str(e)}")
        return None

def GenerateQuestionsForCourseCompletionTest(mycourse):
    try:
        questions = Test_space.objects.filter(Q(level='easy') | Q(level='medium') | Q(level='hard') | Q(level='expert'), course=mycourse).order_by('?')[:20]
        return questions
    except Exception as e:
        return None