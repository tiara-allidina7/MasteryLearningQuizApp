from django.core.management.base import BaseCommand

from dashboard.models import GradeAmendment
from ...models import StudentRecord


class Command(BaseCommand):

    def handle(self, *args, **options):
        print "Applying amendments"
        amendments = GradeAmendment.objects.order_by('date_submitted')
        for amendment in amendments:
            topic = amendment.topic
            new_grade = amendment.new_grade
            student_id = amendment.student_id
            StudentRecord.objects.update_or_create(student_id=student_id, topic=topic, defaults={"grade": new_grade})
