from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User

class Cohort(models.Model):
    name = models.CharField(max_length=30)
    created_on = models.DateTimeField(auto_now_add=True)

class CohortUser(models.Model):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=CohortUser)
def update_scoreboard(sender, instance, created, **kwargs):
    if not created:  
        from .scoreboard import updateUserRank
        updateUserRank(instance.user.email, instance.cohort_id, instance.score)
