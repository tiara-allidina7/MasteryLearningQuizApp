# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from collections import OrderedDict
from datetime import datetime
from threading import Thread

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone

import analytics as analytics_dash
from config import dashboard_config
from dashboard.models import UpdateGradeRecord, PushGradeRecord, GradeAmendment
from deliverables.results_manager import ResultsManager
from forms import AmendmentForm
from quiz.models import WrittenSubmission, Student, AnswerKey, StudentRecord
from utils.general_utils import DecimalEncoder
from utils.grade_record_utils import get_student_grade
from utils.topic_utils import is_valid_topic, students_missing_required


def main(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)
    if request.GET.get('mark_written'):
        pre_unmarked = len(WrittenSubmission.objects.filter(mark__isnull=True))
        call_command('mark_written')
        unmarked = len(WrittenSubmission.objects.filter(mark__isnull=True))
        return render(request, 'dashboard_main.html',
                      {'marking_msg': "Marking complete: " + str(pre_unmarked - unmarked) + " quizzes marked",
                       'unmarked': unmarked})

    if "update_grades" in request.POST:
        update_grades()
        return redirect(settings.QUIZ_HOME_URL + "dashboard/")

    if "push_grades" in request.POST:
        push_grades()
        return redirect(settings.QUIZ_HOME_URL + "dashboard/")

    if "import_rubric_feedback" in request.POST:
        import_rubric_feedback()
        return redirect(settings.QUIZ_HOME_URL + "dashboard/")

    unmarked = len(WrittenSubmission.objects.filter(mark__isnull=True))
    last_updated = UpdateGradeRecord.objects.all()
    last_updated = last_updated[0].last_updated if len(last_updated) > 0 else ""

    last_pushed = PushGradeRecord.objects.all()
    last_pushed = last_pushed[0].last_pushed if len(last_pushed) > 0 else ""
    return render(request, 'dashboard_main.html',
                  {'unmarked': unmarked, 'last_updated': last_updated, 'last_pushed': last_pushed})


def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return decorator


@start_new_thread
def update_grades():
    call_command("mark_written", "n")

    update_record = UpdateGradeRecord.objects.all()
    if len(update_record) == 0:
        UpdateGradeRecord(last_updated=datetime.now()).save()
    else:
        update_record = update_record[0]
        update_record.last_updated = datetime.now()
        update_record.save()


@start_new_thread
def push_grades():
    with connection.cursor() as cursor:
        cursor.execute("delete from dashboard_pushedstudentfeedback")
        cursor.execute("insert into dashboard_pushedstudentfeedback select * from dashboard_studentfeedback")

        cursor.execute("update quiz_studentrecord set pushed_grade = grade")

    push_record = PushGradeRecord.objects.all()
    if len(push_record) > 0:
        push_record = push_record[0]
        push_record.last_pushed = datetime.now()
    else:
        push_record = PushGradeRecord(last_pushed=datetime.now())

    push_record.save()


@start_new_thread
def import_rubric_feedback():
    call_command('import_rubric')
    call_command('import_feedback')


def topic_results_summary(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)

    num_students = Student.objects.count()

    topic_results = []
    with connection.cursor() as cursor:
        cursor.execute('SELECT name FROM quiz_writtentopic ORDER BY ordering')
        topics = cursor.fetchall()

        for topic in topics:
            topic = topic[0]
            passes = StudentRecord.objects.filter(topic=topic.lower(), grade__gte=0.5).count()
            taken = StudentRecord.objects.filter(topic=topic.lower()).count()
            fails = taken - passes
            missing = num_students - taken
            topic_result = {'topic': topic, 'pass': passes, 'fail': fails, 'missing': missing}
            topic_results.append(topic_result)

    return render(request, 'topic_results_summary.html', {'query_results': topic_results})


def quiz_grade_counts(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)

    counts_per_quiz = {}

    for i in range(6):
        subs = []
        if i < 5:
            subs = WrittenSubmission.objects.filter(mark=40 - i).values_list('quiz_id', 'topic',
                                                                             'topic__ordering').annotate(
                count=Count('id')).order_by(
                'quiz_id')
        else:
            subs = WrittenSubmission.objects.filter(mark__lte=35).values_list('quiz_id', 'topic',
                                                                              'topic__ordering').annotate(
                count=Count('id')).order_by('quiz_id')
        for sub in subs:
            quiz_id = sub[0].lower()
            quiz_counts = counts_per_quiz.get(quiz_id)
            if not quiz_counts:
                counts = [0, 0, 0, 0, 0, 0]
                quiz_counts = {}
                quiz_counts['counts'] = counts
                quiz_counts['topic'] = sub[1]
                quiz_counts['topic_order'] = sub[2]
            else:
                counts = quiz_counts['counts']
            counts[i] += sub[3]
            counts_per_quiz[quiz_id] = quiz_counts

    counts_per_quiz = OrderedDict(sorted(counts_per_quiz.items(), key=lambda (k, v): (v['topic_order'], k)))

    return render(request, 'quiz_grade_counts.html', {'counts_per_quiz': counts_per_quiz})


