from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ReleaseChecklist, Version


@receiver(post_save, sender=Version)
def create_checklist(sender, instance: Version, created: bool, **kwargs) -> None:
    if created:
        ReleaseChecklist.objects.get_or_create(version=instance)
