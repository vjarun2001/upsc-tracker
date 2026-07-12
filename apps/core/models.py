from django.db import models


class Quote(models.Model):
    text = models.CharField(max_length=300)

    author = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text[:50]
