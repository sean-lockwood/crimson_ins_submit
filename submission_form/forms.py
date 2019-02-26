import yaml
from django import forms
from .models import Submission
from django.forms import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator

email_validator = EmailValidator()

with open('questions.yml') as f:
    form_info = yaml.load(f) 
QUESTIONS  = {q: _(v + '\n') for q, v in form_info['questions' ].items()}
HELP_TEXTS = {q: _(v + '\n') for q, v in form_info['mouseover_text'].items()}


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['deliverer', 'other_email', 'delivery_date', 'instrument', 
                  'file_type', 'history_updated', 'keywords_checked', 'descrip_updated', 
                  'useafter_matches', 'compliance_verified', 'ingest_files', 'etc_delivery', 
                  'jwst_etc', 'calpipe_version', 'replacement_files', 'old_reference_files', 
                  'replacing_badfiles', 'was_jira_issue_filed', 'jira_issue', 'change_level', 
                  'table_rows_changed', 'modes_affected', 'correctness_testing', 
                  'additional_considerations', 'disk_files', 'delivery_reason']
        labels = QUESTIONS
        widgets = {'delivery_date': forms.SelectDateWidget(), }
        help_texts = HELP_TEXTS
    
    def clean_deliverer(self):
        deliverer = self.cleaned_data['deliverer']
        if not deliverer.lower() == 'sean':
            raise ValidationError('Deliverer is not Sean!')
        return deliverer

    def clean_other_email(self):
        other_email = self.cleaned_data['other_email']
        if other_email is None:  return
        other_email = other_email.split(',')
        other_email = [x.strip() for x in other_email]
        for email in other_email:
            email_validator(email)
        return other_email
