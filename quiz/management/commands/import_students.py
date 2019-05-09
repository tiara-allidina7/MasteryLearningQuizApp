import csv

from django.core.management.base import BaseCommand

from ...models import Student

classlist_file = "import_data/classlist.csv"


def import_students():
    with open(classlist_file) as infile:
        csv_reader = csv.reader(infile)
        first_row = True
        for row in csv_reader:
            if first_row:
                first_row = False
            else:
                student_id = row[0]
                last_name = row[1]
                first_name = row[2]
                section = row[3]
                lab = row[4]
                Student.objects.update_or_create(
                    id=student_id, defaults={"last_name": last_name,
                                             "first_name": first_name,
                                             "section": section,
                                             "lab": lab}
                )


class Command(BaseCommand):

    def handle(self, *args, **options):
        import_students()
