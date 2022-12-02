from django.db import models
from django.template.defaultfilters import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from users.models import User
# from batches.solutions import updateScoreSave

class Batch(models.Model):
    batch_name = models.CharField(max_length=30)
    created_on = models.DateTimeField(auto_now_add=True)

class BatchUser(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True)