def answer_log(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)
    subs = WrittenSubmission.objects.values('student_id', 'quiz_id', 'mark', 'is_pass', 'responses',
                                            'q_marks').order_by('student_id')
    for sub in subs:
        if len(sub['q_marks']) == 0:
            sub['q_marks'] = ''
            sub['q_marks'] = [sub['q_marks'] + '0' for x in sub['responses']]
            sub['responses'] = zip(sub['responses'], sub['q_marks'])
        sub['responses'] = zip(sub['responses'], sub['q_marks'])
    return render(request, 'answer_log.html', {'submissions': subs})


def results(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)

    if request.GET.get('filter') and (request.GET.get("missing_required")):
        student_ids = students_missing_required()
        students = Student.objects.filter(id__in=student_ids)
    else:
        students = Student.objects.all()

    results_manager = ResultsManager(False)
    student_records_averages = results_manager.get_students_records(students, calculate_averages=True)
    student_records = student_records_averages["records"]
    averages = student_records_averages["averages"]

    if request.POST.get('download'):
        call_command("export_gradebook", json.dumps(student_records, cls=DecimalEncoder))

        file = settings.BASE_DIR + '/export_data/gradebook_filtered.csv'
        with open(file, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=gradebook-results.csv'
            return response

    return render(request, 'results.html', {'student_records': student_records, 'quiz_home': settings.QUIZ_HOME_URL,
                                            'averages': averages,
                                            'missing_required': request.GET.get("missing_required") is not None})


def results_student(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)

    if request.GET.get('student_results'):
        student_id = request.GET.get('student_id')

        student_id = student_id.strip()
        student = Student.objects.filter(id=student_id)
        if len(student) == 0:
            return render(request, 'results_student.html', {'error': "No student found with this ID"})

        info_fields = []
        info_labels = []
        for item in dashboard_config.student_fields_to_display:
            info_labels.append(item[0])
            info_fields.append(item[1])

        student_info = student.values_list(*info_fields)[0]

        student = student[0]

        results_manager = ResultsManager(False)
        student_results = results_manager.get_student_results(student.id)
        student_marks = student_results.get_full_record(student, include_personal_info=True)

        quizzes = student_results.get_quiz_results().get_records()

        # OVERVIEW
        overview = student_marks['overview']
        topic_marks = student_marks['topic_marks']

        # SECTIONS
        comment = student.comment
        if comment is not None and len(comment) == 0:
            comment = None

        feedback = student_results.get_student_quiz_feedback(student_id)

        if request.method == 'POST' and student_id:
            comment = request.POST.get('comment')
            student.comment = comment
            student.save()
            return HttpResponseRedirect('?student_id=' + student_id + '&student_results=Submit#')

        return render(request, 'results_student.html',
                      {'student_info': zip(info_labels, student_info),
                       'total': student_marks['total'],
                       'overview': overview,
                       'topic_marks': topic_marks,
                       'comment': comment,
                       'quizzes': quizzes,
                       'feedback': feedback,
                       'quiz_file_link': settings.QUIZ_HOME_URL + 'dashboard/quiz_file'})

    return render(request, 'results_student.html')


def quiz_analysis(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)
    quizzes = WrittenSubmission.objects.values('quiz_id', 'q_marks', 'mark', 'topic', 'topic__ordering').order_by(
        'topic__ordering', 'quiz_id')
    quiz_marks = {}
    for quiz in quizzes:
        if len(quiz['q_marks']) == 0:
            continue
        quiz_record = quiz_marks.get(quiz['quiz_id'])
        if quiz_record is None:
            correct_count = [0 for i in range(0, 40)]
            quiz_record = {'count': 0, 'correct': correct_count, 'mark': 0, 'topic': quiz['topic'],
                           'topic_order': quiz['topic__ordering']}
            quiz_marks[quiz['quiz_id'].lower()] = quiz_record
        quiz_record['count'] += 1
        quiz_record['mark'] += quiz['mark']
        for i in range(40):
            quiz_record['correct'][i] += \
                float(quiz['q_marks'][i])

    for quiz, records in quiz_marks.items():
        records['correct'] = [round(correct / records['count'], 2) for correct in records['correct']]
        records['mark'] = round(records['mark'] / records['count'], 2)
        passing_mark = AnswerKey.objects.filter(quiz_id=quiz).values_list('passing_mark')
        if len(passing_mark) > 0:
            records['passing_mark'] = passing_mark[0][0]

    return render(request, 'quiz_analysis.html',
                  {'quiz_records': sorted(quiz_marks.items(), key=lambda (k, v): (v['topic_order'], k))})


def feedback_tally(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)
    with connection.cursor() as cursor:
        cursor.execute('select distinct(df.feedback_msg), corr, incorr, t.name ' +
                       'from (select feedback_id, sum(correct) as corr, (count(correct)-sum(correct)) as incorr ' +
                       'from dashboard_studentfeedback group by feedback_id) as student_temp ' +
                       'left join dashboard_quizfeedback qf on student_temp.feedback_id=qf.feedback_id ' +
                       'left join dashboard_feedback df on df.id = qf.feedback_id ' +
                       'left join quiz_writtentopic t on t.name = qf.topic_id order by t.ordering;')
        results = cursor.fetchall()
    return render(request, 'feedback_tally.html', {'results': results})


def comment(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)
    if request.method == 'GET':
        student_id = request.GET.get('student_id')
        if student_id:
            try:
                student = Student.objects.get(id=student_id)
                comment = student.comment
                if not comment:
                    comment = ''
                return render(request, 'student_comment.html', {'student_id': student_id, 'comment': comment})
            except Student.DoesNotExist:
                return render(request, 'student_comment.html', {'error': 'No student found with this ID'})

    student_id = request.GET.get('student_id')
    if request.method == 'POST' and student_id:
        comment = request.POST.get('comment')
        student = Student.objects.get(id=student_id)
        student.comment = comment
        student.save()
        return render(request, 'student_comment.html', {'student_id': student_id, 'comment': comment})

    return render(request, 'student_comment.html')


def quiz_file(request, quiz_id, student_id):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)
    subs = WrittenSubmission.objects.filter(student_id=student_id, quiz_id=quiz_id).values('student_id', 'quiz_id',
                                                                                           'mark',
                                                                                           'is_pass', 'responses',
                                                                                           'q_marks',
                                                                                           'date_submitted').order_by(
        'date_submitted')
    for sub in subs:
        if len(sub['q_marks']) == 0:
            sub['q_marks'] = ''
            sub['q_marks'] = [sub['q_marks'] + '0' for x in sub['responses']]
        sub['responses'] = zip(sub['responses'], sub['q_marks'])

    return render(request, 'quiz_file.html', {'quiz_id': quiz_id, 'student_id': student_id, 'subs': subs})


