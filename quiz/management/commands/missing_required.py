import csv

from django.core.management.base import BaseCommand
from django.db import connection

from config import grade_config


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('include_topics', type=str, nargs='?')

    def handle(self, *args, **options):
        missing_required_element(grade_config.REQUIRED_QUIZZES, 'export_data/missing_required_quiz.csv',
                                 options['include_topics'] == 'topics')


def missing_required_element(elements, file_name, include_topics):
    if include_topics:
        students_missing_required = {}
        with connection.cursor() as cursor:
            for element in elements:
                cursor.execute(
                    "Select id, first_name, last_name from quiz_student where " + element + " =0 or " + element + " is null")
                students = cursor.fetchall()
                for student in students:
                    student_record = students_missing_required.get(student[0])
                    if not student_record:
                        student_missing = []
                        student_record = {'missing': student_missing, 'first_name': student[1], 'last_name': student[2]}
                        students_missing_required[student[0]] = student_record
                        student_record['missing'].append(element)

            with open(file_name, 'wb') as file:
                writer = csv.writer(file)
                writer.writerow(['Email', 'First Name', 'Last Name', 'Topics'])
                for student_id, student_record in students_missing_required.items():
                    writer.writerow([student_id, student_record['first_name'], student_record['last_name'],
                                     student_record['missing']])

    else:
        with connection.cursor() as cursor:
            students = set()
            for element in elements:
                cursor.execute(
                    "Select distinct(id), first_name, last_name from quiz_student where " + element + " =0 or " + element + " is null")
                result = cursor.fetchall()
                students.update(set(result))

            with open(file_name, 'wb') as file:
                writer = csv.writer(file)
                writer.writerow(['Student ID', 'First Name', 'Last Name'])
                for student in students:
                    writer.writerow([student[0], student[1], student[2]])
