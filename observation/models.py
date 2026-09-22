from django.db import models
from django.conf import settings
from patient.models import Patient
from django.utils import timezone


class DailyObservation(models.Model):
    """
    A single observation entry for a patient.

    Each observation is stored as a separate record.
    This model does not diagnose a patient.
    It only records observable factors to help counsellors
    prioritize patients who may need closer observation.
    """

    # ---------------------------------------------------------
    # MOOD
    # ---------------------------------------------------------

    MOOD_CHOICES = [
        ('HAPPY', 'Happy'),
        ('CALM', 'Calm'),
        ('SAD', 'Sad'),
        ('AGGRESSIVE', 'Aggressive'),
    ]

    # ---------------------------------------------------------
    # BEHAVIOUR
    # ---------------------------------------------------------

    BEHAVIOUR_CHOICES = [
        ('COOPERATIVE', 'Cooperative'),
        ('WITHDRAWN', 'Withdrawn'),
        ('RESTLESS', 'Restless'),
        ('DISRUPTIVE', 'Disruptive'),
    ]

    # ---------------------------------------------------------
    # SLEEP
    # ---------------------------------------------------------

    SLEEP_CHOICES = [
        ('GOOD', 'Good'),
        ('POOR', 'Poor'),
    ]

    # ---------------------------------------------------------
    # APPETITE
    # ---------------------------------------------------------

    APPETITE_CHOICES = [
        ('GOOD', 'Good'),
        ('POOR', 'Poor'),
    ]

    # ---------------------------------------------------------
    # PERSONAL HYGIENE
    # ---------------------------------------------------------

    HYGIENE_CHOICES = [
        ('GOOD', 'Good'),
        ('POOR', 'Poor'),
    ]

    # ---------------------------------------------------------
    # COMMUNICATION
    # ---------------------------------------------------------

    COMMUNICATION_CHOICES = [
        ('NORMAL', 'Normal'),
        ('LIMITED', 'Limited'),
        ('NONE', 'None'),
    ]

    # ---------------------------------------------------------
    # PARTICIPATION
    # ---------------------------------------------------------

    PARTICIPATION_CHOICES = [
        ('ACTIVE', 'Active'),
        ('REFUSED', 'Refused'),
    ]

    # ---------------------------------------------------------
    # PRIORITY LEVELS
    # ---------------------------------------------------------

    PRIORITY_STABLE = 'STABLE'

    PRIORITY_NEEDS_OBSERVATION = 'NEEDS_OBSERVATION'

    PRIORITY_NEEDS_ATTENTION = 'NEEDS_ATTENTION'

    PRIORITY_HIGH = 'HIGH_PRIORITY'

    PRIORITY_CHOICES = [
        (
            PRIORITY_STABLE,
            'Stable'
        ),
        (
            PRIORITY_NEEDS_OBSERVATION,
            'Needs Observation'
        ),
        (
            PRIORITY_NEEDS_ATTENTION,
            'Needs Attention'
        ),
        (
            PRIORITY_HIGH,
            'High Priority'
        ),
    ]

    # ---------------------------------------------------------
    # PATIENT
    # ---------------------------------------------------------

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='observations'
    )

    # ---------------------------------------------------------
    # COUNSELLOR
    # ---------------------------------------------------------

    counsellor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='observations_made'
    )

    # ---------------------------------------------------------
    # DATE AND TIME
    # ---------------------------------------------------------

    date = models.DateField()

    time = models.TimeField()

    # ---------------------------------------------------------
    # OBSERVATION FACTORS
    # ---------------------------------------------------------

    mood = models.CharField(
        max_length=15,
        choices=MOOD_CHOICES
    )

    behaviour = models.CharField(
        max_length=15,
        choices=BEHAVIOUR_CHOICES
    )

    sleep_quality = models.CharField(
        max_length=5,
        choices=SLEEP_CHOICES
    )

    appetite = models.CharField(
        max_length=5,
        choices=APPETITE_CHOICES
    )

    personal_hygiene = models.CharField(
        max_length=5,
        choices=HYGIENE_CHOICES
    )

    communication = models.CharField(
        max_length=10,
        choices=COMMUNICATION_CHOICES
    )

    participation = models.CharField(
        max_length=10,
        choices=PARTICIPATION_CHOICES
    )

    # ---------------------------------------------------------
    # REMARKS
    # ---------------------------------------------------------

    remarks = models.TextField(
        blank=True
    )

    # ---------------------------------------------------------
    # POI
    # ---------------------------------------------------------

    poi_score = models.PositiveIntegerField(
        default=0,
        editable=False
    )

    # ---------------------------------------------------------
    # PRIORITY
    # ---------------------------------------------------------

    priority_level = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_STABLE,
        editable=False
    )

    # ---------------------------------------------------------
    # CREATED TIME
    # ---------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ---------------------------------------------------------
    # META
    # ---------------------------------------------------------

    class Meta:
        ordering = ['-date', '-time']

        # Prevent duplicate observations for the exact
        # same patient, date and time.
        unique_together = (
            'patient',
            'date',
            'time',
        )

    # ---------------------------------------------------------
    # STRING REPRESENTATION
    # ---------------------------------------------------------

    def __str__(self):
        return f"{self.patient.full_name} - {self.date}"

    # ---------------------------------------------------------
    # CALCULATE POI
    # ---------------------------------------------------------

    def calculate_poi(self):
        """
        Patient Observation Index (POI).

        This is NOT a diagnostic score.

        It only helps counsellors prioritize patients
        who may require closer observation.

        Higher score = more observation factors
        requiring attention.

        Maximum possible score = 20.
        """

        score = 0

        # -----------------------------------------------------
        # MOOD SCORE
        # -----------------------------------------------------

        mood_scores = {
            'HAPPY': 0,
            'CALM': 1,
            'SAD': 2,
            'AGGRESSIVE': 4,
        }

        score += mood_scores.get(
            self.mood,
            0
        )

        # -----------------------------------------------------
        # BEHAVIOUR SCORE
        # -----------------------------------------------------

        behaviour_scores = {
            'COOPERATIVE': 0,
            'WITHDRAWN': 2,
            'RESTLESS': 3,
            'DISRUPTIVE': 4,
        }

        score += behaviour_scores.get(
            self.behaviour,
            0
        )

        # -----------------------------------------------------
        # SLEEP SCORE
        # -----------------------------------------------------

        if self.sleep_quality == 'POOR':
            score += 2

        # -----------------------------------------------------
        # APPETITE SCORE
        # -----------------------------------------------------

        if self.appetite == 'POOR':
            score += 2

        # -----------------------------------------------------
        # PERSONAL HYGIENE SCORE
        # -----------------------------------------------------

        if self.personal_hygiene == 'POOR':
            score += 2

        # -----------------------------------------------------
        # COMMUNICATION SCORE
        # -----------------------------------------------------

        communication_scores = {
            'NORMAL': 0,
            'LIMITED': 2,
            'NONE': 3,
        }

        score += communication_scores.get(
            self.communication,
            0
        )

        # -----------------------------------------------------
        # PARTICIPATION SCORE
        # -----------------------------------------------------

        if self.participation == 'REFUSED':
            score += 3

        return score

    # ---------------------------------------------------------
    # GET PRIORITY LEVEL
    # ---------------------------------------------------------

    def get_priority_level(self, score):
        """
        Convert the POI score into an observation
        priority level.

        This is NOT a medical diagnosis.
        """

        if score <= 4:
            return self.PRIORITY_STABLE

        elif score <= 8:
            return self.PRIORITY_NEEDS_OBSERVATION

        elif score <= 13:
            return self.PRIORITY_NEEDS_ATTENTION

        else:
            return self.PRIORITY_HIGH

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    def save(self, *args, **kwargs):
        """
        Automatically:

        1. Set the current date.
        2. Set the current time.
        3. Calculate POI.
        4. Calculate priority level.
        5. Save the observation.
        """

        # -----------------------------------------------------
        # AUTOMATIC DATE
        # -----------------------------------------------------

        if not self.date:
            self.date = timezone.localdate()

        # -----------------------------------------------------
        # AUTOMATIC TIME
        # -----------------------------------------------------

        if not self.time:
            self.time = timezone.localtime().time()

        # -----------------------------------------------------
        # CALCULATE POI
        # -----------------------------------------------------

        self.poi_score = self.calculate_poi()

        # -----------------------------------------------------
        # CALCULATE PRIORITY
        # -----------------------------------------------------

        self.priority_level = self.get_priority_level(
            self.poi_score
        )

        # -----------------------------------------------------
        # SAVE TO DATABASE
        # -----------------------------------------------------

        super().save(*args, **kwargs)