from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.main, name='dash_main'),
    url(r'^topic_results_summary/', views.topic_results_summary, name='topic_results_summary'),
    url(r'^quiz_grade_counts/', views.quiz_grade_counts, name='quiz_grade_counts'),
    url(r'^answer_log/', views.answer_log, name='answer_log'),
    url(r'^results/', views.results, name='results'),
    url(r'^results_student/', views.results_student, name='results_student'),
    url(r'^quiz_analysis/', views.quiz_analysis, name='quiz_analysis'),
    url(r'^feedback_tally/', views.feedback_tally, name='feedback_tally'),
    url(r'^quiz_file/(?P<quiz_id>[\w\-]+)/(?P<student_id>[\w\-]+)$', views.quiz_file, name='quiz_file'),
    url(r'^comment/', views.comment, name='comment'),
    url(r'^missing_quiz/', views.missing_required_quiz, name='missing_required_quiz'),
    url(r'^update_grades/', views.main, name='update_grades'),
    url(r'^push_grades/', views.main, name='push_grades'),
    url(r'^amendments/', views.amendments, name='amendments'),
    url(r'^analytics/', views.analytics, name='analytics'),
    url(r'^import_rubric_feedback/', views.main, name='import_rubric_feedback')
]
