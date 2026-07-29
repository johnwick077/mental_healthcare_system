from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User


@receiver(post_save, sender=User)
def create_counsellor_profile(sender, instance, created, **kwargs):
    if instance.role == User.Role.COUNSELLOR:
        from patient.models import Counsellor
        Counsellor.objects.get_or_create(user=instance)