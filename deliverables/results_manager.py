import decimal
from collections import OrderedDict

from config import grade_config
from deliverables.student_results import StudentResults
from utils import grade_record_utils


class ResultsManager:
    pushed_grades = None
    bonuses = None

    def __init__(self, pushed_grades):
        self.pushed_grades = pushed_grades

        self.read_grade_files()

    def read_grade_files(self):
        self.bonuses = grade_record_utils.get_bonuses()

    def get_student_results(self, student_id):
        student_results = StudentResults(self, student_id, self.pushed_grades)
        return student_results

    def get_students_records(self, students, calculate_averages=False):
        results = []
        totals = OrderedDict()
        weights = None
        for student in students:
            student_results = self.get_student_results(student.id)
            results.append(student_results.get_full_record(student, True))
            if calculate_averages:
                if weights is None:
                    weights = student_results.get_weights()
                self.update_totals(totals, student_results.get_overview_records())

        if calculate_averages:
            averages = self.calculate_averages(totals, weights, len(students))
        else:
            averages = []

        results.sort(key=lambda (rec): rec['total'])

        return {"records": results, "averages": averages}

    def get_bonus(self, student_id):
        return self.bonuses.get(student_id)

    @staticmethod
    def update_totals(totals, student_overview):
        for record in student_overview:
            label = record['label']
            mark = record['mark']
            if totals.get(label) is None:
                totals[label] = decimal.Decimal(mark) if mark is not None and mark > -1 else 0
            else:
                totals[label] += decimal.Decimal(mark) if mark is not None and mark > -1 else 0

    @staticmethod
    def calculate_averages(totals, weights, num_students):
        averages = []
        for label, count in totals.items():
            avg = round(count / num_students, 2)
            average = {"label": label, "average": avg, "worth": weights.get(label)}
            averages.append(average)
        return averages
