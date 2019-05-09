# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.

class Student(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    first_name = models.CharField(max_length=30, null=True)
    last_name = models.CharField(max_length=100, null=True)
    lab = models.CharField(max_length=5, null=True)
    section = models.CharField(max_length=5, null=True)

    comment = models.CharField(max_length=1000, null=True)

    def __str__(self):
        return self.id


class WrittenTopic(models.Model):
    name = models.CharField(max_length=5, primary_key=True)
    ordering = models.IntegerField()

    class Meta:
        ordering = ('ordering',)


class AnswerKey(models.Model):
    topic = models.ForeignKey(WrittenTopic, null=True)
    quiz_id = models.CharField(max_length=20, primary_key=True)
    answers = models.CharField(max_length=50)
    passing_mark = models.IntegerField()
    retake_msg = models.CharField(max_length=100)
    worth = models.DecimalField(max_digits=3, decimal_places=1)


class WrittenSubmission(models.Model):
    student = models.ForeignKey(Student)
    topic = models.ForeignKey(WrittenTopic, null=True)
    date_submitted = models.DateTimeField()
    responses = models.CharField(max_length=50)
    q_marks = models.CharField(max_length=50)
    quiz_id = models.CharField(max_length=20)
    mark = models.IntegerField(null=True)
    is_pass = models.NullBooleanField()
    taSignature = models.CharField(max_length=50)
    lab = models.CharField(max_length=5, null=True)

    def __str__(self):
        return str(self.student) + " - " + self.quiz_id

    class Meta:
        unique_together = ('student', 'date_submitted', 'responses')


class Amendment(models.Model):
    latest_submission = models.DateTimeField()


class StudentRecord(models.Model):
    student = models.ForeignKey(Student)
    topic = models.CharField(max_length=10)
    grade = models.DecimalField(decimal_places=4, max_digits=6)
    pushed_grade = models.DecimalField(null=True, decimal_places=4, max_digits=6)

    class Meta:
        unique_together = ('student', 'topic')
