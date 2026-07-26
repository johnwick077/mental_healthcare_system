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