def missing_required_quiz(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)
    file = settings.BASE_DIR + '/export_data/missing_required_quiz.csv'
    with open(file, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'inline; filename=missing_required_quiz.csv'
        return response


def amendments(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)

    form = AmendmentForm()
    if request.method == 'POST':
        if request.POST.get('update'):
            form = AmendmentForm(request.POST)
            if form.is_valid():
                student_id = form.cleaned_data['student'].lower()
                topic = form.cleaned_data['topic'].lower()
                new_grade = form.cleaned_data['new_grade']

                try:
                    Student.objects.get(id=student_id)
                except:
                    return render(request, 'amendments.html', {'form': form, 'error': 'No student with this ID'})

                if not is_valid_topic(topic):
                    return render(request, 'amendments.html', {'form': form, 'error': 'Invalid topic'})

                current_grade = get_student_grade(student_id, topic)

                request.session['student'] = student_id
                request.session['topic'] = topic
                request.session['new_grade'] = float(new_grade)
                request.session['current_grade'] = float(current_grade) if current_grade else 0

                return render(request, 'amendments.html',
                              {'form': form, 'student_id': student_id, 'topic': topic.upper(),
                               'current_grade': current_grade, 'new_grade': new_grade, 'confirmed': False})

        elif request.POST.get('confirm'):
            student_id = request.session.get('student')
            if not student_id:
                return HttpResponseRedirect(settings.QUIZ_HOME_URL + 'dashboard/amendments')
            topic = request.session.get('topic')
            new_grade = request.session.get('new_grade')
            current_grade = request.session.get('current_grade')

            request.session['student'] = None

            GradeAmendment(
                student_id=student_id,
                topic=topic,
                old_grade=current_grade,
                new_grade=new_grade,
                date_submitted=timezone.now()
            ).save()

            StudentRecord.objects.update_or_create(student_id=student_id, topic=topic.lower(),
                                                   defaults={"grade": new_grade})

            return render(request, 'amendments.html', {'form': form, 'student_id': student_id, 'topic': topic.upper(),
                                                       'current_grade': current_grade, 'new_grade': new_grade,
                                                       'confirmed': True})

    return render(request, 'amendments.html', {'form': form})


def analytics(request):
    if not has_access(request):
        return redirect(settings.QUIZ_HOME_URL)

    graphs = []

    total_num_students = Student.objects.count()

    with connection.cursor() as cursor:
        graphs.append(analytics_dash.weekly_failures(total_num_students))

        graphs.append(analytics_dash.topic_results(total_num_students))

        # AVG QUIZZES / STUDENT PER TOPIC
        graphs.append(analytics_dash.quizzes_per_student_by_topic(cursor, total_num_students))

        graphs.append(analytics_dash.feedback_msg_burndown())

        return render(request, 'analytics.html', {'graphs': graphs})


"""Defines which users have dashboard access"""


def has_access(request):
    return True  # For demo, all users have instructor access
