from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views import view_task_tutor, news_create, news_update, news_delete, conversation_detail, remove_file, working_program, delete_study_plan, study_plan, add_study_plan, edit_study_plan, SignUp, load_universities, delete_profile_image
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',  views.index, name = 'home'),
    path('about', views.about, name = 'about'),
    path('create', views.create, name = 'create'),
    path('contacts', views.contacts, name = 'contacts'),
    path('contacts/delete/<int:question_id>/', views.delete_question, name='delete_question'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('signup', SignUp.as_view(), name = 'signup'),
    path('ajax/load-universities/', load_universities, name='load_universities'),
    path('get-fields/<str:role>/', views.GetFieldsView.as_view(), name='get_fields'),
    path('accounts', include('django.contrib.auth.urls')),
    path('login', views.login_view, name='login'),
    path('logout', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('create_task/', views.create_task, name='create_task'),
    path('my_tasks/', views.my_tasks, name='my_tasks'),
    path('task/tutor/<int:task_id>/', view_task_tutor, name='view_task_tutor'),
    path('task/student/<int:task_id>/', views.view_task_student, name='view_task_student'),
    path('tasks/', views.tasks, name='tasks'),
    path('edit_task/<int:task_id>/', views.edit_task, name='edit_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('task_statistics/<int:task_id>/', views.task_statistics, name='task_statistics'),
    path('tutors', views.tutors, name='tutors'),
    path('participants', views.participants, name='participants'),
    path('study_plan/', study_plan, name='study_plan'),
    path('study_plan/add/', add_study_plan, name='add_study_plan'),
    path('study_plan/edit/<int:plan_id>/', edit_study_plan, name='edit_study_plan'),
    path('my_students', views.my_students, name='my_students'),
    path('study_plan/delete/<int:plan_id>/', delete_study_plan, name='delete_study_plan'),
    path('my_team', views.my_team, name='my_team'),
    path('statistics', views.statistics, name='statistics'),
    path('messenger', views.messenger, name='messenger'),
    path('conversation/<int:user_id>/', conversation_detail, name='conversation_detail'),
    path('remove_file/<int:message_id>/', remove_file, name='remove_file'),
    path('working_program', working_program, name='working_program'),
    path('division', views.division, name='division'),
    path('news/', views.news, name='news'),
    path('news/create/', news_create, name='news_create'),
    path('news/update/<int:pk>/', news_update, name='news_update'),
    path('news/delete/<int:pk>/', news_delete, name='news_delete'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('assign_tutors/', views.assign_tutors, name='assign_tutors'),
    path('confirm_assignment/', views.confirm_assignment, name='confirm_assignment'),
    path('delete_profile_image/', delete_profile_image, name='delete_profile_image'),
    path('export_statistics/', views.export_statistics, name='export_statistics'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
