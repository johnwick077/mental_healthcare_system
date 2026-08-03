from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access.
    Roles: Admin, Counsellor, Store Manager
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        COUNSELLOR = 'COUNSELLOR', 'Counsellor'
        STORE_MANAGER = 'STORE_MANAGER', 'Store Manager'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.COUNSELLOR,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_counsellor(self):
        return self.role == self.Role.COUNSELLOR

    def is_store_manager(self):
        return self.role == self.Role.STORE_MANAGER

class Notification(models.Model):
    TYPE_LOW_STOCK = 'LOW_STOCK'
    TYPE_PENDING_REQUEST = 'PENDING_REQUEST'
    TYPE_CHOICES = [
        (TYPE_LOW_STOCK, 'Low Stock'),
        (TYPE_PENDING_REQUEST, 'Pending Request'),
    ]

    recipient = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type}: {self.message}"