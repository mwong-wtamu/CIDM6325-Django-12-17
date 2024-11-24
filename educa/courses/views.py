from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.core.cache import cache
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.detail import DetailView
from django.db.models import Count
from django.apps import apps
from django.forms.models import modelform_factory
from django.http import HttpResponseBadRequest
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from students.forms import CourseEnrollForm
from .forms import ModuleFormSet
from .models import Course
from .models import Module, Content
from .models import Subject


class OwnerMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin:
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
    model = Course
    fields = ["subject", "title", "slug", "overview"]
    success_url = reverse_lazy("manage_course_list")


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = "courses/manage/course/form.html"


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = "courses/manage/course/list.html"
    permission_required = "courses.view_course"


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = "courses.add_course"


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = "courses.change_course"


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = "courses/manage/course/delete.html"
    permission_required = "courses.delete_course"


class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = "courses/manage/module/formset.html"
    course = None

    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)

    def dispatch(self, request, pk):
        self.course = get_object_or_404(Course, id=pk, owner=request.user)
        return super().dispatch(request, pk)

    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({"course": self.course, "formset": formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect("manage_course_list")
        return self.render_to_response({"course": self.course, "formset": formset})


class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = "courses/manage/content/form.html"

    def get_model(self, model_name):
        if model_name in ["text", "video", "image", "file"]:
            return apps.get_model(app_label="courses", model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(
            model, exclude=["owner", "order", "created", "updated"]
        )
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(
            Module, id=module_id, course__owner=request.user
        )
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)
        return super().dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({"form": form, "object": self.obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(
            self.model, instance=self.obj, data=request.POST, files=request.FILES
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # new content
                Content.objects.create(module=self.module, item=obj, owner=request.user)
            return redirect("module_content_list", self.module.id)
        return self.render_to_response({"form": form, "object": self.obj})


class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Content, id=id, module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect("module_content_list", module.id)


class ModuleContentListView(TemplateResponseMixin, View):
    template_name = "courses/manage/module/content_list.html"

    # def get(self, request, module_id):
    #     module = get_object_or_404(Module, id=module_id, course__owner=request.user)
    #     return self.render_to_response({"module": module})

    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id)

        course = module.course  # Retrieve the course related to the module

        # Separate instructor and student content
        instructor_content = module.contents.filter(
            owner=course.owner
        )  # Owner of the course is the instructor
        student_content = module.contents.filter(
            owner__in=course.students.all()
        )  # Enrolled students' content

        return self.render_to_response(
            {
                "module": module,
                "instructor_content": instructor_content,
                "student_content": student_content,
            }
        )


class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(id=id, course__owner=request.user).update(order=order)
        return self.render_json_response({"saved": "OK"})


class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id, module__course__owner=request.user).update(
                order=order
            )
        return self.render_json_response({"saved": "OK"})


class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = "courses/course/list.html"

    def get(self, request, subject=None):
        subjects = cache.get("all_subjects")
        if not subjects:
            subjects = Subject.objects.annotate(total_courses=Count("courses"))
            cache.set("all_subjects", subjects)
        all_courses = Course.objects.annotate(total_modules=Count("modules"))
        if subject:
            subject = get_object_or_404(Subject, slug=subject)
            key = f"subject_{subject.id}_courses"
            courses = cache.get(key)
            if not courses:
                courses = all_courses.filter(subject=subject)
                cache.set(key, courses)
        else:
            courses = cache.get("all_courses")
            if not courses:
                courses = all_courses
                cache.set("all_courses", courses)
        return self.render_to_response(
            {"subjects": subjects, "subject": subject, "courses": courses}
        )


class CourseDetailView(DetailView):
    model = Course
    template_name = "courses/course/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["enroll_form"] = CourseEnrollForm(initial={"course": self.object})
        return context


# Content creation and update view for students
class StudentContentCreateUpdateView(LoginRequiredMixin, TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = "courses/manage/content/form.html"

    def get_model(self, model_name):
        """Retrieve model based on the type of content."""
        if model_name in ["text", "video", "image", "file"]:
            return apps.get_model(app_label="courses", model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        """Generate a form dynamically based on the model."""
        Form = modelform_factory(
            model, exclude=["owner", "order", "created", "updated"]
        )

        form = Form(*args, **kwargs)

        # Make content and file optional for the 'text' model
        if model._meta.model_name == "text":
            form.fields["content"].required = False
            form.fields["file"].required = False

            # Remove 'required' attribute in the HTML
            form.fields["content"].widget.attrs["required"] = False
            form.fields["file"].widget.attrs["required"] = False

        return form

    def dispatch(self, request, module_id, model_name, id=None):
        """
        Handle the request and ensure students can only manage their content.
        """
        # Retrieve the module
        self.module = get_object_or_404(Module, id=module_id)

        # Check if the user is enrolled in the course
        if request.user not in self.module.course.students.all():
            return redirect("student_course_list")  # Redirect if not enrolled

        # Retrieve the model for the content type
        self.model = self.get_model(model_name)

        # Check ownership if editing existing content
        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)

        # Proceed with the usual dispatch
        return super().dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        """Handle GET requests to display the form."""
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({"form": form, "object": self.obj})

    def post(self, request, module_id, model_name, id=None):
        """Handle POST requests to save the form."""
        form = self.get_form(
            self.model, instance=self.obj, data=request.POST, files=request.FILES
        )

        if model_name == "file":
            uploaded_file = request.FILES.get("file")
            if uploaded_file and not uploaded_file.name.endswith(".pdf"):
                return HttpResponseBadRequest("Only PDF files are allowed.")

        if model_name == "image":
            uploaded_image = request.FILES.get("image")
            if uploaded_image and not uploaded_image.name.lower().endswith(".png"):
                return HttpResponseBadRequest("Only PNG images are allowed.")

        if model_name == "video":
            uploaded_file = request.FILES.get("file")
            video_url = request.POST.get("url")

            # Validate YouTube URL
            if video_url and not video_url.startswith(
                ("http://www.youtube.com", "https://www.youtube.com")
            ):
                return HttpResponseBadRequest("Only YouTube links are allowed.")

            # Validate MP4 file
            if uploaded_file and not uploaded_file.name.lower().endswith(".mp4"):
                return HttpResponseBadRequest(
                    "Only MP4 files are allowed for video uploads."
                )

            # Ensure at least one is provided
            if not video_url and not uploaded_file:
                return HttpResponseBadRequest(
                    "You must provide either a YouTube URL or an MP4 file."
                )

        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user  # Assign the owner as the current student
            obj.save()
            if not id:
                # Create a new content entry
                Content.objects.create(module=self.module, item=obj, owner=request.user)
            # Redirect to the correct student view after saving
            return redirect(
                "student_course_detail_module",
                pk=self.module.course.id,
                module_id=self.module.id,
            )
        return self.render_to_response({"form": form, "object": self.obj})


class StudentContentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, module_id, model_name, id):
        # Your existing code here

        """
        Allow students to delete their own content.
        """

        # Get the model based on the content type
        model = apps.get_model(app_label="courses", model_name=model_name)
        # Retrieve the object to delete
        content = get_object_or_404(model, id=id, owner=request.user)
        # Delete the object
        content.delete()
        # Redirect to the student course detail view
        return redirect(
            "student_course_detail_module", pk=request.user.id, module_id=module_id
        )


class InstructorContentDetailView(LoginRequiredMixin, DetailView):
    model = Content
    template_name = "courses/manage/module/content_detail.html"

    def get_object(self, queryset=None):
        # Override to use 'id' instead of 'pk'
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs["id"])

    def get_queryset(self):

        print("URL Parameters:", self.kwargs)
        queryset = Content.objects.filter(
            # module__course__id=self.kwargs["pk"],  # Course ID
            # module__id=self.kwargs["module_id"],  # Module ID
            # id=self.kwargs["id"],  # Content ID
            module__course__owner=self.request.user,  # Course owned by the professor
        )
        print("Filtered Queryset for InstructorContentDetailView:", queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the content item to the context
        print("Context Object:", self.object)
        context["item"] = self.object.item
        return context
