from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404


from django.db import IntegrityError
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from accounts.models import Student, Teacher
from courses.models import Course, Course_members
from sections.models import Section, Available_sections, Section_completed
from modules.models import Module, Module_completed
from progress.models import ModuleVideos, CompletedModules, RevisionSections

from django.views.generic import CreateView, DetailView, UpdateView, DeleteView


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields =('module_name', 'module_content', 'module_image', 'module_video')
        label ={
            'module_name' : 'Name of The Lesson',
            'module_content' : 'Content of the Lesson',
            'module_image' : 'Add Image',
            'module_video': 'Add Video',
        }

class ModuleVideosForm(forms.ModelForm):
    class Meta:
        model = ModuleVideos
        fields = ['module_video']



# 1. CreateModule
class CreateModule(LoginRequiredMixin, CreateView):
    template_name = 'modules/create_modules.html'
    model = Module
    form_class = ModuleForm

    context_object_name = 'module'

    def form_valid(self, form):
        course_slug = self.kwargs.get('course_slug')
        section_slug = self.kwargs.get('section_slug')
        module_created = ModuleForm(self.request.POST)
        module_videos_form = ModuleVideosForm(self.request.POST)
        if course_slug:
             try:
                 course1 = Course.objects.get(slug=course_slug)
                 section1 = Section.objects.get(slug =section_slug)
                 form.instance.belong_to_course = course1
                 form.instance.part_of_section = section1
             except Course.DoesNotExist:
                 return HttpResponseRedirect(reverse('courses:allcourseslist'))
        slug = form.instance.slug
        count = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f"{form.instance.slug}-{count}"
            count += 1
            form.instance.slug = slug

        form.instance.save()

        if module_videos_form.is_valid():
            module_videos = module_videos_form.save(commit=False)
            module_videos.module = form.instance
            module_videos.course = course1
            module_videos.save()
        return super().form_valid(form)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_slug = self.kwargs.get('course_slug')   
        
        if course_slug:
             try:
                 course1 = Course.objects.get(slug=course_slug)
             except Exception as e:
                 course1 = None
                 print(str(e))
                 return HttpResponseRedirect(reverse('courses:allcourseslist'))
                   
        # Add additional data to the context
        context['module_videos_form'] = ModuleVideosForm()
        context['course'] = course1
        return context
   
    def get_success_url(self):
        course_slug = self.kwargs.get('course_slug')
        return reverse('courses:singlecourse', kwargs={'slug': course_slug})
    

# Update Module Forms
class SectionForm(forms.ModelForm):
    class Meta:
      model = Section
      fields = ('section_name', 'section_description', 'Difficulty' )
      label = {
         'section_name': 'Name of the section',
         'section_description':'Description',
         'Difficulty':'Set Difficulty',
    }

# 2. UpdateModule
class UpdateModule(LoginRequiredMixin, UpdateView):
    template_name="modules/update_modules.html"
    model = Module
    fields = ['module_name', 'module_video', 'module_content', 'module_image']

    def get_success_url(self):
        course_slug = self.kwargs.get('course_slug')
        print(course_slug)
        return reverse('courses:singlecourse', kwargs={'slug': course_slug})
    

# 3. DeleteModule
class DeleteModule(LoginRequiredMixin, DeleteView):
    template_name = 'modules/delete_modules.html'
    model = Module

    def get_success_url(self):
        course_slug = self.kwargs.get('course_slug')
        print(course_slug)
        return reverse('courses:singlecourse', kwargs={'slug': course_slug})


# 4. DetailModule
class DetailModule(LoginRequiredMixin, DetailView):
    template_name = 'modules/detail_modules.html'
    context_object_name = 'module'
    model = Module
    slug_field = 'slug'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section_slug = self.kwargs.get('section_slug')
        course_slug = self.kwargs.get('course_slug')
        module_slug = self.kwargs.get('slug')

        Section1 = Section.objects.get(slug = section_slug) 
        Course1 = Course.objects.get(slug=course_slug)
        module1 = Module.objects.get(slug=module_slug)
        modules_list = None
        module_video = None
        complete_module = None
        complete_module_single = None
        try:
          module_video = ModuleVideos.objects.get(module=module1)
        except Exception as e:
          module_video = None

        if hasattr(self.request.user, 'student'):
            try:
                complete_module_single = CompletedModules.objects.filter(student=self.request.user.student, complete_module=module1)
                complete_module = CompletedModules.objects.filter(student=self.request.user.student, course_belongs= Course1)
                modules_list = Module.objects.filter(part_of_section=Section1)
            except Exception as e:
                complete_module = None
                print("Exception occured! : ", str(e))

        
        context['section'] = Section1
        context['course'] = Course1
        context['module'] = module1
        context['module_video'] = module_video
        context['modules_completed'] = complete_module
        context['single_module_completed'] = complete_module_single
        context['modules_list'] = modules_list
        return context
    

# View to complete a module 
def CompleteModule(request, module_slug):
    module1 = Module.objects.get(slug=module_slug)
    course1 = module1.belong_to_course
    section1 = module1.part_of_section
    revision_to_be_removed = None
    if hasattr(request.user, 'student'):
        student1 = Student.objects.get(id=request.user.student.id)
        if CompletedModules.objects.filter(student=student1,complete_module=module1,course_belongs=course1).exists():
            print("already completed module")
        else:
            complete_module = CompletedModules.objects.create(course_belongs=course1 ,student=student1,complete_module=module1, in_section=section1)
            print(complete_module)
        
        # check if the whole section has been completed
        complete_all_in_section =  CompletedModules.objects.filter(student=student1, course_belongs=course1, in_section=section1)
        count_modules_comp = complete_all_in_section.count()
        if count_modules_comp == section1.has_modules.count():
            if not Section_completed.objects.filter(section=section1, student=student1, course=course1).exists():
                Section_completed.objects.create(section=section1, student=student1, course=course1)
                # Check if the section completed is the revision section or not (and delete it)
                if RevisionSections.objects.filter(course=course1, student=student1, section=section1).exists():
                    revision_to_be_removed =  RevisionSections.objects.filter(course=course1, student=student1, section=section1)
                    revision_to_be_removed.delete()
            
    course_slug = module1.belong_to_course.slug
    section_slug = module1.part_of_section.slug
    slug = module1.slug
    return HttpResponseRedirect(reverse('modules:detailmodule', kwargs={'course_slug': course_slug, 'section_slug': section_slug, 'slug': slug}))


