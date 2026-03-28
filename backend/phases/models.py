from django.db import models

class Phase(models.Model):
    phase_number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"Phase {self.phase_number}: {self.name}"
