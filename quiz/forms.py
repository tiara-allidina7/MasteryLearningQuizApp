from django import forms
from django.core.exceptions import ValidationError

from config import quiz_config


class StudentInfoForm(forms.Form):
    username = forms.CharField(label="Username")
    quiz_id = forms.ChoiceField(choices=[(quiz, quiz) for quiz in
                                         quiz_config.demo_quiz_ids])
    # for non-demo version, can change above to quiz_id = forms.CharField(label="Quiz ID") for text field
    ta_sign = forms.CharField(label="TA Signature", help_text="(Entered by the TA)", widget=forms.PasswordInput())

    def clean_username(self):
        username = self.cleaned_data["username"]
        if " " in username:
            raise ValidationError("Spaces not allowed in username")
        return username


class QuizInputForm(forms.Form):
    q1 = forms.BooleanField(label="Q1", required=False)
    q2 = forms.BooleanField(label="Q2", required=False)
    q3 = forms.BooleanField(label="Q3", required=False)
    q4 = forms.BooleanField(label="Q4", required=False)
    q5 = forms.BooleanField(label="Q5", required=False)
    q6 = forms.BooleanField(label="Q6", required=False)
    q7 = forms.BooleanField(label="Q7", required=False)
    q8 = forms.BooleanField(label="Q8", required=False)
    q9 = forms.BooleanField(label="Q9", required=False)
    q10 = forms.BooleanField(label="Q10", required=False)
    q11 = forms.BooleanField(label="Q11", required=False)
    q12 = forms.BooleanField(label="Q12", required=False)
    q13 = forms.BooleanField(label="Q13", required=False)
    q14 = forms.BooleanField(label="Q14", required=False)
    q15 = forms.BooleanField(label="Q15", required=False)
    q16 = forms.BooleanField(label="Q16", required=False)
    q17 = forms.BooleanField(label="Q17", required=False)
    q18 = forms.BooleanField(label="Q18", required=False)
    q19 = forms.BooleanField(label="Q19", required=False)
    q20 = forms.BooleanField(label="Q20", required=False)
    q21 = forms.BooleanField(label="Q21", required=False)
    q22 = forms.BooleanField(label="Q22", required=False)
    q23 = forms.BooleanField(label="Q23", required=False)
    q24 = forms.BooleanField(label="Q24", required=False)
    q25 = forms.BooleanField(label="Q25", required=False)
    q26 = forms.BooleanField(label="Q26", required=False)
    q27 = forms.BooleanField(label="Q27", required=False)
    q28 = forms.BooleanField(label="Q28", required=False)
    q29 = forms.BooleanField(label="Q29", required=False)
    q30 = forms.BooleanField(label="Q30", required=False)
    q31 = forms.BooleanField(label="Q31", required=False)
    q32 = forms.BooleanField(label="Q32", required=False)
    q33 = forms.BooleanField(label="Q33", required=False)
    q34 = forms.BooleanField(label="Q34", required=False)
    q35 = forms.BooleanField(label="Q35", required=False)
    q36 = forms.BooleanField(label="Q36", required=False)
    q37 = forms.BooleanField(label="Q37", required=False)
    q38 = forms.BooleanField(label="Q38", required=False)
    q39 = forms.BooleanField(label="Q39", required=False)
    q40 = forms.BooleanField(label="Q40", required=False)
