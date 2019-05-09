from django import forms


class AmendmentForm(forms.Form):
    student = forms.CharField(label="Student ID")
    topic = forms.CharField(label="Topic")
    new_grade = forms.DecimalField(label="New Grade")
