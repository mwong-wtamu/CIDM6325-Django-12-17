from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.shortcuts import render
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
from courses.models import Course
from .forms import CourseEnrollForm
from courses.models import Content


class StudentRegistrationView(CreateView):
    template_name = "students/student/registration.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("student_course_list")

    def form_valid(self, form):
        result = super().form_valid(form)
        cd = form.cleaned_data
        user = authenticate(username=cd["username"], password=cd["password1"])
        login(self.request, user)
        return result


class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data["course"]
        self.course.students.add(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("student_course_detail", args=[self.course.id])


class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "students/course/list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])


# class StudentCourseDetailView(LoginRequiredMixin, DetailView):
#     model = Course
#     template_name = "students/course/detail.html"

#     def get_queryset(self):
#         qs = super().get_queryset()
#         return qs.filter(students__in=[self.request.user])

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # get course object
#         course = self.get_object()
#         if "module_id" in self.kwargs:
#             # get current module
#             context["module"] = course.modules.get(id=self.kwargs["module_id"])
#         else:
#             # get first module
#             context["module"] = course.modules.all()[0]
#         return context


@method_decorator(never_cache, name="dispatch")
class StudentCourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "students/course/detail.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get course object
        course = self.get_object()
        if "module_id" in self.kwargs:
            # Get current module
            module = course.modules.get(id=self.kwargs["module_id"])
        else:
            # Get first module
            module = course.modules.first()

        context["module"] = module

        # Separate instructor and student content
        instructor_content = module.contents.filter(owner__groups__name="Instructors")
        # student_content = module.contents.filter(owner__in=course.students.all())
        student_content = module.contents.filter(owner=self.request.user)

        context["instructor_content"] = instructor_content
        context["student_content"] = student_content

        # Check if the user is enrolled in the course
        if self.request.user in course.students.all():
            context["can_upload"] = True
        else:
            context["can_upload"] = False

        return context


class StudentContentDetailView(LoginRequiredMixin, DetailView):
    model = Content
    template_name = "students/course/content_detail.html"

    def get_queryset(self):
        print("URL Parameters:", self.kwargs)
        # Ensure students can only view their own uploaded content
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
