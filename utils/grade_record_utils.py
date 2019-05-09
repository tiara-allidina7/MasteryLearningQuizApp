import csv
import decimal

from django.conf import settings

from config import dashboard_config
from quiz.models import StudentRecord

PASS = "pass"
FAIL = "fail"
FAIL_REQ = "failReq"
EXEMPT = "exempt"
HALF = "half"


def get_student_grade(student_id, topic):
    student_record = StudentRecord.objects.filter(student_id=student_id, topic=topic)
    grade = student_record[0].grade if len(student_record) > 0 else None
    return grade


def get_pushed_student_grade(student_id, topic):
    student_record = StudentRecord.objects.filter(student_id=student_id, topic=topic)
    grade = student_record[0].pushed_grade if len(student_record) > 0 else None
    return grade


def get_bonuses():
    bonuses = {}
    try:
        surveys_file = open(settings.BASE_DIR + "/import_data/bonus.csv", 'rb')
        reader = csv.reader(surveys_file)
        i = 0
        for row in reader:
            if i == 0:
                i += 1
                continue
            bonuses[row[0]] = decimal.Decimal(row[1])
    except IOError:
        pass

    return bonuses


def get_personal_info(student):
    personal_info = []
    for item in dashboard_config.student_fields_to_display:
        personal_info.append((item[0], student.__getattribute__(item[1])))
    return personal_info
