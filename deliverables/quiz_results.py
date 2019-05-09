import decimal

from django.db import connection

from config import grade_config
from deliverables.deliverable_results import DeliverableResults
from quiz.models import WrittenSubmission, WrittenTopic, StudentRecord
from utils import topic_utils
from utils.display_utils import trim_trailing_zeroes


class QuizResults(DeliverableResults):
    topic_marks = None

    def __init__(self, student_id, pushed_grades):
        DeliverableResults.__init__(self, student_id, pushed_grades)
        self.topic_marks = self.get_marks()

    def get_records(self):
        subs = WrittenSubmission.objects.filter(student_id=self.student_id).values('student_id', 'quiz_id', 'mark',
                                                                                   'is_pass', 'responses',
                                                                                   'q_marks',
                                                                                   'date_submitted').order_by(
            'topic__ordering', 'quiz_id')
        for sub in subs:
            if len(sub['q_marks']) == 0:
                sub['q_marks'] = ''
                sub['q_marks'] = [sub['q_marks'] + '0' for x in sub['responses']]
                sub['responses'] = zip(sub['responses'], sub['q_marks'])
            sub['responses'] = zip(sub['responses'], sub['q_marks'])

        return subs

    def get_marks(self):
        if self.topic_marks is not None:
            return self.topic_marks

        quiz_topics = WrittenTopic.objects.all().order_by('ordering').values_list('name', flat=True)
        quiz_topics = [topic.lower() for topic in quiz_topics]

        grade_field = 'pushed_grade' if self.pushed_grades else 'grade'
        quiz_marks = list(
            StudentRecord.objects.filter(student_id=self.student_id, topic__in=quiz_topics).values('topic',
                                                                                                   grade_field))

        for quiz_mark in quiz_marks:
            quiz_mark['status'] = self.get_status(quiz_mark[grade_field], quiz_mark['topic'])
            quiz_mark['grade'] = trim_trailing_zeroes(quiz_mark[grade_field])

        for topic in quiz_topics:
            if topic not in [x['topic'] for x in quiz_marks]:
                quiz_marks.append({'topic': topic, 'grade': None, 'status': self.get_status(None, topic)})

        quiz_marks.sort(key=lambda (rec): quiz_topics.index((rec['topic'])))

        self.topic_marks = quiz_marks
        return quiz_marks

    def get_total_mark(self):
        quiz_total = 0
        exemptions = 0
        for quiz in self.topic_marks:
            quiz_total += decimal.Decimal(quiz['grade']) if quiz['grade'] is not None and quiz['grade'] > -1 else 0
            if quiz['grade'] == -1:
                exemptions += 1

        quiz_total = quiz_total / (WrittenTopic.objects.count() - exemptions) * self.get_worth() if \
            (WrittenTopic.objects.count() - exemptions) * self.get_worth() > 0 else 0
        return quiz_total

    def get_status(self, mark, topic=None):
        from utils.grade_record_utils import FAIL, PASS, FAIL_REQ, EXEMPT, HALF
        if mark and mark > 0.5:
            return PASS
        if mark == 0.5:
            return HALF
        if mark == -1:
            return EXEMPT
        if topic_utils.is_required_quiz(topic):
            return FAIL_REQ
        if mark is None:
            return ''
        return FAIL

    def is_missing_required(self):
        req_quizzes = topic_utils.get_required_quiz_topics()
        req_quizzes_passing = StudentRecord.objects.filter(student_id=self.student_id, topic__in=req_quizzes,
                                                           grade__gte=0.5)
        return len(req_quizzes_passing) < len(req_quizzes)

    @staticmethod
    def get_label():
        return grade_config.QUIZ_LABEL

    @staticmethod
    def get_worth():
        return grade_config.QUIZ_WORTH

    @staticmethod
    def is_required():
        return grade_config.QUIZ_REQUIRED

    """Returns list of student quiz feedback, each with topic, feedback message, and whether correct"""

    def get_student_quiz_feedback(self, pushed_feedback=False):
        table = "dashboard_studentfeedback"
        if pushed_feedback:
            table = "dashboard_pushedstudentfeedback"
        with connection.cursor() as cursor:
            cursor.execute("SELECT distinct t.name, feedback_msg, correct from " + table + " sf " +
                           "left join dashboard_feedback f on sf.feedback_id = f.id " +
                           "left join dashboard_quizfeedback qf on sf.feedback_id = qf.feedback_id " +
                           "left join quiz_writtentopic t on t.name = qf.topic_id " +
                           "where sf.student_id = '" + self.student_id + "' order by t.ordering")
            feedback = cursor.fetchall()

            return feedback

    """Returns list of student quiz feedback, grouped by topic"""

    def get_student_quiz_feedback_by_topic(self, pushed_feedback=False):
        feedback = self.get_student_quiz_feedback(pushed_feedback)
        topic_order = []
        feedback_by_topic = {}
        for f in feedback:
            topic_feedback = feedback_by_topic.get(f[0])
            if not topic_feedback:
                topic_feedback = []
                feedback_by_topic[f[0]] = topic_feedback
            entry = {'msg': f[1], 'correct': f[2]}
            topic_feedback.append(entry)
            if f[0] not in topic_order:
                topic_order.append(f[0])

        feedback_by_topic = sorted(feedback_by_topic.items(), key=lambda (k, v): topic_order.index(k))
        return feedback_by_topic
