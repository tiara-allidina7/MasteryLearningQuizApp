from collections import OrderedDict

from config import grade_config
from deliverables.quiz_results import QuizResults
from utils import grade_record_utils
from utils.display_utils import trim_trailing_zeroes


class StudentResults:
    student_id = None
    pushed_grades = None
    results_manager = None

    quiz_results = None

    topic_results_list = []
    results_list = []

    def __init__(self, results_manager, student_id, pushed_grades):
        self.results_manager = results_manager
        self.student_id = student_id
        self.pushed_grades = pushed_grades

        self.quiz_results = QuizResults(self.student_id, pushed_grades)

        # Additional non-quiz results can be added here
        self.topic_results_list = [self.quiz_results]  # breakdown of grades per topic
        self.results_list = [self.quiz_results]  # grade overview with only total mark

        self.results_list.sort(key=lambda (results): results.get_worth(), reverse=True)

    def get_full_record(self, student, include_personal_info=False):
        total = self.get_total_mark()

        overview_records = self.get_overview_records()
        results = {'overview': overview_records, 'total': round(total, 2), 'topic_marks': self.get_topic_marks()}

        if include_personal_info:
            results['personal_info'] = grade_record_utils.get_personal_info(student)

        return results

    """Returns dict of deliverable name to list of topic marks; each topic mark is dict with topic, mark, status
    
    Params:
    pushed_grades: True if method should return grades that were pushed, False if return latest grades
    """

    def get_topic_marks(self):
        topic_marks = OrderedDict()

        for results in self.topic_results_list:
            topic_marks[results.get_label()] = results.get_marks()

        return topic_marks

    """Returns list of grade overview records, each with label, worth, failRequired, mark, isPass"""

    def get_overview_records(self):
        overview = []
        for result in self.results_list:
            worth = result.get_worth()
            mark = result.get_total_mark()
            is_pass = mark >= worth / 2
            record = {'label': result.get_label(),
                      'worth': result.get_worth(),
                      'failRequired': (result.is_required() and not is_pass) or result.is_missing_required(),
                      'mark': trim_trailing_zeroes(round(mark, 2)) if mark is not None else None,
                      'isPass': is_pass}
            overview.append(record)
        return overview

    """Returns student total mark, not including bonuses"""

    def get_total_mark(self):
        total = 0
        for result in self.results_list:
            mark = result.get_total_mark()
            total += mark if mark > 0 else 0
        if grade_config.ADD_BONUS:
            total += self.results_manager.get_bonus(self.student_id)
        return total

    """Returns list of student quiz feedback, each with topic, feedback message, and whether correct"""

    def get_student_quiz_feedback(self, pushed_feedback=False):
        return self.quiz_results.get_student_quiz_feedback(pushed_feedback)

    """Returns list of student quiz feedback, grouped by topic"""

    def get_student_quiz_feedback_by_topic(self, pushed_feedback=False):
        return self.quiz_results.get_student_quiz_feedback_by_topic(pushed_feedback)

    """Returns quiz results object"""

    def get_quiz_results(self):
        return self.quiz_results

    """Returns dict of deliverable names to weights"""

    def get_weights(self):
        weights = {}
        for results in self.results_list:
            weights[results.get_label()] = results.get_worth()
        return weights
