from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Notification


@receiver(post_save, sender=User)
def create_counsellor_profile(sender, instance, created, **kwargs):
    if instance.role == User.Role.COUNSELLOR:
        from patient.models import Counsellor
        Counsellor.objects.get_or_create(user=instance)


def notify_store_managers(notification_type, message):
    store_managers = User.objects.filter(role=User.Role.STORE_MANAGER)
    for sm in store_managers:
        Notification.objects.create(
            recipient=sm, notification_type=notification_type, message=message
        )


def notify_admins(notification_type, message):
    admins = User.objects.filter(role=User.Role.ADMIN)
    for admin_user in admins:
        Notification.objects.create(
            recipient=admin_user, notification_type=notification_type, message=message
        )