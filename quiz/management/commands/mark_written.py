from django.core.management.base import BaseCommand
from django.db import transaction, connection

from dashboard.models import QuizFeedback, GradeAmendment
from ...models import WrittenSubmission, AnswerKey, StudentRecord

submissions = []
students = {}
mark_all = True


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('mark_all', type=str)

    def handle(self, *args, **options):
        mark_all = options['mark_all'] != 'n'
        if mark_all:
            submissions = WrittenSubmission.objects.filter()
            connection.cursor().execute("DELETE FROM dashboard_studentfeedback")
            connection.cursor().execute("DELETE FROM quiz_amendment")
        else:
            submissions = WrittenSubmission.objects.filter(is_pass=None)

        print "- " + str(len(submissions)) + ' written submissions to mark'

        answer_keys = {x.quiz_id: x for x in AnswerKey.objects.all()}

        for sub in submissions:
            answer_key = answer_keys.get(sub.quiz_id)
            if answer_key:
                mark(answer_key.answers, answer_key.passing_mark, answer_key.worth, sub)

        save_submissions()
        update_feedback()

        apply_amendments()


def mark(answers, passing_mark, worth, sub):
    responses = sub.responses
    q_marks = ''
    num_marks = 0
    length = len(answers)
    while len(responses) < length:
        responses = responses + "0"
    for i in range(length):
        mark = 0
        if answers[i] == 'x' or answers[i] == responses[i]:
            mark = 1
        q_marks = q_marks + str(mark)
        num_marks = num_marks + mark

    sub.q_marks = q_marks
    sub.mark = num_marks
    sub.is_pass = num_marks >= passing_mark
    submissions.append(sub)

    # update student record
    if sub.is_pass:
        grade = worth
    else:
        grade = 0
    student = students.get(sub.student_id)
    if not student:
        student = {}

    current_grade = student.get(sub.topic.name.lower())

    if current_grade is None or current_grade < grade:
        student[sub.topic.name.lower()] = grade
    students[sub.student_id] = student


def update_feedback():
    student_feedbacks = []

    quiz_feedbacks = {}
    for sub in submissions:
        quiz_feedback = quiz_feedbacks.get(sub.quiz_id)
        if not quiz_feedback:
            quiz_feedback = QuizFeedback.objects.filter(quiz_id=sub.quiz_id).values_list('feedback_id',
                                                                                         flat=True).order_by(
                'question_num')
            quiz_feedbacks[sub.quiz_id] = quiz_feedback

        stud_quiz_feedback = {}
        for mark, fb in zip(sub.q_marks, quiz_feedback):
            if mark == '0':
                stud_quiz_feedback[fb] = 0
            elif fb not in stud_quiz_feedback:
                stud_quiz_feedback[fb] = 1

        student_feedbacks.extend([[sub.student_id, fb, mark] for fb, mark in stud_quiz_feedback.items()])

    save_feedback(student_feedbacks)


@transaction.atomic()
def save_submissions():
    print "- Saving marked submissions"
    for sub in submissions:
        sub.save()

    print "- Saving student marks"
    for student_id, records in students.items():
        for topic, grade in records.items():
            try:
                student_record = StudentRecord.objects.filter(student_id=student_id, topic=topic)
                current_grade = student_record[0].grade if len(student_record) > 0 else None
                if current_grade is None or grade > current_grade:
                    StudentRecord.objects.update_or_create(student_id=student_id, topic=topic,
                                                           defaults={"grade": grade})
            except:
                continue


@transaction.atomic()
def save_feedback(student_feedbacks):
    print "- Saving student feedback"
    for fb in student_feedbacks:
        with connection.cursor() as cursor:
            result = cursor.execute(
                "UPDATE dashboard_studentfeedback set correct = " + str(fb[2]) + " where student_id = '" + fb[
                    0] + "' and feedback_id = '" + str(fb[1]) + "'")
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO dashboard_studentfeedback (student_id, feedback_id, correct) VALUES ('" + fb[
                        0] + "', " + str(fb[1]) + ", " + str(fb[2]) + ")")


def apply_amendments():
    print "- Applying amendments"
    amendments = GradeAmendment.objects.order_by('date_submitted')
    for amendment in amendments:
        StudentRecord.objects.update_or_create(student_id=amendment.student_id, topic=amendment.topic,
                                               defaults={"grade": amendment.new_grade})
