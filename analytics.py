import matplotlib
from django.db import connection

from dashboard.models import QuizFeedback
from quiz.models import StudentRecord

matplotlib.use('agg')
from matplotlib import pyplot as plt
import io, base64


def weekly_failures(total_num_students):
    with connection.cursor() as cursor:
        cursor.execute("select min(strftime('%W', date_submitted)) from quiz_writtensubmission")
        first_week = cursor.fetchone()
        first_week = int(first_week[0]) if first_week and first_week[0] else 0

        cursor.execute("select max(strftime('%W', date_submitted)) from quiz_writtensubmission")
        last_week = cursor.fetchone()
        last_week = int(last_week[0]) if last_week and last_week[0] else 0

        weekly_counts = {}

        for i in range(first_week, last_week + 1):

            query = "select topic_id, count(distinct(student_id)) from quiz_writtensubmission where is_pass=1 and CAST(strftime('%W', date_submitted) as decimal) <= '" + str(
                i) + "' group by topic_id order by topic_id, strftime('%W', date_submitted);"
            cursor.execute(query)

            for row in cursor:
                topic = row[0]
                num_passing = int(row[1])

                topic_weekly_count = weekly_counts.get(topic)

                if topic_weekly_count == None:
                    topic_weekly_count = []
                    for j in range(last_week - first_week + 1):
                        topic_weekly_count.append(0)
                    weekly_counts[topic] = topic_weekly_count

                topic_weekly_count[i - first_week] = total_num_students - num_passing

        weeks = [i + 1 for i in range(last_week + 1 - first_week)]

        fig, ax = plt.subplots()
        for topic, counts in weekly_counts.items():
            plt.plot(weeks, counts, label=topic)

        ax.set_xticks(weeks)
        ax.set_xticklabels(weeks)
        ax.set_xlabel("Weeks")
        ax.set_ylabel("# Students")
        ax.set_title("Weekly Failure Rates")
        ax.legend()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        weekly_failures_graph = base64.b64encode(buf.getvalue())
        return weekly_failures_graph


def topic_results(total_num_students):
    with connection.cursor() as cursor:
        cursor.execute('SELECT name FROM quiz_writtentopic ORDER BY ordering')
        topics = cursor.fetchall()

        pass_counts = []
        fail_counts = []
        missing_counts = []

        for topic in topics:
            topic = topic[0]
            passes = StudentRecord.objects.filter(topic=topic.lower(), grade__gte=0.5).count()
            cursor.execute(
                "SELECT COUNT(DISTINCT(student_id)) FROM quiz_writtensubmission WHERE topic_id='" + topic + "'")
            taken = cursor.fetchone()[0]
            fails = taken - passes
            missing = total_num_students - taken
            pass_counts.append(passes)
            fail_counts.append(fails)
            missing_counts.append(missing)

        fig_topics_results, ax_topic_results = plt.subplots()
        plt.bar([x for x in range(len(topics))], pass_counts, color='#98c65f')
        plt.bar([x for x in range(len(topics))], fail_counts, color='#e89494', bottom=pass_counts)
        plt.bar([x for x in range(len(topics))], missing_counts, color='#999c9e',
                bottom=[x + y for x, y in zip(pass_counts, fail_counts)])
        ax_topic_results.set_xticklabels([x[0] for x in topics])
        ax_topic_results.set_xticks(range(len(topics)))
        ax_topic_results.set_title("Topic Results Summary")
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig_topics_results)
        topic_results_graph = base64.b64encode(buf.getvalue())
        return topic_results_graph


