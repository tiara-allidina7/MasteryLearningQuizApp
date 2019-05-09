from django.db import connection

from config import grade_config
from quiz.models import AnswerKey


def is_valid_topic(topic):
    return is_valid_quiz_topic(topic)  # Other checks can be added here if non-quiz components included


def is_valid_quiz_topic(topic):
    return len(AnswerKey.objects.filter(topic_id=topic.upper())) > 0


def get_required_topics():
    return get_required_quiz_topics()  # Other topics can be added here if non-quiz components included


def get_required_quiz_topics():
    return grade_config.REQUIRED_QUIZZES


def is_required(topic):
    return topic.lower() in get_required_topics()


def is_required_quiz(topic):
    return topic.lower() in get_required_quiz_topics()


def students_missing_required():
    required_topics = "("
    for topic in get_required_topics():
        required_topics += "'" + topic + "',"
    student_ids = []
    if len(required_topics) > 1:
        required_topics = required_topics[:-1]
        required_topics += ")"
        query = "select id from quiz_student where (select count(distinct(topic)) from quiz_studentrecord " \
                "where student_id=quiz_student.id and grade>=0.5 and topic in " + required_topics + ") " \
                                                                                                    "< " + str(
            len(get_required_topics()))

        with connection.cursor() as cursor:
            cursor.execute(query)
            student_ids = cursor.fetchall()
            student_ids = [id[0] for id in student_ids]

    return student_ids
