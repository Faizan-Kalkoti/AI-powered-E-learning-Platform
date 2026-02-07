from progress.models import TestFeedback, RevisionSections, TestResults
from courses.models import Course, Course_members
from sections.models import Available_sections, Section, Section_completed
from modules.models import Module
from alltests.models import CompletedModules, TestResultsDetail, LevelsAvailable

# For Gen Ai gemini model 
from datetime import date
from collections import Counter
from django.db.models import Count
import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown
import misaka

from envfile import GOOGLE_API_KEY 


# 1. Generate Feedback
def GenerateFeedback(curr_student, course, result_status, right_ans, wrong_ans, wrong_answer_questions, result_record):
    wrgsec_str =""
    wrglist_str =""
    for a in wrong_answer_questions:
        wrgsec_str = wrgsec_str + a.section.section_name+", "
        wrglist_str = wrglist_str + a.question.question + ", "

    # For feedback from api
    input_prompt_str = f""" For student {curr_student} Result of the test: {result_status}, marks: {right_ans} out of 20 questions and {wrong_ans} wrong answers.  
    for the course: {course.course_name}, sections name: {wrgsec_str} and the questions that were wrong are: {wrglist_str}
    for this first generate a Feedback to guide student to improve in these topics and then tell 
    them which materials to study eg. book name or websites like w3schools, Wikipedia etc.. and how much 
    time to spend on which topic that will help them 
    get better at these topics for this course, After this given below output format:

    Topics to focus on :
    1. topic name1.. [time required in hrs and mins]
    2. topic name2.. [time required in hrs and mins]
    ...etc
    
    The resources to study from:
    topics name: book names or some video's or playlist
    ....etc
    """ 
    feedback_response =""

    try:
      print(input_prompt_str)
      print("input prompt is also correct")

      genai.configure(api_key = GOOGLE_API_KEY)
      print("configured correctly")
      model = genai.GenerativeModel('gemini-pro')
      print("model goes correctly")
    
      response = model.generate_content(input_prompt_str)
      print("this is the respose \n ", response.prompt_feedback)
      feedback_response = ""
      feedback_response = feedback_response + response.text
    except Exception as e:
        feedback_response = "No feedback.. We are facing some problem in generating feedback!"
    
    # To store feedback in db model
    try:
        # Store a feedback in the model (either create or update)
        if not TestFeedback.objects.filter(student = curr_student, course=course).exists():
            TestFeedback.objects.create(student=curr_student, course=course,
                testname=result_record, feedback=feedback_response)
        else:
            feedback1 = TestFeedback.objects.get(student = curr_student, course=course) 
            feedback1.testname=result_record 
            if feedback_response=="" or feedback_response=="No feedback.. We are facing some problem in generating feedback!":
                print("No feedback")
            else:
                feedback1.feedback=feedback_response
                feedback1.feedback_date = date.today()
            feedback1.save()
    except Exception as e:
        print("Exception while storing feedback to feedback model: " +str(e))  

    # To show in html format
    renderer = misaka.HtmlRenderer()
    md = misaka.Markdown(renderer)
    # Parse the Markdown text and render it as HTML
    feedback_response_html = md(feedback_response)
    return feedback_response_html





# 2. Revision section recommendation
def FindAndStoreRevisionSection(student1, course1, wrong_answer_questions):
    revision_section = None
    wrong_answer_list = []
    count =0
    # try:
    section_list = wrong_answer_questions.annotate(section_count=Count('section')).order_by('-section_count')
    revision_section =  section_list.first().section

    if revision_section is not None:
        for rec in wrong_answer_questions:
            if rec.section == revision_section:
                count+=1
    else:
        count = 0
    
    print("revision section: ", revision_section.section_name, "and count - ", count)
    if count>=4:
        if revision_section is not None:
            if not RevisionSections.objects.filter(student=student1, course=course1).exists():
                RevisionSections.objects.create(student=student1, course=course1, section=revision_section)
            else:
                rev_sec = RevisionSections.objects.filter(student=student1, course=course1)
                rev_sec.delete()
                RevisionSections.objects.create(student=student1, course=course1, section=revision_section)

            if CompletedModules.objects.filter(student=student1, course_belongs=course1, in_section=revision_section).exists():
                delete_rec = CompletedModules.objects.filter(student=student1, course_belongs=course1, in_section=revision_section)
                delete_rec.delete()
            if Section_completed.objects.filter(student=student1, section=revision_section).exists():
                delete_rec_sec = Section_completed.objects.filter(student=student1, section=revision_section, course=course1)
                delete_rec_sec.delete()
    else:
        revision_section = None
        
    # except Exception as e: 
    #     print("Exception while processing the revision section" + str(e))

    return revision_section



#  3. to return the level to be made available now (in this test, if any)
def MakeLevelsAvailable(student1, course, testtype):
    level_available = None
    level_unlocked = None
    if LevelsAvailable.objects.filter(student = student1, course=course).exists():
        level_available = LevelsAvailable.objects.filter(student = student1, course=course)
        available_levels_count = level_available.count()
        
        if testtype=='levelup':
            if available_levels_count==1:
                level_unlocked = 'Medium'
            elif available_levels_count==2:
                level_unlocked = 'Hard'
            elif available_levels_count==3:
                level_unlocked = 'Expert'
            elif available_levels_count==4:
                level_unlocked = 'completecourse'
            else:
                level_unlocked = None
        else:
            level_unlocked = None

        if level_unlocked != None:
            if not LevelsAvailable.objects.filter(student=student1, course=course,level=level_unlocked).exists():
                LevelsAvailable.objects.create(student=student1, course=course, level=level_unlocked)
            else:
                print("Record with this level already exists!")
        else:
            print("level unlocked is null!")

            print("test type in method: MakeLevelsAvailable() -  ", testtype)
            print("level unlocked that we will be using :", level_unlocked)

    return level_unlocked

