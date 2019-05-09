from deliverables.results import Results


class DeliverableResults(Results):

    def __init__(self, student_id, pushed_grades):
        Results.__init__(self, student_id, pushed_grades)

    def get_records(self):
        return []  # stub

    def get_marks(self):
        return []  # stub

    def get_status(self, mark, topic=None):
        from utils.grade_record_utils import FAIL, PASS, EXEMPT, HALF
        if mark and mark > 0.5:
            return PASS
        if mark == 0.5:
            return HALF
        if mark == -1:
            return EXEMPT
        if mark is None:
            return ''
        return FAIL
