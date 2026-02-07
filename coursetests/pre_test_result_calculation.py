from accounts.models import Student
from progress.models import RevisionSections, TestResults, TestFeedback
from coursetests.models import Pretest_result, Test_space, Startcourse
from sections.models import Section_completed, Available_sections
from progress.models import CompletedModules


from collections import Counter


def FindAndStoreRevisionSections(current_student, mycourse):
    pre_test_result  = Pretest_result.objects.filter(student=current_student)
    wrong_answer_list = None
    wrong_answer_sections = []
    most_common_section = None

    try:
        wrong_answer_list = pre_test_result.filter(answer='Wrong')
        for w in wrong_answer_list:
            wrong_answer_sections.append(w.question.section) 
        print(wrong_answer_sections)

        try:

            section_counts = Counter(wrong_answer_sections)
            # Find the most common section object and its count
            most_common_section, count = section_counts.most_common(1)[0]

            print(most_common_section)
            print(count)
            
        except Exception as e:
            print("an exception occured and we could not get the revision sections", str(e))
    except Exception as e:
        print("exception occurred while fetching wrong_answer_list", str(e))

    # To store this in the revision table
    try:
        if count>=4:
            if not RevisionSections.objects.filter(student=current_student, course=mycourse, section=most_common_section).exists():
               RevisionSections.objects.create(student=current_student, course=mycourse, section=most_common_section)
               
               # this will come to use with other tests for other levels   
               if CompletedModules.objects.filter(student=current_student, course_belongs=mycourse, in_section=most_common_section).exists():
                     CompletedModules.objects.filter(student=current_student, course_belongs=mycourse, in_section=most_common_section).delete()
               if Section_completed.objects.filter(student=current_student, course=mycourse, section=most_common_section).exists():
                   Section_completed.objects.filter(student=current_student, course=mycourse, section=most_common_section).delete()
            else: 
                print("alreay exists revision section !")
    except Exception as e:
        print("excetion occured while creating record!", str(e))