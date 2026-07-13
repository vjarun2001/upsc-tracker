from django.db import models


class Phase(models.TextChoices):
    PRELIMS = "prelims", "Prelims"
    MAINS = "mains", "Mains"
    INTERVIEW = "interview", "Interview"
