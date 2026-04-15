from django.urls import path
from . import views

urlpatterns = [
    path('',                                  views.index,                 name='index'),
    path('register/',                         views.register_view,         name='register'),
    path('login/',                            views.login_view,            name='login'),
    path('logout/',                           views.logout_view,           name='logout'),
    path('profile/',                          views.profile_view,          name='profile'),
    path('profile/user/<int:pk>/',            views.public_profile,        name='public_profile'),
    path('talents/',                          views.talents_view,          name='talents'),
    path('leaderboard/',                      views.leaderboard_view,      name='leaderboard'),
    path('contests/',                         views.contests_view,         name='contests'),
    path('contests/add/',                     views.add_contest_view,      name='add_contest'),
    path('contests/<int:pk>/apply/',          views.apply_contest,         name='apply_contest'),
    path('mentor/request/<int:pk>/',          views.send_mentor_request,   name='mentor_request'),
    path('mentor/<int:req_id>/<str:action>/', views.handle_mentor_request, name='mentor_handle'),
    path('messages/',                         views.inbox_view,            name='inbox'),
    path('messages/<int:pk>/',                views.conversation_view,     name='conversation'),
    path('notifications/',                    views.notifications_view,    name='notifications'),
    path('resources/',                        views.resources_view,        name='resources'),
    path('jobs/',                             views.jobs_view,             name='jobs'),
    path('search/',                           views.search_view,           name='search'),
    path('courses/',                          views.courses_view,          name='courses'),
    path('courses/<int:pk>/',                 views.course_detail,         name='course_detail'),
    path('courses/<int:pk>/enroll/',          views.course_enroll,         name='course_enroll'),
    path('courses/lesson/<int:pk>/done/',     views.lesson_done,           name='lesson_done'),
    path('certificate/<str:cert_number>/',    views.certificate_view,      name='certificate_view'),
]
