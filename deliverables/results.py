"""Represents a component that contributes towards student mark.
Additional subclasses can be added to account for non-quiz grade components."""


class Results:
    student_id = None
    pushed_grades = None

    def __init__(self, student_id, pushed_grades):
        self.student_id = student_id
        self.pushed_grades = pushed_grades

    def get_total_mark(self):
        return 0  # stub

    @staticmethod
    def get_label():
        return ''  # stub

    @staticmethod
    def get_worth():
        return 0  # stub

    @staticmethod
    def is_required():
        return False  # stub

    def is_missing_required(self):
        return False  # stub