def quizzes_per_student_by_topic(cursor, total_num_students):
    cursor.execute(" select topic_id, count(*) from quiz_writtensubmission "
                   "left join quiz_writtentopic on topic_id=name "
                   "where exists (select * from quiz_writtentopic where name=topic_id) "
                   "group by topic_id "
                   "order by quiz_writtentopic.ordering;")
    topic_counts = cursor.fetchall()

    quiz_per_stud_topics = []
    quiz_per_stud_counts = []
    for topic_count in topic_counts:
        if total_num_students > 0:
            quiz_per_stud_topics.append(topic_count[0])
            quiz_per_stud_counts.append(float(topic_count[1]) / float(total_num_students))

    fig2, ax2 = plt.subplots()
    nums = [x + 1 for x in range(len(quiz_per_stud_topics))]
    plt.bar(nums, quiz_per_stud_counts)
    quiz_per_stud_topics.insert(0, '')
    ax2.set_xticks(range(len(quiz_per_stud_topics)))
    ax2.set_xticklabels(quiz_per_stud_topics)
    ax2.set_ylabel("Average # quizzes per student")
    ax2.set_xlabel("Topic")
    ax2.set_title("Average Quiz Count per Student, by Topic")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig2)
    topic_graph = base64.b64encode(buf.getvalue())
    return topic_graph


def feedback_msg_burndown():
    with connection.cursor() as cursor:
        cursor.execute("select min(strftime('%W', date_submitted)) from quiz_writtensubmission")
        first_week = cursor.fetchone()
        first_week = int(first_week[0]) if first_week and first_week[0] else 0

        cursor.execute("select max(strftime('%W', date_submitted)) from quiz_writtensubmission")
        last_week = cursor.fetchone()
        last_week = int(last_week[0]) if last_week and last_week[0] else 0

        quizzes_feedback = {}

        feedback_fail_counts = {}

        for i in range(first_week, last_week + 1):

            query = "select student_id, quiz_id, q_marks, topic_id from quiz_writtensubmission where CAST(strftime('%W', date_submitted) as decimal) <= '" + str(
                i) + "' order by student_id, topic_id, date_submitted desc;"

            cursor.execute(query)
            student_quizzes = {}

            for row in cursor:
                student_id = row[0]
                quiz_id = row[1]
                q_marks = row[2]
                topic = row[3]

                student_quiz_list = student_quizzes.get(student_id)
                if student_quiz_list:
                    if topic in student_quizzes.get(student_id):
                        continue
                else:
                    student_quiz_list = []
                    student_quizzes[student_id] = student_quiz_list

                student_quiz_list.append(topic)

                quiz_feedback = quizzes_feedback.get(quiz_id)

                if quiz_feedback is None:
                    quiz_feedback = QuizFeedback.objects.filter(quiz_id=quiz_id) \
                        .values_list('feedback_id', flat=True) \
                        .order_by('question_num')
                    quizzes_feedback[quiz_id] = quiz_feedback

                stud_quiz_feedback = {}

                for mark, fb in zip(q_marks, quiz_feedback):
                    if mark == '0':
                        stud_quiz_feedback[fb] = 0
                    elif fb not in stud_quiz_feedback:
                        stud_quiz_feedback[fb] = 1

                for fb, score in stud_quiz_feedback.items():
                    feedback_fail_count = feedback_fail_counts.get(fb)
                    if not feedback_fail_count:
                        feedback_fail_count = [0 for x in range(first_week, last_week + 1)]
                        feedback_fail_counts[fb] = feedback_fail_count

                    if score != 1:
                        feedback_fail_count[i - first_week] += 1

        weeks = [i + 1 for i in range(last_week + 1 - first_week)]

        fig, ax = plt.subplots()
        for topic, counts in feedback_fail_counts.items():
            plt.plot(weeks, counts, label=topic)

        ax.set_xticks(weeks)
        ax.set_xticklabels(weeks)
        ax.set_xlabel("Weeks")
        ax.set_ylabel("# Students")
        ax.set_title("Feedback Message Burndown")
        # Shrink current axis by 20%
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width * 0.8, box.height * 0.9])

        # Put a legend to the right of the current axis
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        weekly_failures_graph = base64.b64encode(buf.getvalue())
        return weekly_failures_graph
