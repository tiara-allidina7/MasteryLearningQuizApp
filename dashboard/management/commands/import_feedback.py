import csv
import os

from django.core.management.base import BaseCommand

from ...models import Feedback, QuizFeedback

feedback_path = 'import_data/feedback/'


class Command(BaseCommand):

    def handle(self, *args, **options):
        for file_name in os.listdir(feedback_path):
            with open(feedback_path + file_name) as quiz_file:
                csv_reader = csv.reader(quiz_file)

                topic = file_name[0:file_name.index(".")].upper()
                i = 0
                quiz_ids = None
                for row in csv_reader:
                    if i == 0:
                        quiz_ids = row
                        i += 1
                    else:
                        for j in range(len(row)):
                            if j == 0:
                                message = row[j]
                                feedback = Feedback.objects.filter(feedback_msg=message)
                                feedback = feedback[0] if len(feedback) > 0 else None
                                if feedback is None:
                                    feedback = Feedback(feedback_msg=message)
                                    feedback.save()
                            else:
                                q_nums = row[j].split(",")
                                quiz_id = quiz_ids[j]
                                for q_num in q_nums:
                                    q_num = q_num.strip()
                                    if len(q_num) == 0:
                                        continue
                                    result = QuizFeedback.objects.filter(quiz_id=quiz_id, question_num=int(q_num))

                                    if len(result) == 0:
                                        quiz_feedback = QuizFeedback(quiz_id=quiz_id,
                                                                     topic_id=topic,
                                                                     question_num=q_num,
                                                                     feedback_id=feedback.id)
                                        quiz_feedback.save()
                                    else:
                                        quiz_feedback = result[0]
                                        quiz_feedback.feedback_id = feedback.id
                                        quiz_feedback.save()
