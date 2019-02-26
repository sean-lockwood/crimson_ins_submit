from django.conf import settings
from django.db import models
from django.utils import timezone


INSTR = ['ACS', 'COS', 'STIS', 'WFC3']
CHANGE = ['SEVERE', 'MODERATE', 'TRIVIAL']

class Submission(models.Model):
    created_date              = models.DateTimeField(default=timezone.now)
    published_date            = models.DateTimeField(blank=True, null=True)
    
    deliverer                 = models.CharField(max_length=100)
    other_email               = models.CharField(max_length=500, blank=True, null=True)  #EmailField(blank=True, null=True)
    delivery_date             = models.DateTimeField()
    instrument                = models.CharField(max_length=20, choices=zip(INSTR, INSTR), default=INSTR[0])
    file_type                 = models.CharField(max_length=100)
    history_updated           = models.BooleanField()
    keywords_checked          = models.BooleanField()
    descrip_updated           = models.BooleanField()
    useafter_matches          = models.NullBooleanField()
    compliance_verified       = models.NullBooleanField()
    ingest_files              = models.TextField()
    etc_delivery              = models.NullBooleanField()
    jwst_etc                  = models.NullBooleanField()
    calpipe_version           = models.CharField(max_length=100)
    replacement_files         = models.BooleanField()
    old_reference_files       = models.CharField(max_length=100)  # Clean and search CRDS database?
    replacing_badfiles        = models.NullBooleanField()
    was_jira_issue_filed      = models.BooleanField()
    jira_issue                = models.CharField(max_length=100, blank=True, null=True)  # Clean and search JIRA issues?
    change_level              = models.CharField(max_length=100, choices=zip(CHANGE, CHANGE), default=CHANGE[0])
    table_rows_changed        = models.TextField()
    modes_affected            = models.TextField()
    correctness_testing       = models.TextField()
    additional_considerations = models.TextField()
    disk_files                = models.TextField()
    delivery_reason           = models.TextField()
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return '{} {}'.format(self.deliverer, self.instrument)
    