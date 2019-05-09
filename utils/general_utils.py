import decimal
import json
from datetime import datetime

import pytz

from dashboard.models import PushGradeRecord


def get_date_grades_released():
    date_released = PushGradeRecord.objects.all()
    date_released = date_released[0].last_pushed if len(date_released) > 0 else None

    if date_released is None:
        return ''
    else:
        return format_date(date_released)


def format_date(date, convert_to_pst=False):
    if convert_to_pst:
        pst = pytz.timezone("US/Pacific")
        date = datetime.astimezone(date, pst)
    return datetime.strftime(date, '%Y-%m-%d %H:%M:%S')


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)
