import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from deliverables.results_manager import ResultsManager
from ...models import Student


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('student_records', type=str, nargs='?')

    def handle(self, *args, **options):
        student_records = options["student_records"]

        file_name = settings.BASE_DIR + "/export_data/gradebook.csv"
        if student_records is None:
            results_manager = ResultsManager(False)
            student_records_averages = results_manager.get_students_records(Student.objects.all(),
                                                                            calculate_averages=False)
            student_records = student_records_averages["records"]
        else:
            file_name = settings.BASE_DIR + "/export_data/gradebook_filtered.csv"

        if not os.path.exists(settings.BASE_DIR + '/export_data'):
            os.makedirs(settings.BASE_DIR + '/export_data')
        with open(file_name, 'wb') as gradebook_file:
            writer = csv.writer(gradebook_file)

            header = ["Student Number", "Section", "Percent Grade"]

            student_records = json.loads(student_records)
            i = 0
            for record in student_records:
                if i == 0:
                    header.extend(item['label'] for item in record['overview'])
                    for component, results in record['topic_marks'].items():
                        header.extend([result['topic'] for result in results])
                    writer.writerow(header)
                    i += 1

                write_student_row(writer, record)


def write_student_row(writer, student_record):
    total = student_record['total']

    student_id = None
    section = None
    for item in student_record['personal_info']:
        if 'ID' == item[0]:
            student_id = item[1]
        elif 'Section' == item[0]:
            section = item[1]

    row = [student_id, section, total]

    for item in student_record['overview']:
        row.append(item['mark'])
    for component, results in student_record['topic_marks'].items():
        row.extend([result['grade'] for result in results])

    writer.writerow(row)
