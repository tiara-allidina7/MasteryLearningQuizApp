from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.student_info, name='student_info'),
    url(r'^quiz$', views.quiz_input, name='quiz_input'),
    url(r'^handback$', views.handback, name='handback'),
    url(r'^handback/(?P<student_id>[\w\-]+)$', views.handback, name='handback'),
]
