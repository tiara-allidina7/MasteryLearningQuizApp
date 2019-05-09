import csv

from django.core.management.base import BaseCommand

from ...models import AnswerKey, WrittenTopic

rubric_file = "import_data/rubric.csv"
num_questions = 40


def read_rubric():
    with open(rubric_file) as infile:
        csv_reader = csv.reader(infile)

        start_index, end_index = 0, 0
        first_line = True
        answer_keys = []
        topics = []

        for row in csv_reader:
            if first_line:
                start_index = row.index('Q1')
                end_index = start_index + (num_questions - 1)
                first_line = False
            else:
                quiz_id = row[0]
                worth = row[1]
                retake_msg = row[2]
                topic = row[3].upper()
                passing_mark = row[4]
                answers = ''
                if topic not in topics:
                    topics.append(topic)
                for i in range(start_index, end_index + 1):
                    answer = row[i].strip()
                    if not answer:
                        answer = '0'
                    answers = answers + answer
                answer_key = (topic, quiz_id, answers, passing_mark, retake_msg, worth)

                answer_keys.append(answer_key)
        save_to_db(topics, answer_keys)


def save_to_db(topics, answer_keys):
    for i in range(len(topics)):
        topic = WrittenTopic(
            name=topics[i],
            ordering=i
        )
        topic.save()
    for answer_key in answer_keys:
        key = AnswerKey(
            topic_id=answer_key[0],
            quiz_id=answer_key[1],
            answers=answer_key[2],
            passing_mark=answer_key[3],
            retake_msg=answer_key[4],
            worth=answer_key[5]
        )
        key.save()


class Command(BaseCommand):

    def handle(self, *args, **options):
        read_rubric()
