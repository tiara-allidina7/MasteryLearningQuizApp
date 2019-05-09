# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from quiz.models import Student, WrittenTopic


# Create your models here.

class Feedback(models.Model):
    feedback_msg = models.CharField(max_length=1000)


class QuizFeedback(models.Model):
    quiz_id = models.CharField(max_length=20)
    topic = models.ForeignKey(WrittenTopic)
    question_num = models.IntegerField()
    feedback = models.ForeignKey(Feedback)


class StudentFeedback(models.Model):
    student = models.ForeignKey(Student)
    feedback = models.ForeignKey(Feedback)
    correct = models.BooleanField()


class PushedStudentFeedback(models.Model):
    student = models.ForeignKey(Student)
    feedback = models.ForeignKey(Feedback)
    correct = models.BooleanField()


class GradeAmendment(models.Model):
    student = models.ForeignKey(Student)
    topic = models.CharField(max_length=10)
    old_grade = models.DecimalField(max_digits=7, decimal_places=4)
    new_grade = models.DecimalField(max_digits=7, decimal_places=4)
    date_submitted = models.DateTimeField(null=True)


class UpdateGradeRecord(models.Model):
    last_updated = models.DateTimeField()


class PushGradeRecord(models.Model):
    last_pushed = models.DateTimeField()
