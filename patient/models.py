from django.db import models
from django.conf import settings


class Ward(models.Model):
    """
    Represents a hospital ward where patients are housed.
    """
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField(default=10)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Counsellor(models.Model):
    """
    Extends the User model with counsellor-specific profile info.
    Only users with role=COUNSELLOR should have a Counsellor profile.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='counsellor_profile'
    )
    phone_number = models.CharField(max_length=15, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    date_joined = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class Patient(models.Model):
    """
    Core patient record. Registration only — no diagnosis fields.
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    full_name = models.CharField(max_length=150)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_contact = models.CharField(max_length=15, blank=True)
    admission_date = models.DateField(auto_now_add=True)
    ward = models.ForeignKey(
        Ward, on_delete=models.SET_NULL, null=True, related_name='patients'
    )
    assigned_counsellor = models.ForeignKey(
        Counsellor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='patients'
    )
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='patient_photos/', blank=True, null=True)
    notes = models.TextField(blank=True, help_text="General notes only — not a diagnosis")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['-created_at']
