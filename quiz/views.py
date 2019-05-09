# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

from config import dashboard_config
from deliverables.results_manager import ResultsManager
from utils.display_utils import topic_marks_to_percent_display
from utils.general_utils import get_date_grades_released
from .forms import StudentInfoForm, QuizInputForm
from .models import Student, AnswerKey, WrittenSubmission


def render_quiz(request):
    return render(request, "main.html", {})


def student_info(request):
    request.session['student_id'] = None
    request.session['topic'] = None

    if request.method == 'POST':
        form = StudentInfoForm(request.POST)

        if form.is_valid():
            student_id = form.cleaned_data['username'].lower()
            quiz_id = form.cleaned_data['quiz_id'].lower()
            ta_sign = form.cleaned_data['ta_sign']

            # check if student with this id exists
            students_with_id = Student.objects.filter(id=student_id)
            if students_with_id.count() <= 0 and dashboard_config.restrict_student_classlist:
                return render(request, 'main.html',
                              {'form': form, 'form_errors': "User " + student_id + " is not enrolled in course."})

            answer_key = AnswerKey.objects.filter(quiz_id=quiz_id)
            if answer_key.count() <= 0:  # quiz id doesn't exist
                return render(request, 'main.html', {'form': form, 'form_errors': "Invalid quiz id."})
            else:
                topic = answer_key[0].topic_id.upper()
                request.session['student_id'] = student_id
                request.session['topic'] = topic
                request.session['quiz_id'] = quiz_id
                request.session['ta_sign'] = ta_sign
                request.session['from'] = 'student_info'
                return redirect(reverse(quiz_input))
    else:
        form = StudentInfoForm()

    return render(request, 'main.html', {'form': form})


def quiz_input(request):
    student_id = request.session['student_id'].lower()
    topic = request.session['topic']

    if not student_id or not request.session.get('from'):
        return redirect(reverse(student_info))

    if request.method == 'GET':
        form = QuizInputForm()
        quiz_id = request.session['quiz_id'].lower()
        quiz_file = quiz_id + ".html"
        return render(request, 'quiz_boxes.html',
                      {'form': form, 'student_id': student_id, 'topic': topic, 'quiz_file': quiz_file})
    if request.method == 'POST':
        form = QuizInputForm(request.POST)

        if form.is_valid():
            request.session['from'] = None
            return submit_quiz(request, form)


def submit_quiz(request, form):
    session = request.session

    if not session['student_id']:
        return redirect(reverse(student_info))

    responses = ""

    form_data = form.cleaned_data
    form_data = sorted(form_data.items(), key=lambda (k, v): int(k[1:]))

    for q, a in form_data:
        answer = "0"
        if a:
            answer = "1"
        responses = responses + answer

    student_id = session['student_id'].lower()
    students_with_id = Student.objects.filter(id=student_id)
    if len(students_with_id) == 0:
        Student(
            id=student_id,
            first_name="Temp",
            last_name="Temp",
            lab="",
            section=""
        ).save()

    submission = WrittenSubmission(
        student_id=student_id,
        topic_id=session['topic'],
        date_submitted=timezone.now(),
        responses=responses,
        quiz_id=session['quiz_id'],
        taSignature=session['ta_sign'])

    submission.save()
    return render(request, 'submission.html', {'student_id': student_id})


def handback(request, student_id=None):
    date_released = get_date_grades_released()

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return render(request, 'handback.html', {'error': "No student found with this ID"})

    results_manager = ResultsManager(pushed_grades=True)
    student_results = results_manager.get_student_results(student.id)
    student_marks = student_results.get_full_record(student)

    topic_marks = student_marks['topic_marks']
    topic_marks_to_percent_display(topic_marks)

    feedback = student_results.get_student_quiz_feedback_by_topic(True)

    return render(request, 'handback.html', {'student_id': student_id,
                                             'overview': student_marks['overview'],
                                             'topic_marks': topic_marks,
                                             'total': student_marks['total'],
                                             'last_pushed': date_released,
                                             'feedback': feedback, })
