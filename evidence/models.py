from django.db import models
from django.conf import settings
from patient.models import Patient

class ResearchPaper(models.Model):
    title = models.CharField(max_length=500)
    authors = models.TextField(blank=True)
    journal = models.CharField(max_length=300, blank=True)
    publication_year = models.PositiveIntegerField(null=True, blank=True)

    doi = models.CharField(max_length=200, blank=True)
    paper_url = models.URLField(blank=True)

    abstract = models.TextField(blank=True)

    dataset_name = models.CharField(max_length=300, blank=True)

    key_finding = models.TextField()

    source = models.CharField(
        max_length=50,
        default="IEEE"
    )

    verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ResearchDataset(models.Model):
    name = models.CharField(max_length=300)
    source_url = models.URLField(blank=True)

    description = models.TextField(blank=True)

    features = models.TextField(blank=True)

    sample_size = models.PositiveIntegerField(null=True, blank=True)

    license = models.CharField(max_length=300, blank=True)

    related_papers = models.ManyToManyField(
        ResearchPaper,
        blank=True,
        related_name="datasets"
    )

    def __str__(self):
        return self.name

class ObservationPattern(models.Model):
    name = models.CharField(max_length=300)

    description = models.TextField()

    observation_fields = models.JSONField(default=list)

    pattern_description = models.TextField()

    possible_concern = models.TextField(blank=True)

    recommendation = models.TextField(blank=True)

    supporting_papers = models.ManyToManyField(
        ResearchPaper,
        blank=True,
        related_name="observation_patterns"
    )

    minimum_days = models.PositiveIntegerField(default=7)

    minimum_occurrences = models.PositiveIntegerField(
        default=1,
        help_text="Minimum number of observations that must match each pattern condition."
    )

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class AISummaryHistory(models.Model):
    """
    Stores a generated AI observation summary so that previous
    analysis results can be reviewed later.

    This is an observation-support record, not a diagnosis.
    """

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='ai_summary_history'
    )

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_ai_summaries'
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    observation_count = models.PositiveIntegerField(default=0)

    observation_days = models.PositiveIntegerField(default=0)

    matched_pattern = models.CharField(
        max_length=255,
        blank=True
    )

    observation_summary = models.TextField()

    observed_changes = models.JSONField(
        default=list
    )

    evidence_interpretation = models.TextField(
        blank=True
    )

    recommended_follow_up = models.TextField(
        blank=True
    )

    disclaimer = models.TextField(
        blank=True
    )

    research_evidence = models.JSONField(
        default=list
    )

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return (
            f"AI Summary - {self.patient.full_name} "
            f"({self.generated_at.strftime('%d-%m-%Y %H:%M')})"
        )