from django.db import models
from django.conf import settings
from patient.models import Patient


class DailyObservation(models.Model):
    """
    A single day's observation entry for a patient.
    Never overwritten — each day creates a new row (observation history).
    This model does NOT diagnose; it only records observable behaviour
    to help counsellors prioritize attention.
    """

    MOOD_CHOICES = [
        ('HAPPY', 'Happy'),
        ('CALM', 'Calm'),
        ('SAD', 'Sad'),
        ('AGGRESSIVE', 'Aggressive'),
    ]
    BEHAVIOUR_CHOICES = [
        ('COOPERATIVE', 'Cooperative'),
        ('WITHDRAWN', 'Withdrawn'),
        ('RESTLESS', 'Restless'),
        ('DISRUPTIVE', 'Disruptive'),
    ]
    SLEEP_CHOICES = [('GOOD', 'Good'), ('POOR', 'Poor')]
    APPETITE_CHOICES = [('GOOD', 'Good'), ('POOR', 'Poor')]
    HYGIENE_CHOICES = [('GOOD', 'Good'), ('POOR', 'Poor')]
    COMMUNICATION_CHOICES = [
        ('NORMAL', 'Normal'),
        ('LIMITED', 'Limited'),
        ('NONE', 'None'),
    ]
    PARTICIPATION_CHOICES = [('ACTIVE', 'Active'), ('REFUSED', 'Refused')]

    PRIORITY_STABLE = 'STABLE'
    PRIORITY_NEEDS_OBSERVATION = 'NEEDS_OBSERVATION'
    PRIORITY_NEEDS_ATTENTION = 'NEEDS_ATTENTION'
    PRIORITY_HIGH = 'HIGH_PRIORITY'
    PRIORITY_CHOICES = [
        (PRIORITY_STABLE, 'Stable'),
        (PRIORITY_NEEDS_OBSERVATION, 'Needs Observation'),
        (PRIORITY_NEEDS_ATTENTION, 'Needs Attention'),
        (PRIORITY_HIGH, 'High Priority'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='observations')
    counsellor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='observations_made'
    )
    date = models.DateField()
    time = models.TimeField()

    mood = models.CharField(max_length=15, choices=MOOD_CHOICES)
    behaviour = models.CharField(max_length=15, choices=BEHAVIOUR_CHOICES)
    sleep_quality = models.CharField(max_length=5, choices=SLEEP_CHOICES)
    appetite = models.CharField(max_length=5, choices=APPETITE_CHOICES)
    personal_hygiene = models.CharField(max_length=5, choices=HYGIENE_CHOICES)
    communication = models.CharField(max_length=10, choices=COMMUNICATION_CHOICES)
    participation = models.CharField(max_length=10, choices=PARTICIPATION_CHOICES)
    remarks = models.TextField(blank=True)

    poi_score = models.PositiveIntegerField(default=0, editable=False)
    priority_level = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_STABLE, editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        # Prevents accidentally saving two observations for the same
        # patient at the exact same date+time slot.
        unique_together = ('patient', 'date', 'time')

    def __str__(self):
        return f"{self.patient.full_name} - {self.date}"

    def calculate_poi(self):
        """
        Patient Observation Index (POI).
        This is NOT a diagnostic score — it only helps counsellors
        prioritize which patients may need closer attention today.
        """
        score = 0

        mood_scores = {'HAPPY': 0, 'CALM': 1, 'SAD': 2, 'AGGRESSIVE': 4}
        score += mood_scores.get(self.mood, 0)

        if self.sleep_quality == 'POOR':
            score += 2
        if self.appetite == 'POOR':
            score += 2
        if self.personal_hygiene == 'POOR':
            score += 2
        if self.participation == 'REFUSED':
            score += 3

        return score

    def get_priority_level(self, score):
        if score <= 2:
            return self.PRIORITY_STABLE
        elif score <= 5:
            return self.PRIORITY_NEEDS_OBSERVATION
        elif score <= 8:
            return self.PRIORITY_NEEDS_ATTENTION
        else:
            return self.PRIORITY_HIGH

    def save(self, *args, **kwargs):
        self.poi_score = self.calculate_poi()
        self.priority_level = self.get_priority_level(self.poi_score)
        super().save(*args, **kwargs)