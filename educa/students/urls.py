from django.urls import path
from django.views.decorators.cache import cache_page
from . import views
from courses.views import StudentContentCreateUpdateView
from courses.views import StudentContentDeleteView


urlpatterns = [
    path(
        "register/",
        views.StudentRegistrationView.as_view(),
        name="student_registration",
    ),
    path(
        "enroll-course/",
        views.StudentEnrollCourseView.as_view(),
        name="student_enroll_course",
    ),
    path("courses/", views.StudentCourseListView.as_view(), name="student_course_list"),
    # path(
    #     "course/<pk>/",
    #     cache_page(60 * 15)(views.StudentCourseDetailView.as_view()),
    #     name="student_course_detail",
    # ),
    # path(
    #     "course/<pk>/<module_id>/",
    #     cache_page(60 * 15)(views.StudentCourseDetailView.as_view()),
    #     name="student_course_detail_module",
    # ),Now I
    path(
        "course/<pk>/",
        views.StudentCourseDetailView.as_view(),
        name="student_course_detail",
    ),
    path(
        "course/<pk>/<module_id>/",
        views.StudentCourseDetailView.as_view(),
        name="student_course_detail_module",
    ),
    path(
        "course/<pk>/<int:module_id>/content/<str:model_name>/<int:id>/delete/",
        StudentContentDeleteView.as_view(),
        name="student_content_delete",
    ),
    path(
        "course/<pk>/<int:module_id>/content/<str:model_name>/create/",
        StudentContentCreateUpdateView.as_view(),
        name="student_content_create",
    ),
    path(
        "students/module/<int:module_id>/content/<int:pk>/",
        views.StudentContentDetailView.as_view(),
        name="student_content_detail",
    ),
]
